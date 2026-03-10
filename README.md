# CMDScript Interpreter
## Technical Documentation & User Guide

---

## 1. Introduction
[cite_start]CMDScript is a lightweight, custom scripting language interpreter built in Python. [cite_start]It is designed for straightforward console automation, allowing users to manage data with typed variables, implement complex branching logic, and create reusable functions.

---

## 2. Language Features

### 2.1 Variables & Data Types
[cite_start]CMDScript uses a three-step process for memory management to ensure type safety.

* [cite_start]**Declaration**: Use `%newestvar` to create a new variable name.
    ```cmdscript
    %newestvar = PlayerName
    ```
* **Typing**: You must define a type before assigning values.
    * `%int`: Whole numbers.
    * `%dec`: Decimal/Floating-point numbers.
    * `%string` / `%txt`: Text data.
    ```cmdscript
    PlayerName = %string
    ```
* **Assignment**: Use the `%value` suffix to store data.
    ```cmdscript
    PlayerName%value = "Aldrich"
    ```

### 2.2 Input & Output
* [cite_start]**User Input (`%icq`)**: Displays a prompt and stores the result in the `%1` buffer.
    ```cmdscript
    %icq "Enter your age:" %int
    Age%value = %1
    ```
* [cite_start]**Console Output (`write`)**: Displays text or variables. [cite_start]Use `%var Name` to inject variable values.
    ```cmdscript
    write %bluetext "Hello, " %var PlayerName
    ```
* [cite_start]**Newlines**: The `write` command does not end in a newline. [cite_start]Use `send %NL%` to move to the next line.

### 2.3 System Commands
* [cite_start]**Clear Screen (`%cls`)**: Instantly clears the terminal window[cite: 1].
* [cite_start]**Wait (`wait`)**: Pauses execution for a specified number of seconds.
    ```cmdscript
    wait 2.5
    ```
* [cite_start]**Notifications (`msg`)**: Sends a desktop toast notification.
    ```cmdscript
    msg %title "Alert" %subtitle "Process Complete"
    ```

---

## 3. Control Flow (Block Logic)
[cite_start]**Important**: CMDScript relies on indentation to define the scope of functions, loops, and conditionals.

### 3.1 Functions (`%f`)
Define reusable code blocks. [cite_start]All code inside the function must be indented.
```cmdscript
%f SayGoodbye:
    write "Goodbye!"
    send %NL%

# Call the function by its name
SayGoodbye

## 3.2 Conditionals (`%if / %else`)

Supports numeric and string comparisons.

**Operators:**
- `==`
- `!=` (not equal)
- `>`
- `<`
- `>=`
- `<=`
- `~` (contains)
- `~=` (case-insensitive contains)

### Code snippet

```
%if Score >= 10
    write "You Win!"
%else
    write "Try Again!"
```

---

## 4. How to Run

1. **Requirement:** Ensure Python 3.x is installed.

2. **Dependencies:**  
   For notifications, run:
   ```bash
   pip install win11toast
   ```

3. **Execution:** Run your script via the terminal:

   ```bash
   python app.py your_script.cmdscript
   ```

4. **Optional Input:** Provide initial text accessible as `%1`:

   ```bash
   python app.py your_script.cmdscript --input "Initial text"
   ```

---

*Generated for CMDScript Version 1.2*

> Now that the documentation is complete, are you planning to add any new features?
