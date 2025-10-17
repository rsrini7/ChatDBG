# Java Sample Programs for ChatDBG JDB Integration

This directory contains sample Java programs for testing the ChatDBG JDB integration.

## Prerequisites

1. **Java Development Kit (JDK)**: Ensure JDK 8 or higher is installed
2. **ChatDBG**: Install ChatDBG with JDB support
3. **Build tools**: Maven or Gradle for dependency management

## Sample Programs

### 1. NullPointerExample.java

A simple Java program demonstrating common null pointer exception scenarios.

**Features demonstrated:**
- Null pointer exceptions in collections
- Defensive programming practices
- Exception handling patterns

**To compile and run:**
```bash
javac -g NullPointerExample.java
java NullPointerExample
```

**Debugging scenario:**
The program will throw a `NullPointerException` when trying to process null items in a list.

### 2. SpringBootExample.java

A Spring Boot application demonstrating enterprise Java debugging scenarios.

**Features demonstrated:**
- Spring dependency injection issues
- REST controller debugging
- Service layer debugging
- Exception handling in web applications

**To compile and run:**
```bash
# Compile
javac -cp "$(find ~/.m2/repository -name '*.jar' | head -20 | tr '\n' ':')" -g SpringBootExample.java

# Run (requires manual classpath setup for Spring dependencies)
java -cp ".:$(find ~/.m2/repository -name 'spring-*.jar' | head -10 | tr '\n' ':')" SpringBootExample
```

## Using with ChatDBG JDB

### Basic Usage

1. **Compile with debug information:**
```bash
javac -g YourProgram.java
```

2. **Start ChatDBG with JDB:**
```bash
python3 -m chatdbg --java YourProgram
```

3. **In the debugger, use:**
   - `chat` or `why` to ask questions about the code
   - `locals` to see local variables
   - `print <expression>` to evaluate expressions
   - `where` to see the stack trace

### Enterprise Application Debugging

For Spring Boot applications:

1. **Set up proper classpath:**
```bash
export CLASSPATH=".:lib/*:$(find ~/.m2/repository -name 'spring-*.jar' | tr '\n' ':')"
```

2. **Start with remote debugging:**
```bash
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005 \
     -cp $CLASSPATH YourSpringApp
```

3. **Attach ChatDBG JDB:**
```bash
python3 -m chatdbg --java --attach 5005 YourSpringApp
```

## Common Debugging Scenarios

### Null Pointer Exceptions
```
(ChatDBG jdb) why
# Ask about null pointer causes and fixes
```

### Spring Dependency Issues
```
(ChatDBG jdb) why
# Ask about @Autowired failures and injection problems
```

### Threading Issues
```
(ChatDBG jdb) threads
# Examine thread states and synchronization issues
```

### Performance Issues
```
(ChatDBG jdb) why
# Ask about performance bottlenecks and optimization
```

## JDB Commands for Java Debugging

- `locals` - Show local variables
- `print <expression>` - Evaluate Java expressions
- `dump <object>` - Show object details
- `fields <class>` - Show class fields
- `methods <class>` - Show class methods
- `threads` - Show thread information
- `where` - Show stack trace
- `up`/`down` - Navigate stack frames

## Troubleshooting

### Common Issues

1. **"Command not recognized"**
   - Ensure you're using valid JDB commands
   - Check if the program is properly suspended

2. **Class not found errors**
   - Verify classpath includes all required JARs
   - Check source file locations

3. **No debug information**
   - Compile with `javac -g` flag
   - Ensure source files are available

### Getting Help

- Use `config` command to see ChatDBG configuration options
- Use `history` to see previous commands
- Use `test_prompt` to debug prompt generation