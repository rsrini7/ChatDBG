"""JDB process management for ChatDBG."""

import subprocess
import os
import signal
import time
import threading
import socket
from typing import List, Optional, Tuple, Any, Dict
from queue import Queue, Empty


class JDBProcess:
    """Manages a JDB (Java Debugger) process."""

    def __init__(self, java_home: Optional[str] = None, classpath: str = '.'):
        self.java_home = java_home or os.environ.get('JAVA_HOME', '')
        self.classpath = classpath
        self.process: Optional[subprocess.Popen] = None
        self.jdb_process: Optional[subprocess.Popen] = None
        self.output_queue = Queue()
        self.error_queue = Queue()
        self._stop_event = threading.Event()

    def _get_java_path(self) -> str:
        """Get the path to the java executable."""
        if self.java_home:
            java_path = os.path.join(self.java_home, 'bin', 'java')
            if os.path.exists(java_path):
                return java_path

        # Try system PATH
        try:
            result = subprocess.run(['which', 'java'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        # Fallback to common locations
        common_locations = [
            '/usr/bin/java',
            '/usr/local/bin/java',
            '/opt/java/bin/java',
        ]

        for location in common_locations:
            if os.path.exists(location):
                return location

        raise FileNotFoundError("java command not found. Please ensure JDK is installed.")

    def _find_available_port(self, start_port: int = 5005) -> int:
        """Find an available port for JDWP debugging."""
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('localhost', port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError(f"No available ports found in range {start_port}-{start_port + 100}")

    def start_jdb(self, main_class: str, args: List[str] = None) -> bool:
        """Start JDB attached to a Java process."""
        try:
            # Find an available port for JDWP
            jdwp_port = self._find_available_port()
            print(f"Using JDWP port: {jdwp_port}")

            # First, start the Java process with debugging enabled
            # Ensure classpath includes current directory and samples/java for finding classes
            java_classpath = self.classpath
            if '.' not in java_classpath:
                java_classpath = '.' + os.pathsep + java_classpath
            if 'samples/java' not in java_classpath:
                java_classpath = 'samples/java' + os.pathsep + java_classpath

            java_cmd = [
                self._get_java_path(),
                '-classpath', java_classpath,
                f'-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address={jdwp_port}',
                main_class
            ]

            if args:
                java_cmd.extend(args)

            # Start Java process
            self.process = subprocess.Popen(
                java_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=0
            )

            # Wait a moment for JVM to start
            time.sleep(1)

            if self.process.poll() is not None:
                # Process failed to start
                print(f"Java process failed to start. Return code: {self.process.poll()}")
                stdout, stderr = self.process.communicate()
                print(f"Java process stdout: {stdout}")
                print(f"Java process stderr: {stderr}")
                return False

            # Now start JDB attached to the JVM
            # Ensure classpath includes current directory and samples/java for finding compiled classes
            jdb_classpath = self.classpath
            if '.' not in jdb_classpath:
                jdb_classpath = '.' + os.pathsep + jdb_classpath
            if 'samples/java' not in jdb_classpath:
                jdb_classpath = 'samples/java' + os.pathsep + jdb_classpath

            # Now start JDB attached to the JVM
            # Ensure classpath includes current directory for finding compiled classes
            jdb_classpath = self.classpath
            if '.' not in jdb_classpath:
                jdb_classpath = '.' + os.pathsep + jdb_classpath
            if 'samples/java' not in jdb_classpath:
                jdb_classpath = 'samples/java' + os.pathsep + jdb_classpath

            # Use the correct JDB syntax for connecting to a running JVM
            jdb_cmd = [
                'jdb',
                '-classpath', jdb_classpath,
                '-connect', f'com.sun.jdi.SocketAttach:hostname=localhost,port={jdwp_port}'
            ]

            # Start JDB process
            print(f"Starting JDB with command: {' '.join(jdb_cmd)}")
            self.jdb_process = subprocess.Popen(
                jdb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=0
            )

            # Check if JDB process started successfully
            time.sleep(2)
            if self.jdb_process.poll() is not None:
                print(f"JDB process failed to start. Return code: {self.jdb_process.poll()}")
                stdout, stderr = self.jdb_process.communicate()
                print(f"JDB process stdout: {stdout}")
                print(f"JDB process stderr: {stderr}")
                return False

            # Start output monitoring threads
            self._start_output_monitoring()

            print("JDB process started successfully")
            return True

        except Exception as e:
            print(f"Error starting JDB: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _start_output_monitoring(self):
        """Start threads to monitor JDB output."""
        if not self.jdb_process:
            return

        # Monitor stdout
        def monitor_output(stream, queue):
            try:
                while not self._stop_event.is_set():
                    line = stream.readline()
                    if not line:
                        break
                    queue.put(line.strip())
            except Exception:
                pass

        self.stdout_thread = threading.Thread(
            target=monitor_output,
            args=(self.jdb_process.stdout, self.output_queue)
        )
        self.stderr_thread = threading.Thread(
            target=monitor_output,
            args=(self.jdb_process.stderr, self.error_queue)
        )

        self.stdout_thread.daemon = True
        self.stderr_thread.daemon = True
        self.stdout_thread.start()
        self.stderr_thread.start()

    def send_command(self, command: str) -> bool:
        """Send a command to JDB."""
        if not self.jdb_process or not self.jdb_process.stdin:
            return False

        try:
            self.jdb_process.stdin.write(command + '\n')
            self.jdb_process.stdin.flush()
            return True
        except Exception:
            return False

    def get_output(self, timeout: float = 1.0) -> Tuple[List[str], List[str]]:
        """Get output from JDB with timeout."""
        stdout_lines = []
        stderr_lines = []

        # Collect available output
        while True:
            try:
                line = self.output_queue.get_nowait()
                stdout_lines.append(line)
            except Empty:
                break

        while True:
            try:
                line = self.error_queue.get_nowait()
                stderr_lines.append(line)
            except Empty:
                break

        return stdout_lines, stderr_lines

    def wait_for_prompt(self, timeout: float = 5.0) -> bool:
        """Wait for JDB prompt indicating command completion."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            lines, _ = self.get_output(timeout=0.1)

            for line in lines:
                if line.startswith('>') or line.endswith('>'):
                    return True

            time.sleep(0.1)

        return False

    def run_command(self, command: str, timeout: float = 5.0) -> Tuple[str, str]:
        """Run a JDB command and return output."""
        if not self.send_command(command):
            return "", "Failed to send command"

        # Wait for command completion
        if not self.wait_for_prompt(timeout):
            return "", "Command timeout"

        lines, error_lines = self.get_output()

        return '\n'.join(lines), '\n'.join(error_lines)

    def stop(self):
        """Stop JDB and Java processes."""
        self._stop_event.set()

        if self.jdb_process:
            try:
                self.jdb_process.terminate()
                self.jdb_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.jdb_process.kill()

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def is_running(self) -> bool:
        """Check if JDB process is still running."""
        return (self.jdb_process is not None and
                self.jdb_process.poll() is None)

    def get_stack_trace(self) -> List[Dict]:
        """Get current stack trace from JDB."""
        output, error = self.run_command('where')

        if error or not output:
            return []

        return self._parse_stack_trace(output)

    def _parse_stack_trace(self, output: str) -> List[Dict]:
        """Parse JDB stack trace output."""
        frames = []
        lines = output.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('>'):
                continue

            # Parse lines like:
            # [1] com.example.MyClass.main (MyClass.java:15)
            match = re.match(r'\[\d+\]\s+(\S+)\s+\((\S+):(\d+)\)', line)
            if match:
                frames.append({
                    'method': match.group(1),
                    'file': match.group(2),
                    'line': int(match.group(3))
                })

        return frames

    def get_locals(self) -> Dict:
        """Get local variables from current frame."""
        output, error = self.run_command('locals')

        if error or not output:
            return {}

        return self._parse_locals(output)

    def _parse_locals(self, output: str) -> Dict:
        """Parse JDB locals output."""
        locals_dict = {}
        lines = output.split('\n')

        for line in lines:
            line = line.strip()
            if '=' in line:
                parts = line.split('=', 1)
                var_name = parts[0].strip()
                var_value = parts[1].strip()
                locals_dict[var_name] = var_value

        return locals_dict


# Utility functions for finding Java processes
def find_java_processes() -> List[Dict]:
    """Find running Java processes that might be debuggable."""
    try:
        result = subprocess.run(['jps', '-v'], capture_output=True, text=True)
        if result.returncode != 0:
            return []

        processes = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header

        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[0]
                    main_class = parts[1]
                    processes.append({
                        'pid': pid,
                        'main_class': main_class,
                        'args': ' '.join(parts[2:]) if len(parts) > 2 else ''
                    })

        return processes

    except FileNotFoundError:
        # jps command not available
        return []