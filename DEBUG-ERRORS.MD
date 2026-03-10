# CMDScript Debugging & Common Errors
## Comprehensive Troubleshooting & Technical Reference

---

## 1. Introduction
This document is the primary resource for debugging CMDScript programs. When an error occurs, the `app.py` interpreter provides an error message and a line number (e.g., `Ln 42`). Pay close attention to these, as they point to where the interpreter's logic failed to parse your intent.

---

## 2. The Golden Rules of Development
Before troubleshooting specific code lines, verify these environment requirements:
1.  **File Extension**: Your script must end in `.cmdscript`. The interpreter will reject any other extension.
2.  **Indentation**: CMDScript uses indentation to define blocks. Use either 4 spaces or 1 tab consistently—never mix them.
3.  **The Lifecycle**: Variables must follow a strict path: `Declare (%newestvar)` -> `Define Type (Name = %type)` -> `Assign (Name%value = X)`.

---

## 3. Syntax Error Dictionary

### 3.1 `Unknown command: [text] (Ln X)`
* **Description**: The interpreter found a line that isn't a command, assignment, or function call.
* **Common Causes**:
    * Typing `print` instead of `write`.
    * Typing `cls` instead of `%cls`.
    * Forgetting the colon `:` at the end of `%f FunctionName:`.
    * Stray characters or invisible symbols at the end of a line.
* **Fix**: Verify the spelling against the `README.md` and check for trailing spaces.

### 3.2 `Bad variable declaration (Ln X)`
* **Description**: The syntax for `%newestvar = Name` is malformed.
* **Common Causes**: Missing the `=` sign or the `%` prefix.
* **Fix**: Ensure the line follows exactly: `%newestvar = YourVariableName`.

### 3.3 `Bad msg syntax (Ln X)`
* **Description**: The `msg` command is missing its structure.
* **Fix**: Every `msg` must include both `%title "Text"` and `%subtitle "Text"`.

---

## 4. Type & Arithmetic Errors

### 4.1 `Type mismatch: [varname] is [type] (Ln X)`
* **Description**: Attempting to assign data that does not match the variable's defined type.
* **Examples**:
    * Assigning `"Apple"` to a variable typed as `%int`.
    * Assigning a decimal like `7.5` to an `%int`.
* **Fix**: Ensure the value matches the type, or change the declaration to `%string` or `%dec`.

### 4.2 `Division by zero (Ln X)`
* **Description**: A mathematical operation tried to divide a number by `0`.
* **Fix**: Check your variables before dividing to ensure they aren't zero.

---

## 5. Logical & Block Errors

### 5.1 `Max recursion depth reached (Ln X)`
* **Description**: The interpreter has reached its limit for nested blocks (usually 16 levels).
* **Cause**: This is often caused by a function calling itself indefinitely or excessive nested `%if` statements.
* **Fix**: Simplify your logic or break complex code into separate functions.

### 5.2 `Infinite loop detected (Ln X)`
* **Description**: A `%while` loop has exceeded 10,000 iterations.
* **Fix**: Check the condition of your loop. Ensure the variable used in the condition is being updated inside the loop body.

---

## 6. System & External Module Errors

### 6.1 `[Notification skipped: No toast module installed]`
* **Description**: The `msg` command was used, but the necessary Python library is missing.
* **Fix**: 
    * For Windows 11: Run `pip install win11toast`.
    * For Windows 10: Run `pip install win10toast`.

---

## 7. Formatting & Display Pitfalls

### 7.1 "Bunching" Text
* **Problem**: `write "Hello" %var Name` results in `HelloAldrich`.
* **Fix**: Add manual spaces inside your quotes: `write "Hello " %var Name`.

### 7.2 Missing Newlines
* **Problem**: Multiple `write` commands all appear on the same line.
* **Fix**: Use the `send %NL%` command to force the console to the next line.

---
*End of Debugging Guide*
