"""Java classpath management utilities for ChatDBG."""

import os
import glob
from pathlib import Path
from typing import List, Optional, Set


class ClasspathManager:
    """Manages Java classpath construction and validation."""

    def __init__(self, java_home: Optional[str] = None):
        self.java_home = java_home or os.environ.get('JAVA_HOME', '')
        self._classpath_entries: Set[str] = set()

    def add_jar_dir(self, directory: str) -> None:
        """Add all JAR files from a directory to classpath."""
        if not os.path.exists(directory):
            return

        path = Path(directory)
        jar_files = path.glob('*.jar')
        for jar in jar_files:
            self._classpath_entries.add(str(jar))

    def add_class_dir(self, directory: str) -> None:
        """Add a directory containing compiled classes."""
        if os.path.exists(directory):
            self._classpath_entries.add(directory)

    def add_jar(self, jar_path: str) -> None:
        """Add a specific JAR file."""
        if os.path.exists(jar_path) and jar_path.endswith('.jar'):
            self._classpath_entries.add(jar_path)

    def add_maven_dependencies(self, pom_path: str) -> None:
        """Add dependencies from Maven pom.xml (simplified)."""
        # This would parse pom.xml and extract dependencies
        # For now, just add target directories
        pom_dir = os.path.dirname(pom_path)
        target_dir = os.path.join(pom_dir, 'target')
        if os.path.exists(target_dir):
            self.add_jar_dir(target_dir)

    def add_gradle_dependencies(self, build_file: str) -> None:
        """Add dependencies from Gradle build file (simplified)."""
        # This would parse build.gradle and extract dependencies
        # For now, just add build directories
        build_dir = os.path.dirname(build_file)
        classes_dir = os.path.join(build_dir, 'build', 'classes')
        if os.path.exists(classes_dir):
            self.add_class_dir(classes_dir)

        libs_dir = os.path.join(build_dir, 'build', 'libs')
        if os.path.exists(libs_dir):
            self.add_jar_dir(libs_dir)

    def get_classpath_string(self) -> str:
        """Get the classpath as a colon/semicolon separated string."""
        if not self._classpath_entries:
            return '.'

        entries = list(self._classpath_entries)
        # Use os.pathsep for cross-platform compatibility
        return os.pathsep.join(entries)

    def find_class(self, class_name: str) -> Optional[str]:
        """Find the JAR file or directory containing a specific class."""
        # Convert class name to file path (com.example.MyClass -> com/example/MyClass.class)
        class_filename = class_name.replace('.', '/') + '.class'

        for entry in self._classpath_entries:
            if entry.endswith('.jar'):
                # For JAR files, we'd need to check inside the JAR
                # This is a simplified implementation
                continue
            else:
                # Check directory structure
                class_file = os.path.join(entry, class_filename)
                if os.path.exists(class_file):
                    return entry

        return None

    def validate_classpath(self) -> List[str]:
        """Validate classpath entries and return any issues."""
        issues = []

        for entry in self._classpath_entries:
            if not os.path.exists(entry):
                issues.append(f"Classpath entry does not exist: {entry}")
            elif entry.endswith('.jar'):
                if not os.path.isfile(entry):
                    issues.append(f"JAR file is not a regular file: {entry}")
            else:
                if not os.path.isdir(entry):
                    issues.append(f"Class directory is not a directory: {entry}")

        return issues


def detect_java_project_classpath(project_root: str) -> ClasspathManager:
    """Auto-detect classpath for a Java project."""
    manager = ClasspathManager()
    project_path = Path(project_root)

    # Check for Maven project
    if (project_path / 'pom.xml').exists():
        manager.add_maven_dependencies(str(project_path / 'pom.xml'))

    # Check for Gradle project
    if (project_path / 'build.gradle').exists() or (project_path / 'build.gradle.kts').exists():
        gradle_file = 'build.gradle' if (project_path / 'build.gradle').exists() else 'build.gradle.kts'
        manager.add_gradle_dependencies(str(project_path / gradle_file))

    # Add common directories
    manager.add_class_dir(str(project_path / 'build' / 'classes'))
    manager.add_class_dir(str(project_path / 'target' / 'classes'))
    manager.add_class_dir(str(project_path / 'out' / 'production' / 'classes'))

    # Add lib directories
    manager.add_jar_dir(str(project_path / 'lib'))
    manager.add_jar_dir(str(project_path / 'libs'))

    return manager