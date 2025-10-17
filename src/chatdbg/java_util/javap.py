"""Java bytecode analysis utilities using javap."""

import subprocess
import re
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class JavapAnalyzer:
    """Analyzes Java bytecode using javap command."""

    def __init__(self, java_home: Optional[str] = None):
        self.java_home = java_home or os.environ.get('JAVA_HOME', '')

    def _get_javap_path(self) -> str:
        """Get the path to the javap executable."""
        if self.java_home:
            javap_path = os.path.join(self.java_home, 'bin', 'javap')
            if os.path.exists(javap_path):
                return javap_path

        # Try system PATH
        try:
            result = subprocess.run(['which', 'javap'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        # Fallback to common locations
        common_locations = [
            '/usr/bin/javap',
            '/usr/local/bin/javap',
            '/opt/java/bin/javap',
        ]

        for location in common_locations:
            if os.path.exists(location):
                return location

        raise FileNotFoundError("javap command not found. Please ensure JDK is installed.")

    def get_class_info(self, class_name: str, classpath: str = '.') -> Optional[Dict]:
        """Get detailed information about a Java class using javap."""
        try:
            javap_cmd = [
                self._get_javap_path(),
                '-classpath', classpath,
                '-public',  # Show public members only for security
                class_name
            ]

            result = subprocess.run(javap_cmd, capture_output=True, text=True, check=True)

            return self._parse_javap_output(result.stdout)

        except subprocess.CalledProcessError as e:
            print(f"Error running javap: {e}")
            return None
        except FileNotFoundError as e:
            print(f"Javap not found: {e}")
            return None

    def get_method_bytecode(self, class_name: str, method_name: str, classpath: str = '.') -> Optional[str]:
        """Get bytecode for a specific method."""
        try:
            javap_cmd = [
                self._get_javap_path(),
                '-classpath', classpath,
                '-c',  # Show bytecode
                class_name
            ]

            result = subprocess.run(javap_cmd, capture_output=True, text=True, check=True)

            return self._extract_method_bytecode(result.stdout, method_name)

        except subprocess.CalledProcessError as e:
            print(f"Error running javap: {e}")
            return None

    def _parse_javap_output(self, output: str) -> Dict:
        """Parse javap output into structured data."""
        lines = output.strip().split('\n')
        class_info = {
            'class': '',
            'extends': '',
            'implements': [],
            'methods': [],
            'fields': [],
            'constants': []
        }

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('public class ') or line.startswith('class '):
                # Parse class declaration
                match = re.match(r'(?:public\s+)?class\s+(\S+)(?:\s+extends\s+(\S+))?(?:\s+implements\s+(.+))?', line)
                if match:
                    class_info['class'] = match.group(1)
                    if match.group(2):
                        class_info['extends'] = match.group(2)
                    if match.group(3):
                        class_info['implements'] = [impl.strip() for impl in match.group(3).split(',')]

            elif line.startswith('public ') and 'method' not in line:
                # Parse method signatures
                method_info = self._parse_method_signature(line)
                if method_info:
                    class_info['methods'].append(method_info)

            elif line and not line.startswith(' ') and not line.startswith('{') and not line.startswith('}'):
                # Parse field declarations
                field_info = self._parse_field_declaration(line)
                if field_info:
                    class_info['fields'].append(field_info)

            i += 1

        return class_info

    def _parse_method_signature(self, line: str) -> Optional[Dict]:
        """Parse a Java method signature."""
        # Handle method signatures like:
        # "public java.lang.String toString();"
        # "public void <init>();"
        # "public static void main(java.lang.String[]);"

        match = re.match(r'(\w+(?:\s+\w+)*)\s+(\w+)\s*\(([^)]*)\)', line.strip())
        if not match:
            return None

        modifiers_and_return = match.group(1)
        method_name = match.group(2)
        parameters = match.group(3)

        # Split modifiers and return type
        parts = modifiers_and_return.split()
        return_type = parts[-1]
        modifiers = parts[:-1]

        return {
            'name': method_name,
            'return_type': return_type,
            'modifiers': modifiers,
            'parameters': [param.strip() for param in parameters.split(',') if param.strip()],
            'signature': line.strip()
        }

    def _parse_field_declaration(self, line: str) -> Optional[Dict]:
        """Parse a Java field declaration."""
        # Handle field declarations like:
        # "public static final int MAX_SIZE;"
        # "private java.lang.String name;"

        match = re.match(r'(\w+(?:\s+\w+)*)\s+(\w+);', line.strip())
        if not match:
            return None

        type_and_modifiers = match.group(1)
        field_name = match.group(2)

        parts = type_and_modifiers.split()
        field_type = parts[-1]
        modifiers = parts[:-1]

        return {
            'name': field_name,
            'type': field_type,
            'modifiers': modifiers,
            'declaration': line.strip()
        }

    def _extract_method_bytecode(self, output: str, method_name: str) -> Optional[str]:
        """Extract bytecode for a specific method from javap output."""
        lines = output.split('\n')
        method_bytecode = []
        in_target_method = False

        for line in lines:
            if f'{method_name}():' in line:
                in_target_method = True
                method_bytecode.append(line)
            elif in_target_method:
                if line.strip() and not line.startswith('  ') and not line.startswith('\t'):
                    # End of method
                    break
                elif in_target_method:
                    method_bytecode.append(line)

        return '\n'.join(method_bytecode) if method_bytecode else None

    def is_available(self) -> bool:
        """Check if javap is available."""
        try:
            self._get_javap_path()
            return True
        except FileNotFoundError:
            return False


# Global instance for convenience
javap_analyzer = JavapAnalyzer()