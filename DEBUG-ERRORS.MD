### DEBUG-ERRORS.MD

```markdown
# CMDScript Debugging & Common Errors

## Table of Contents
* [Introduction](#introduction)
* [Common Error Types](#common-error-types)
    * [Syntax Errors](#syntax-errors)
    * [Type Mismatch Errors](#type-mismatch-errors)
    * [Undeclared/Unassigned Variable Errors](#undeclaredunassigned-variable-errors)
    * [Logical Errors (e.g., Infinite Loops)](#logical-errors-eg-infinite-loops)
    * [File System Errors](#file-system-errors)
    * [External Module Errors](#external-module-errors)

## Introduction

This document aims to help you understand and resolve common errors you might encounter while writing and running CMDScript programs. When an error occurs, the interpreter usually provides an error message along with the line number where the problem was detected. Pay close attention to these messages, as they are your primary guide to debugging.

## Common Error Types

### Syntax Errors

These errors occur when the script's structure or command usage does not follow the rules of CMDScript.

* **Error Message Examples:**
    * `Bad variable declaration (Ln X)`: Indicates an issue with how you've declared a variable alias or its name.
    * `Bad msg syntax (Ln X)`: The `msg` command was not formatted correctly (e.g., missing `%title` or `%subtitle`).
    * `Bad %while syntax (Ln X)`: The `%while` loop condition is malformed or incomplete.
    * `Unknown command (Ln X)`: The interpreter does not recognize the command on that line. This could be a typo, an unsupported command, or incorrect usage.

* **Possible Causes:**
    * Typographical errors in command names or keywords.
    * Incorrect spacing or missing required arguments.
    * Misplaced quotes or special characters.
    * Incorrect indentation for code blocks (functions, `if`/`else`, `while`).

* **Common Fixes:**
    * **Double-check spelling:** Ensure all commands and keywords (`write`, `wait`, `%if`, `%var`, etc.) are spelled correctly.
    * **Review syntax rules:** Compare your line against the documented syntax for that command (see `README.MD`).
    * **Verify arguments:** Make sure all required arguments are present and in the correct order.
    * **Check indentation:** For blocks like `%f`, `%if`, `%else`, and `%while`, ensure that the lines within the block are consistently indented (using spaces or tabs, but not a mix) and that the indentation is correct relative to the block start.

### Type Mismatch Errors

These errors occur when you try to use data in a way that is incompatible with its declared type.

* **Error Message Examples:**
    * `Type mismatch assigning to variable '<varname>' (Ln X)`: You attempted to assign a value of one type (e.g., a string) to a variable declared as another type (e.g., an integer).
    * `Input type mismatch for icq (Ln X)`: The user's input to an `%icq` command did not match the expected type you specified (e.g., user entered "hello" when `%int` was expected).
    * `Cannot perform arithmetic on non-numeric values: 'val1' and 'val2' (Ln X)`: You attempted to perform an arithmetic operation (e.g., `+`, `-`) on values that cannot be converted to numbers.

* **Possible Causes:**
    * Assigning `"5"` to an `%int` variable (it should be `5`).
    * Expecting a number from `%icq` but the user types text.
    * Trying to add a string and a number (e.g., `write "Hello" + 5`).

* **Common Fixes:**
    * **Match types:** Always ensure the value you're assigning or expecting matches the variable's declared type.
    * **Correct literal format:** Numbers should be written as numbers (e.g., `123`, `45.6`), and strings should be in quotes (e.g., `"text"`).
    * **Validate input:** When using `%icq`, inform the user about the expected input format in your prompt.
    * **Check arithmetic operands:** Ensure that both sides of an arithmetic operation resolve to numeric values.

### Undeclared/Unassigned Variable Errors

These errors relate to using variables that haven't been properly set up or given a value.

* **Error Message Examples:**
    * `Variable '<varname>' not declared (Ln X)`: You are trying to use a variable name that has not had its alias declared (e.g., `%int_alias = myVar`).
    * `Unknown variable '<varname>' (Ln X)`: Similar to "not declared," often a typo in the variable name when trying to use it.
    * `Variable '<varname>' has no value (Ln X)`: The variable has been declared and typed, but no value has been assigned to it using `<varname>%value = <value>`.

* **Possible Causes:**
    * Forgetting the `%alias` declaration at the top of the script.
    * Forgetting the type definition (e.g., `myVar = %int`).
    * Attempting to read a variable's value before assigning anything to it.
    * Typos when referencing a variable (`%var myVariable` vs. `%var myVaraible`).

* **Common Fixes:**
    * **Declare all variables:** Ensure every variable you intend to use has both an alias declaration and a type definition at the beginning of your script.
    * **Initialize variables:** Assign an initial value to variables using `<varname>%value = <value>` before you try to read or use their content.
    * **Check variable names:** Be consistent with spelling and capitalization when declaring and using variable names.

### Logical Errors (e.g., Infinite Loops)

These errors result in unexpected script behavior, often due to flawed logic rather than syntax issues.

* **Error Message Examples:**
    * `Infinite loop detected or exceeded 10000 iterations. (Ln X)`: Your `%while` loop's condition never becomes false, causing it to run indefinitely or hit the interpreter's safety limit.
    * `%if has too much depth (Ln X)` / `%while has too much depth (Ln X)`: You have too many nested `if` or `while` blocks, exceeding the interpreter's maximum nesting limit (currently 16 levels).

* **Possible Causes:**
    * **Infinite Loop:** The variable or condition controlling a `%while` loop is not updated correctly, or the condition is always true.
    * **Excessive Nesting:** Over-complex logic with too many levels of `if`/`else` or `while` statements inside one another.

* **Common Fixes:**
    * **Review loop conditions:** For `%while` loops, ensure that the condition will eventually become false. Check that variables involved in the condition are modified within the loop body.
    * **Simplify logic:** If you encounter depth errors, try to refactor your script to reduce nesting by using functions or breaking down complex conditional structures into simpler, sequential checks.

### File System Errors

These errors relate to problems accessing or finding script files.

* **Error Message Examples:**
    * `File not found: <path_to_script.cmdscript>`: The interpreter cannot locate the script file at the specified path.
    * `Invalid file extension. Only '.cmdscript' files are allowed.`: You tried to run a file that does not have the `.cmdscript` extension.

* **Possible Causes:**
    * Typo in the script file name or its path when running `python app.py ...`.
    * The script file is in a different directory than where you are running the `python` command.
    * Attempting to run a file with an incorrect or missing extension (e.g., `myscript.txt` instead of `myscript.cmdscript`).

* **Common Fixes:**
    * **Verify file path:** Ensure the file name and path you provide to `app.py` are correct and include the `.cmdscript` extension.
    * **Check current directory:** Make sure you are running the `python` command from the directory where your script file is located, or provide the full absolute path to the script.
    * **Correct extension:** Always save your CMDScript files with the `.cmdscript` extension.

### External Module Errors

These occur when a command relies on a Python package that isn't installed in your environment.

* **Error Message Examples:**
    * `[Notification skipped: No toast module installed]`: This message appears if you use the `msg` command without having either `win11toast` or `win10toast` installed. The script will continue to run, but the notification will not appear.

* **Possible Causes:**
    * The `win11toast` (for Windows 11) or `win10toast` (for Windows 10) Python package is not installed in your environment.

* **Common Fixes:**
    * Install the necessary package using pip:
        * For Windows 11: `pip install win11toast`
        * For Windows 10: `pip install win10toast`
