# ChatDBG JDB Integration - Java Debugging Guide

## Overview

ChatDBG now supports Java debugging through JDB (Java Debugger) integration, enabling AI-assisted debugging for Java applications including enterprise applications and Spring Boot projects.

## Features

- **Full JDB Integration**: Complete Java debugger support with AI assistance
- **Enterprise Java Support**: Spring Boot, dependency injection, and web application debugging
- **Classpath Management**: Automatic detection and management of complex Java classpaths
- **Java-Specific Analysis**: Bytecode analysis, thread debugging, and memory inspection
- **Source Code Integration**: Enhanced source code analysis for Java files

## Installation

### Prerequisites

1. **Java Development Kit (JDK)**: JDK 8 or higher
   ```bash
   # Check if JDK is installed
   java -version
   javac -version
   ```

2. **ChatDBG Installation**:
   ```bash
   python3 -m pip install chatdbg
   ```

### Optional Dependencies

No additional packages are required for Java debugging. ChatDBG uses JDK's built-in tools (javap, jdb) for Java debugging functionality.

## Quick Start

### Basic Java Application Debugging

1. **Compile your Java program with debug information**:
   ```bash
   javac -g MyProgram.java
   ```

2. **Start ChatDBG with JDB**:
   ```bash
   chatdbg --java MyProgram
   ```

3. **When the program hits a breakpoint or exception, use**:
   ```java
   (ChatDBG jdb) why
   ```
   Ask questions like "Why is this null pointer exception occurring?" or "How do I fix this Spring dependency issue?"

### Spring Boot Application Debugging

For enterprise applications:

1. **Set up classpath** (Maven example):
   ```bash
   export CLASSPATH=".:$(find ~/.m2/repository -name '*.jar' | tr '\n' ':')"
   ```

2. **Start with debugging**:
   ```bash
   chatdbg --java com.example.MySpringApp
   ```

## Usage Examples

### Example 1: Null Pointer Exception

```java
// NullPointerExample.java
public class NullPointerExample {
    private List<String> items;

    public void processItems() {
        for (String item : items) {  // NullPointerException here
            System.out.println(item.toUpperCase());
        }
    }

    public static void main(String[] args) {
        new NullPointerExample().processItems();
    }
}
```

**Debugging session**:
```java
(ChatDBG jdb) why
# AI explains: The NullPointerException occurs because 'items' is null.
# The list was never initialized before the for-each loop tries to iterate over it.

(ChatDBG jdb) locals
# Shows current local variables and their values

(ChatDBG jdb) print items
# Shows items is null
```

### Example 2: Spring Boot Dependency Issue

```java
@RestController
public class UserController {
    @Autowired
    private UserService userService;  // Could be null if not properly configured

    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.getUserById(id);  // NullPointerException if userService is null
    }
}
```

**Debugging session**:
```java
(ChatDBG jdb) why
# AI explains: The NullPointerException occurs because userService is null.
# This typically happens when Spring's @Autowired dependency injection fails.

(ChatDBG jdb) print userService
# Confirms userService is null

(ChatDBG jdb) threads
# Shows application thread state
```

## JDB Commands

### Basic Debugging Commands

- `locals` - Show local variables in current frame
- `print <expression>` - Evaluate Java expressions
- `dump <object>` - Show detailed object information
- `where` - Show current stack trace
- `up`/`down` - Navigate stack frames
- `cont` - Continue execution
- `step` - Step to next line

### Java-Specific Commands

- `fields <class>` - Show class fields
- `methods <class>` - Show class methods
- `classes` - Show loaded classes
- `threads` - Show thread information
- `thread <id>` - Switch to specific thread

### ChatDBG Integration Commands

- `chat <message>` - Start AI chat session
- `why` - Ask AI for root cause analysis
- `config` - Show/modify ChatDBG configuration
- `history` - Show command history

## Configuration

### Environment Variables

```bash
export JAVA_HOME=/path/to/jdk
export CHATDBG_MODEL=gpt-4o  # AI model to use
export CHATDBG_LOG=debug.log  # Log file location
```

### Configuration Options

```java
(ChatDBG jdb) config --unsafe
# Allow potentially unsafe debugger commands

(ChatDBG jdb) config --model gpt-4
# Use different AI model

(ChatDBG jdb) config --log debug.log
# Set log file location
```

## Advanced Features

### Classpath Management

ChatDBG automatically detects and manages Java classpaths:

- **Maven projects**: Automatically finds JARs in `target/` directories
- **Gradle projects**: Detects classes in `build/` directories
- **Custom JARs**: Add specific JAR files to classpath
- **Source paths**: Automatically locates source files

### Bytecode Analysis

Use `javap` integration for bytecode analysis:

```java
(ChatDBG jdb) print myObject.getClass()
# Shows class information

# AI can analyze bytecode for optimization suggestions
(ChatDBG jdb) why
# "This method could be optimized by..."
```

### Thread Debugging

Debug multi-threaded Java applications:

```java
(ChatDBG jdb) threads
# Show all threads and their states

(ChatDBG jdb) thread 1
# Switch to thread 1

(ChatDBG jdb) print threadName
# Show current thread name
```

### Memory Analysis

Analyze JVM memory usage:

```java
(ChatDBG jdb) print System.gc()
# Suggest garbage collection

# AI can analyze memory patterns
(ChatDBG jdb) why
# "Memory leak detected in..."
```

## Enterprise Application Debugging

### Spring Boot Applications

1. **Dependency Injection Issues**:
   ```java
   (ChatDBG jdb) why
   # AI explains: "@Autowired field is null because the Spring context
   # couldn't find a matching bean. Check @Service annotation..."
   ```

2. **Configuration Problems**:
   ```java
   (ChatDBG jdb) print applicationContext.getBeanDefinitionNames()
   # Show all Spring beans
   ```

3. **Database Connection Issues**:
   ```java
   (ChatDBG jdb) print dataSource.getConnection()
   # Test database connectivity
   ```

### Web Application Debugging

1. **HTTP Request Issues**:
   ```java
   (ChatDBG jdb) print request.getParameterMap()
   # Show HTTP request parameters
   ```

2. **Session Problems**:
   ```java
   (ChatDBG jdb) print session.getAttributeNames()
   # Show session attributes
   ```

## Troubleshooting

### Common Issues

1. **"JDB process not started"**
   - Ensure Java program is compiled with `-g` flag
   - Check that the main class is correct
   - Verify classpath includes all dependencies

2. **"Command not recognized"**
   - Use valid JDB commands
   - Check if program is suspended at breakpoint

3. **"Class not found"**
   - Verify classpath includes required JARs
   - Check source file locations
   - Ensure correct package structure

4. **"Connection refused" (Remote debugging)**
   - Ensure JDWP port is accessible
   - Check firewall settings
   - Verify JVM debugging agent is attached

### Performance Tips

1. **Use appropriate AI models**:
   ```bash
   export CHATDBG_MODEL=gpt-4o  # Faster responses
   ```

2. **Enable logging for debugging**:
   ```bash
   export CHATDBG_LOG=chatdbg-debug.log
   ```

3. **Use unsafe mode for advanced commands**:
   ```java
   (ChatDBG jdb) config --unsafe
   ```

## Integration with IDEs

### IntelliJ IDEA

1. **Set up remote debugging**:
   - Run → Edit Configurations → Add new configuration → Remote JVM Debug
   - Set port (e.g., 5005)
   - Start with debugging enabled

2. **Attach ChatDBG**:
   ```bash
   chatdbg --java MyClass
   ```

### Eclipse

1. **Enable debugging**:
   - Run → Debug Configurations → Remote Java Application
   - Configure connection properties

2. **Use ChatDBG**:
   ```bash
   chatdbg --java MyClass
   ```

## Best Practices

### For Development

1. **Always compile with debug information**:
   ```bash
   javac -g -d build/classes -cp "lib/*" src/main/java/**/*.java
   ```

2. **Use meaningful variable names**:
   ```java
   // Good
   UserService userService;

   // Avoid
   UserService u;
   ```

3. **Add logging for debugging**:
   ```java
   logger.debug("Processing user: {}", userId);
   ```

### For Production Debugging

1. **Enable remote debugging in production**:
   ```bash
   java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005
   ```

2. **Use appropriate log levels**:
   ```java
   logger.info("Application started successfully");
   ```

3. **Monitor thread states**:
   ```java
   (ChatDBG jdb) threads
   ```

## Contributing

To contribute to ChatDBG JDB integration:

1. **Report issues**: Use GitHub issues with `jdb` label
2. **Submit pull requests**: Follow existing code patterns
3. **Add test cases**: Include Java sample programs
4. **Update documentation**: Keep this guide current

## Support

- **Documentation**: This guide and sample programs
- **Issues**: GitHub issue tracker
- **Discussions**: GitHub discussions for questions
- **Email**: Contact the ChatDBG team

---

*ChatDBG JDB integration makes Java debugging conversational and intelligent, helping developers understand and fix issues faster than traditional debugging methods.*