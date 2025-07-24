# CMDScript Interpreter

## Table of Contents
* [Introduction](#introduction)
* [Features](#features)
    * [Variables](#variables)
    * [Input/Output](#inputoutput)
    * [Control Flow](#control-flow)
    * [System Commands](#system-commands)
    * [Comments](#comments)
* [How to Run](#how-to-run)
* [Example Usage](#example-usage)

## Introduction

CMDScript is a lightweight, custom scripting language interpreter built in Python. It is designed for straightforward scripting tasks, enabling users to automate simple console-based operations, manage data with variables, implement conditional logic, and handle repetitive actions through loops.

## Features

CMDScript provides a set of commands and constructs to build your scripts:

### Variables

Variables are fundamental for storing and manipulating data within your scripts.

* **Declaration with Alias:**
    ```cmdscript
    %<alias> = <variable_name>
    ```
    This line declares a variable with a user-friendly alias. The alias helps categorize or group your variables (e.g., `%int_alias` for integer variables, `%txt_alias` for text variables). The `variable_name` should follow standard naming conventions (alphanumeric and underscores, not starting with a number).
    *Example:* `%int_alias = myScore`

* **Type Definition:**
    ```cmdscript
    <variable_name> = %int|%dec|%txt|%string
    ```
    After declaring a variable with an alias, you *must* define its data type.
    * `%int`: For whole numbers (integers).
    * `%dec`: For decimal numbers (floating-point numbers).
    * `%txt` or `%string`: For text strings.
    *Example:* `myScore = %int`

* **Value Assignment:**
    ```cmdscript
    <variable_name>%value = <value>
    ```
    This command assigns a value to a previously declared and typed variable. The interpreter enforces type validation, so the assigned value must match the variable's declared type.
    * `<value>` can be:
        * A **literal string** enclosed in double quotes (e.g., `"Hello World"`).
        * A **literal number** (e.g., `123`, `45.67`).
        * `%1`: Substitutes the value from the most recent `%icq` input.
        * `%var <another_variable_name>`: Substitutes the value of another declared variable.
        * **Simple Arithmetic Expressions:** Supports `+`, `-`, `*`, `/` between numeric literals, `%1`, or `%var` that resolve to numbers (e.g., `myNumber + 5`). Division by zero will result in an error.
    *Example:*
    ```cmdscript
    myScore%value = 100
    userName%value = "Alice"
    result%value = myScore + 20
    ```

### Input/Output

These commands handle interaction with the user and displaying information.

* **User Input (`%icq`):**
    ```cmdscript
    %icq "Prompt message" %int|%dec|%txt|%string
    ```
    Displays a prompt to the user and waits for input. The input value is then stored and accessible via `%1` for subsequent operations until another `%icq` command is executed. The command also validates the input against the specified type.
    *Example:* `%icq "Please enter your age:" %int`

* **Console Output (`write`):**
    ```cmdscript
    write <token1> <token2> ...
    ```
    Prints one or more tokens to the console on a single line. Tokens can be:
    * Literal strings (e.g., `"Hello"`).
    * Variable values (e.g., `%var myVar`).
    * The current input value (`%1`).
    * Color codes (e.g., `%redtext`, `%bluetext`, `%normal` to reset color).
    * It does *not* automatically add a newline at the end. Use `%NL%` or `send %NL%` for newlines.
    *Example:* `write "Your score is: " %greentext %var myScore %normal`

* **Newline (`send %NL%`):**
    ```cmdscript
    send %NL%
    ```
    Prints a single newline character to the console. Useful for formatting output from `write` commands.
    *Example:*
    ```cmdscript
    write "First line."
    send %NL%
    write "Second line."
    ```

### Control Flow

These constructs enable your script to make decisions and perform repetitive actions. Indentation (spaces or tabs) is crucial for defining blocks of code within `function`, `if`, and `while` statements.

* **Functions (`%f` and Function Calls):**
    ```cmdscript
    %f MyFunction:
        # Commands inside the function
        write "Executing MyFunction"
        send %NL%
    
    # ... later in the script ...
    MyFunction # Call the function
    ```
    Defines a reusable block of code. Functions are declared with `%f FunctionName:` and their body must be indented. To execute a function, simply use its `FunctionName` as a command.

* **Conditional Statements (`%if`, `%else`, `%else if`):**
    ```cmdscript
    %if <condition>
        # Commands if condition is true
    %else if <another_condition>
        # Commands if another_condition is true
    %else
        # Commands if no conditions are true
    ```
    Allows your script to execute different blocks of code based on conditions.
    * **Conditions** compare two values (literals, variables, `%1`) using various operators:
        * `=`: Equality (numeric or case-sensitive string)
        * `X=`: Inequality (numeric or case-sensitive string)
        * `>`: Greater than (numeric only)
        * `<`: Less than (numeric only)
        * `>=`: Greater than or equal to (numeric only)
        * `<=`: Less than or equal to (numeric only)
        * `~`: String contains (case-sensitive)
        * `~=`: String contains (case-insensitive)
    * Code blocks following `%if`, `%else if`, or `%else` must be indented.

* **Loops (`%while`):**
    ```cmdscript
    %while <condition>
        # Commands to repeat
    ```
    Repeatedly executes an indented block of code as long as the specified condition remains true. The condition is re-evaluated at the start of each iteration. There is a built-in safeguard to prevent infinite loops, with a maximum of 10,000 iterations. If this limit is exceeded, the script will terminate.
    *Example:*
    ```cmdscript
    %int_alias = counter
    counter = %int
    counter%value = 0
    %while counter < 5
        write "Count: " %var counter
        send %NL%
        counter%value = counter + 1
    ```

### System Commands

Interact with the operating system and user environment.

* **Wait (`wait`):**
    ```cmdscript
    wait <seconds>
    ```
    Pauses the execution of the script for the specified number of seconds. `<seconds>` can be a decimal value.
    *Example:* `wait 2.5`

* **Clear Console (`clear_console`):**
    ```cmdscript
    clear_console
    clear_console <seconds>
    ```
    Clears all text from the console window.
    * If no argument is provided, it clears instantly.
    * If a numeric value (literal, variable, or `%1`) is provided as `<seconds>`, it will wait for that duration before clearing.
    *Example:*
    ```cmdscript
    write "Clearing in 3 seconds..."
    clear_console 3
    ```

* **Desktop Notification (`msg`):**
    ```cmdscript
    msg %title "Title Text" %subtitle "Subtitle Text"
    ```
    Displays a native desktop notification (toast message) to the user.
    * Requires `win11toast` (for Windows 11) or `win10toast` (for Windows 10) Python packages to be installed (`pip install win11toast` or `pip install win10toast`). If the module is not found, a message `[Notification skipped: No toast module installed]` will be printed instead.
    * `"Title Text"` and `"Subtitle Text"` can be literal strings, `%1`, or `%var` substitutions.
    *Example:* `msg %title "Script Alert" %subtitle "Task completed successfully!"`

### Comments

Comments are non-executable lines used for documenting your script, making it easier to understand.

* **Single-line comments:**
    ```cmdscript
    # This is a comment
    ```
* **Block comments (ignored by interpreter):**
    ```cmdscript
    ## This whole block
    ## is ignored
    ## by the interpreter
    ```

## How to Run

To execute a CMDScript file:

1.  **Save the Interpreter:** Ensure you have the `app.py` interpreter file saved in your working directory.
2.  **Install Dependencies (Optional):** If you plan to use desktop notifications, install the required Python library:
    * For Windows 11: `pip install win11toast`
    * For Windows 10: `pip install win10toast`
3.  **Create Your Script:** Write your CMDScript code and save it with a `.cmdscript` file extension (e.g., `my_script.cmdscript`).
4.  **Execute:** Open your terminal or command prompt, navigate to the directory containing `app.py` and your script, and run the command:
    ```bash
    python app.py your_script.cmdscript
    ```
    You can also provide an initial input value to your script, which will be accessible as `%1`:
    ```bash
    python app.py your_script.cmdscript --input "Some initial text"
    ```

## Example Usage

The `example.cmdscript` file provides an interactive demonstration of many of CMDScript's features. It allows you to select a specific feature (like While Loops, String Comparisons, or Clear Console) and then guides you through a live example of its syntax and functionality. It's an excellent way to see the language in action.

To run the example demo script:
```bash
python app.py example.cmdscript
