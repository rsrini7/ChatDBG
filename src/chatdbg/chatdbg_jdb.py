"""ChatDBG JDB integration for Java debugging."""

import os
import atexit
import sys
from typing import List, Optional

from chatdbg.native_util.jdb_dialog import JDBDialog
from chatdbg.util.config import chatdbg_config
from chatdbg.util.exit_message import chatdbg_was_called, print_exit_message

# JDB Prompt
PROMPT = "(ChatDBG jdb) "

atexit.register(print_exit_message)


class JDBCommand:
    """Base class for JDB commands."""

    def __init__(self, name: str):
        self.name = name

    def invoke(self, command: str, from_tty: bool):
        """Execute the JDB command."""
        raise NotImplementedError


class ChatCommand(JDBCommand):
    """Main chat command for JDB."""

    def __init__(self):
        super().__init__("chat")
        self.dialog: Optional[JDBDialog] = None

    def invoke(self, command: str, from_tty: bool):
        """Start chat dialog."""
        try:
            if not self.dialog:
                self.dialog = JDBDialog(PROMPT)
            self.dialog.dialog(command)
        except Exception as e:
            print(f"Error: {e}")


class WhyCommand(JDBCommand):
    """Why command for JDB."""

    def __init__(self):
        super().__init__("why")
        self.dialog: Optional[JDBDialog] = None

    def invoke(self, command: str, from_tty: bool):
        """Start why dialog."""
        try:
            if not self.dialog:
                self.dialog = JDBDialog(PROMPT)
            self.dialog.dialog(command)
        except Exception as e:
            print(f"Error: {e}")


class ConfigCommand(JDBCommand):
    """Config command for JDB."""

    def __init__(self):
        super().__init__("config")

    def invoke(self, command: str, from_tty: bool):
        """Show configuration."""
        args = command.split()
        message = chatdbg_config.parse_only_user_flags(args)
        print(message)


# Global command instances
chat_cmd = ChatCommand()
why_cmd = WhyCommand()
config_cmd = ConfigCommand()


def initialize_jdb():
    """Initialize JDB integration."""
    # Set up aliases
    print("chat")  # This would normally be handled by JDB alias command
    print("why")   # This would normally be handled by JDB alias command

    print("ChatDBG JDB integration loaded.")
    print("Use 'chat' or 'why' commands to start debugging assistance.")


# Auto-initialize when module is loaded
if __name__ == "__main__":
    initialize_jdb()


# JDB integration functions for use with pyjdb or direct JDB
def start_jdb_session(main_class: str, classpath: str = '.', java_args: List[str] = None):
    """Start a JDB debugging session."""
    dialog = JDBDialog(PROMPT)

    # Set up classpath
    if classpath:
        dialog.classpath_manager = ClasspathManager()
        # Add classpath entries
        for entry in classpath.split(os.pathsep):
            if entry.endswith('.jar'):
                dialog.classpath_manager.add_jar(entry)
            else:
                dialog.classpath_manager.add_class_dir(entry)

    # Initialize JDB process
    dialog.jdb_process = JDBProcess(java_home=dialog.java_home,
                                   classpath=dialog.classpath_manager.get_classpath_string())

    if dialog.jdb_process.start_jdb(main_class, java_args or []):
        return dialog
    else:
        print("Failed to start JDB session")
        return None


def attach_to_running_process(host: str = 'localhost', port: int = 5005):
    """Attach to a running Java process with JDWP debugging."""
    dialog = JDBDialog(PROMPT)

    # This would implement JDWP attachment
    # For now, return the dialog for manual setup
    return dialog