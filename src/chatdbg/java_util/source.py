"""Java source code handling utilities for ChatDBG."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class JavaSourceAnalyzer:
    """Analyzes Java source files for debugging support."""

    def __init__(self):
        self.source_cache: Dict[str, List[str]] = {}

    def load_source_file(self, file_path: str) -> Optional[List[str]]:
        """Load a Java source file into memory."""
        if not os.path.exists(file_path):
            return None

        if file_path in self.source_cache:
            return self.source_cache[file_path]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.source_cache[file_path] = lines
                return lines
        except Exception as e:
            print(f"Error reading source file {file_path}: {e}")
            return None

    def find_method_at_line(self, file_path: str, line_number: int) -> Optional[Dict]:
        """Find the method containing the given line number."""
        lines = self.load_source_file(file_path)
        if not lines:
            return None

        # Find the method that contains line_number
        current_method = None
        brace_count = 0
        method_start = -1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check if this line starts a method
            if self._is_method_declaration(stripped) and brace_count == 0:
                current_method = self._parse_method_signature(stripped)
                method_start = i
                brace_count = 0

            # Count braces to track method boundaries
            brace_count += line.count('{') - line.count('}')

            # If we're leaving a method and it contained our line
            if brace_count == 0 and current_method and method_start <= line_number < i:
                current_method['start_line'] = method_start
                current_method['end_line'] = i - 1
                current_method['containing_lines'] = lines[method_start-1:i]
                return current_method

        return None

    def find_class_at_line(self, file_path: str, line_number: int) -> Optional[Dict]:
        """Find the class containing the given line number."""
        lines = self.load_source_file(file_path)
        if not lines:
            return None

        current_class = None
        brace_count = 0
        class_start = -1

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check if this line starts a class
            if self._is_class_declaration(stripped) and brace_count == 0:
                current_class = self._parse_class_signature(stripped)
                class_start = i
                brace_count = 0

            # Count braces to track class boundaries
            brace_count += line.count('{') - line.count('}')

            # If we're leaving a class and it contained our line
            if brace_count == 0 and current_class and class_start <= line_number < i:
                current_class['start_line'] = class_start
                current_class['end_line'] = i - 1
                return current_class

        return None

    def get_lines_around(self, file_path: str, line_number: int, context: int = 5) -> List[str]:
        """Get lines around a specific line number."""
        lines = self.load_source_file(file_path)
        if not lines:
            return []

        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)

        return [f"{i+1:4}: {line.rstrip()}" for i, line in enumerate(lines[start:end], start)]

    def find_variable_declaration(self, file_path: str, variable_name: str, line_number: int) -> Optional[Dict]:
        """Find where a variable was declared."""
        lines = self.load_source_file(file_path)
        if not lines:
            return None

        # Search backwards from line_number for variable declaration
        for i in range(line_number - 1, -1, -1):
            line = lines[i].strip()
            if variable_name in line and ('=' in line or line.endswith(';')):
                # This might be the declaration
                if re.search(rf'\b{re.escape(variable_name)}\b', line):
                    return {
                        'line_number': i + 1,
                        'line_content': line,
                        'type': self._infer_variable_type(line, variable_name)
                    }

        return None

    def _is_method_declaration(self, line: str) -> bool:
        """Check if a line contains a method declaration."""
        # Simple heuristic: contains return type, method name, parentheses
        return ('(' in line and ')' in line and
                not line.startswith('//') and
                not line.startswith('*') and
                not line.startswith('/*'))

    def _is_class_declaration(self, line: str) -> bool:
        """Check if a line contains a class declaration."""
        return (line.startswith('public class ') or
                line.startswith('class ') or
                line.startswith('private class ') or
                line.startswith('protected class ') or
                line.startswith('final class '))

    def _parse_method_signature(self, line: str) -> Dict:
        """Parse a method signature."""
        # Extract method name and parameters
        match = re.search(r'\s+(\w+)\s*\(([^)]*)\)', line)
        if match:
            method_name = match.group(1)
            parameters = match.group(2)

            return {
                'name': method_name,
                'parameters': [param.strip() for param in parameters.split(',') if param.strip()],
                'signature': line.strip()
            }

        return {'name': 'unknown', 'parameters': [], 'signature': line.strip()}

    def _parse_class_signature(self, line: str) -> Dict:
        """Parse a class signature."""
        match = re.search(r'class\s+(\w+)', line)
        if match:
            class_name = match.group(1)
            return {
                'name': class_name,
                'signature': line.strip()
            }

        return {'name': 'unknown', 'signature': line.strip()}

    def _infer_variable_type(self, line: str, variable_name: str) -> str:
        """Infer the type of a variable from its declaration."""
        # Look for type declarations like "String name" or "int count"
        type_pattern = rf'(\w+(?:\.\w+)*)\s+{re.escape(variable_name)}\b'
        match = re.search(type_pattern, line)

        if match:
            return match.group(1)

        # Check for array declarations
        array_pattern = rf'(\w+(?:\.\w+)*\[\])\s+{re.escape(variable_name)}\b'
        match = re.search(array_pattern, line)

        if match:
            return match.group(1)

        return 'unknown'

    def find_imports(self, file_path: str) -> List[str]:
        """Find all import statements in a Java file."""
        lines = self.load_source_file(file_path)
        if not lines:
            return []

        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import '):
                imports.append(stripped[7:].rstrip(';'))

        return imports

    def find_package(self, file_path: str) -> Optional[str]:
        """Find the package declaration in a Java file."""
        lines = self.load_source_file(file_path)
        if not lines:
            return None

        for line in lines[:10]:  # Check first 10 lines
            stripped = line.strip()
            if stripped.startswith('package '):
                return stripped[8:].rstrip(';')

        return None


# Global instance for convenience
source_analyzer = JavaSourceAnalyzer()