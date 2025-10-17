"""JDB dialog implementation for ChatDBG."""

import os
import re
import subprocess
from typing import List, Optional, Union

from . import clangd_lsp_integration
from ..util.prompts import (
    build_followup_prompt,
    build_initial_prompt,
    initial_instructions,
)
from ..assistant.assistant import Assistant
from ..util.config import chatdbg_config
from ..util.history import CommandHistory
from ..util.log import ChatDBGLog
from .stacks import _ArgumentEntry, _FrameSummaryEntry, _SkippedFramesEntry

from ..java_util.classpath import ClasspathManager, detect_java_project_classpath
from ..java_util.javap import javap_analyzer
from ..java_util.source import source_analyzer
from ..java_util.jdb_process import JDBProcess


class JDBDialog:
    """JDB debugger dialog implementation extending DBGDialog."""

    # The log file used by the listener on the Assistant
    _log = ChatDBGLog(
        log_filename=chatdbg_config.log,
        config=chatdbg_config.to_json(),
        capture_streams=False,
    )

    def __init__(self, prompt: str, java_home: Optional[str] = None, classpath: str = '.'):
        self._prompt = prompt
        self._history = CommandHistory(self._prompt)
        self._unsafe_cmd = False

        # Java-specific attributes
        self.java_home = java_home or os.environ.get('JAVA_HOME', '')
        self.classpath_manager = ClasspathManager(self.java_home)

        # JDB process management
        self.jdb_process: Optional[JDBProcess] = None

        # Current debugging state
        self.current_class: Optional[str] = None
        self.current_method: Optional[str] = None
        self.current_file: Optional[str] = None
        self.current_line: Optional[int] = None

    def query_and_print(self, assistant, user_text, is_followup):
        """Query assistant and print response."""
        prompt = self.build_prompt(user_text, is_followup)

        self._history.clear()
        print(assistant.query(prompt, user_text)["message"])
        if self._unsafe_cmd:
            self.warn(
                "Warning: One or more debugger commands were blocked as potentially unsafe.\n"
                "Warning: You can disable sanitizing with `config --unsafe` and try again at your own risk."
            )
            self._unsafe_cmd = False

    def dialog(self, user_text):
        """Main dialog loop for JDB debugging."""
        assistant = self._make_assistant()
        self.check_debugger_state()

        self.query_and_print(assistant, user_text, False)
        while True:
            try:
                command = input("(ChatDBG chatting) ").strip()
                if command in ["exit", "quit"]:
                    break
                if command in ["chat", "why"]:
                    self.query_and_print(assistant, command, True)
                elif command == "history":
                    print(self._history)
                else:
                    # Send the next input as a JDB command
                    result = self._run_one_command(command)
                    if self._message_is_a_bad_command_error(result):
                        # If result is not a recognized command, pass it as a query
                        self.query_and_print(assistant, command, True)
                    else:
                        if command != "test_prompt":
                            self._history.append(command, result)
                        print(result)
            except EOFError:
                break

        assistant.close()

    def _run_one_command(self, command: str) -> str:
        """Execute a JDB command."""
        if not self.jdb_process:
            return "JDB process not started"

        try:
            output, error = self.jdb_process.run_command(command)
            return output if output else error
        except Exception as e:
            return f"Error executing command: {e}"

    def _message_is_a_bad_command_error(self, message: str) -> bool:
        """Check if message indicates an unrecognized JDB command."""
        return "Command not recognized" in message or "not found" in message.lower()

    def check_debugger_state(self):
        """Check if debugger is in a valid state."""
        if not self.jdb_process or not self.jdb_process.is_running():
            self.fail("JDB process not running. Please start a Java program first.")

        # Check if we have debug information
        if not self._has_debug_info():
            self.warn("Program may not have been compiled with debug information (-g flag)")

    def _has_debug_info(self) -> bool:
        """Check if the current class has debug information."""
        if not self.current_class:
            return False

        try:
            # Try to get line information
            output, error = self.jdb_process.run_command('lines')
            return 'line numbers' in output.lower() or 'source' in output.lower()
        except:
            return False

    def _get_frame_summaries(self, max_entries: int = 20) -> Optional[List[Union[_FrameSummaryEntry, _SkippedFramesEntry]]]:
        """Get Java stack frame summaries."""
        if not self.jdb_process:
            return None

        try:
            stack_trace = self.jdb_process.get_stack_trace()
            if not stack_trace:
                return None

            summaries = []
            for frame in stack_trace[:max_entries]:
                # Parse method signature to extract arguments
                arguments = self._parse_java_method_arguments(frame.get('method', ''))

                # Find source file if available
                source_file = frame.get('file', 'unknown')
                if source_file and source_file != 'unknown':
                    # Convert class name to file path if needed
                    if source_file.endswith('.java'):
                        file_path = source_file
                    else:
                        # Try to find the source file
                        file_path = self._find_source_file(source_file)
                else:
                    file_path = 'unknown'

                summary = _FrameSummaryEntry(
                    index=frame.get('index', 0),
                    name=frame.get('method', 'unknown'),
                    arguments=arguments,
                    file_path=file_path,
                    lineno=frame.get('line', 0)
                )
                summaries.append(summary)

            return summaries

        except Exception as e:
            print(f"Error getting frame summaries: {e}")
            return None

    def _parse_java_method_arguments(self, method_signature: str) -> List[_ArgumentEntry]:
        """Parse Java method arguments from signature."""
        arguments = []

        # Extract parameter types from method signature like "com.example.MyClass.method(String, int)"
        match = re.search(r'\(([^)]+)\)', method_signature)
        if match:
            param_str = match.group(1)
            if param_str.strip():
                # Split by comma and clean up
                params = [p.strip() for p in param_str.split(',')]
                for i, param in enumerate(params):
                    # Extract type (remove generics for simplicity)
                    param_type = param.split('<')[0]
                    arguments.append(_ArgumentEntry(
                        typename=param_type,
                        name=f"arg{i}",  # JDB doesn't always provide parameter names
                        value="[unknown]"  # Would need to inspect locals
                    ))

        return arguments

    def _find_source_file(self, class_name: str) -> str:
        """Find the source file for a Java class."""
        # Convert class name to file path
        if class_name.endswith('.java'):
            return class_name

        # Try different source directory patterns
        class_path = class_name.replace('.', '/') + '.java'

        # Check current directory and subdirectories
        for root, dirs, files in os.walk('.'):
            if class_path in files:
                return os.path.join(root, class_path)

        return class_name  # Return as-is if not found

    def _initial_prompt_error_message(self) -> Optional[str]:
        """Extract the current Java exception or error."""
        if not self.jdb_process:
            return None

        try:
            # Try to get the current exception
            output, error = self.jdb_process.run_command('catch')

            if output and 'exception' in output.lower():
                return output.strip()

            # Try to get thread information
            output, error = self.jdb_process.run_command('threads')
            if output:
                return f"Thread state:\n{output}"

        except Exception:
            pass

        return None

    def _initial_prompt_error_details(self) -> Optional[str]:
        """Get additional error details."""
        return None

    def _initial_prompt_command_line(self) -> Optional[str]:
        """Get the Java command line."""
        if not self.current_class:
            return None

        classpath = self.classpath_manager.get_classpath_string()
        return f"java -classpath {classpath} {self.current_class}"

    def _initial_prompt_input(self) -> Optional[str]:
        """Get input information if available."""
        return None

    def _prompt_stack(self) -> Optional[str]:
        """Return a simple backtrace for followup prompts."""
        return None

    def _prompt_history(self) -> str:
        """Get command history."""
        return str(self._history)

    def build_prompt(self, arg, conversing):
        """Build the prompt for the assistant."""
        if not conversing:
            return build_initial_prompt(
                self._initial_prompt_enchriched_stack_trace(),
                self._initial_prompt_error_message(),
                self._initial_prompt_error_details(),
                self._initial_prompt_command_line(),
                self._initial_prompt_input(),
                self._prompt_history(),
                user_text=arg,
            )
        else:
            return build_followup_prompt(
                self._prompt_history(), self._prompt_stack(), arg
            )

    def _initial_prompt_enchriched_stack_trace(self) -> str:
        """Get enriched stack trace."""
        from .stacks import build_enriched_stacktrace
        return build_enriched_stacktrace(self._get_frame_summaries())

    def llm_debug(self, command: str) -> Tuple[str, str]:
        """Execute a JDB command for LLM."""
        if not chatdbg_config.unsafe and not self._is_safe_command(command):
            self._unsafe_cmd = True
            return command, f"Command `{command}` is not allowed."

        return command, self._run_one_command(command)

    def _is_safe_command(self, command: str) -> bool:
        """Check if a JDB command is safe to execute."""
        # Define safe JDB commands
        safe_commands = {
            'locals', 'print', 'dump', 'eval', 'get',
            'list', 'where', 'up', 'down', 'step',
            'cont', 'run', 'threads', 'thread',
            'methods', 'fields', 'classes'
        }

        command_parts = command.strip().split()
        if not command_parts:
            return True

        base_command = command_parts[0].lower()
        return base_command in safe_commands

    def llm_get_code_surrounding(self, filename: str, line_number: int) -> Tuple[str, str]:
        """Get source code surrounding a line."""
        lines = source_analyzer.get_lines_around(filename, line_number)
        return f"code {filename}:{line_number}", '\n'.join(lines)

    def llm_find_definition(self, filename: str, line_number: int, symbol: str) -> Tuple[str, str]:
        """Find definition of a Java symbol."""
        # Try to use javap for class/method information
        if '.' in symbol:
            class_name = symbol.split('.')[0]
            if javap_analyzer.is_available():
                class_info = javap_analyzer.get_class_info(class_name, self.classpath_manager.get_classpath_string())
                if class_info:
                    return f"definition {filename}:{line_number} {symbol}", str(class_info)

        return f"definition {filename}:{line_number} {symbol}", "Definition not found"

    def _supported_functions(self):
        """Get supported LLM functions."""
        functions = [self.llm_debug, self.llm_get_code_surrounding]

        if javap_analyzer.is_available():
            functions.append(self.llm_find_definition)

        return functions

    def _make_assistant(self) -> Assistant:
        """Create the assistant for this debugging session."""
        functions = self._supported_functions()
        instruction_prompt = self.initial_prompt_instructions()

        # Use stdout for printer (JDB doesn't override stdin like GDB)
        import sys
        printer = chatdbg_config.make_printer(sys.__stdout__, self._prompt, "   ", 80)

        assistant = Assistant(
            instruction_prompt,
            model=chatdbg_config.model,
            functions=functions,
            listeners=[
                printer,
                self._log,
            ],
        )

        return assistant

    def initial_prompt_instructions(self):
        """Get initial instructions for the assistant."""
        functions = self._supported_functions()
        return initial_instructions(functions)

    def warn(self, message):
        """Print a warning message."""
        print(message)

    def fail(self, message):
        """Print an error message and raise exception."""
        raise Exception(message)