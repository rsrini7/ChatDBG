#!/usr/bin/env python3
"""Test script for ChatDBG JDB integration."""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def test_java_compilation():
    """Test Java compilation with debug information."""
    print("Testing Java compilation...")

    # Create a simple test Java program
    test_code = '''
public class TestProgram {
    public static void main(String[] args) {
        String message = "Hello, ChatDBG!";
        System.out.println(message);

        // Intentional null pointer for testing
        String nullStr = null;
        if (args.length > 0) {
            nullStr = args[0];
        }

        if (nullStr != null) {
            System.out.println("Length: " + nullStr.length());
        } else {
            System.out.println("String is null!");
        }
    }
}
'''

    with tempfile.TemporaryDirectory() as temp_dir:
        java_file = Path(temp_dir) / "TestProgram.java"
        class_file = Path(temp_dir) / "TestProgram.class"

        # Write Java source
        java_file.write_text(test_code)

        # Compile with debug information
        result = subprocess.run(
            ['javac', '-g', str(java_file)],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False

        if not class_file.exists():
            print("Class file not generated")
            return False

        print("✓ Java compilation successful")
        return True


def test_jdb_availability():
    """Test if JDB is available."""
    print("Testing JDB availability...")

    try:
        result = subprocess.run(
            ['jdb', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✓ JDB is available")
            return True
        else:
            print(f"JDB check failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print("✗ JDB not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("✗ JDB check timed out")
        return False


def test_chatdbg_jdb_import():
    """Test ChatDBG JDB module import."""
    print("Testing ChatDBG JDB module import...")

    try:
        # Add src to Python path for testing
        import sys
        sys.path.insert(0, 'src')

        from chatdbg.chatdbg_jdb import JDBDialog, start_jdb_session
        from chatdbg.java_util.classpath import ClasspathManager
        from chatdbg.java_util.javap import javap_analyzer
        from chatdbg.java_util.source import source_analyzer

        print("✓ All JDB modules imported successfully")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_classpath_manager():
    """Test classpath management functionality."""
    print("Testing classpath manager...")

    try:
        # Add src to Python path for testing
        import sys
        sys.path.insert(0, 'src')

        from chatdbg.java_util.classpath import ClasspathManager

        manager = ClasspathManager()

        # Test basic functionality
        manager.add_class_dir('.')
        classpath = manager.get_classpath_string()

        if classpath:
            print("✓ Classpath manager working")
            return True
        else:
            print("✗ Classpath manager returned empty classpath")
            return False

    except Exception as e:
        print(f"✗ Classpath manager test failed: {e}")
        return False


def test_javap_analyzer():
    """Test javap analyzer functionality."""
    print("Testing javap analyzer...")

    try:
        # Add src to Python path for testing
        import sys
        sys.path.insert(0, 'src')

        from chatdbg.java_util.javap import javap_analyzer

        if javap_analyzer.is_available():
            print("✓ Javap analyzer is available")
            return True
        else:
            print("! Javap analyzer not available (javap command not found)")
            return True  # Not critical for basic functionality

    except Exception as e:
        print(f"✗ Javap analyzer test failed: {e}")
        return False


def test_source_analyzer():
    """Test source code analyzer."""
    print("Testing source analyzer...")

    try:
        # Add src to Python path for testing
        import sys
        sys.path.insert(0, 'src')

        from chatdbg.java_util.source import source_analyzer

        # Create a test Java file
        test_code = '''
public class TestSource {
    private String name;

    public void setName(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }
}
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            lines = source_analyzer.get_lines_around(temp_file, 5, context=2)

            if lines and len(lines) > 0:
                print("✓ Source analyzer working")
                return True
            else:
                print("✗ Source analyzer returned no lines")
                return False

        finally:
            os.unlink(temp_file)

    except Exception as e:
        print(f"✗ Source analyzer test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("ChatDBG JDB Integration Test Suite")
    print("=" * 40)

    tests = [
        test_java_compilation,
        test_jdb_availability,
        test_chatdbg_jdb_import,
        test_classpath_manager,
        test_javap_analyzer,
        test_source_analyzer,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print()
        if test():
            passed += 1

    print()
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! JDB integration is ready.")
        return 0
    else:
        print("✗ Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())