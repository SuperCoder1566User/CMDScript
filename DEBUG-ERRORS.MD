# CMDScript Debugging & Common Errors
## Comprehensive Troubleshooting & Technical Reference

---

## 1. Introduction
This document is the primary resource for debugging CMDScript programs. When an error occurs, the `app.py` interpreter provides an error message and a line number (e.g., `Ln 42`). Pay close attention to these, as they point to where the interpreter's logic failed to parse your intent.

---

## 2. The Golden Rules of Development
Before troubleshooting specific code lines, verify these environment requirements:

1. **File Extension**: Your script must end in `.cmdscript` or `.cscript`.  
2. **Indentation**: CMDScript uses indentation to define blocks. Use either **4 spaces or 1 tab consistently**—never mix them.  
3. **The Lifecycle**: Variables must follow this path:

```
Declare (%newestvar) → Define Type (Name = %type) → Assign (Name%value = X)
```

---

## 3. Syntax Error Dictionary

### 3.1 `Unknown command: [text] (Ln X)`

**Description**  
The interpreter found a line that isn't a command, assignment, or function call.

**Common Causes**
- Typing `print` instead of `write`
- Typing `cls` instead of `%cls`
- Forgetting the colon `:` in `%f FunctionName:`
- Stray characters at the end of a line

**Fix**
Verify the spelling against `README.md` and remove trailing spaces.

---

### 3.2 `Bad variable declaration (Ln X)`

**Description**  
The syntax for `%newestvar = Name` is malformed.

**Common Causes**
- Missing the `=` sign
- Missing the `%` prefix

**Fix**
Ensure the line follows exactly:

```
%newestvar = YourVariableName
```

---

### 3.3 `Bad msg syntax (Ln X)`

**Description**  
The `msg` command is missing required parameters.

**Fix**
Every `msg` must include:

```
%title "Text" %subtitle "Text"
```

---

## 4. Type & Arithmetic Errors

### 4.1 `Type mismatch: [varname] is [type] (Ln X)`

**Description**
A value was assigned that does not match the variable's defined type.

**Examples**
- Assigning `"Apple"` to `%int`
- Assigning `7.5` to `%int`

**Fix**
Ensure the value matches the declared type, or change the variable type.

---

### 4.2 `Division by zero (Ln X)`

**Description**
A mathematical operation attempted to divide by `0`.

**Fix**
Check the divisor before performing division.

---

## 5. Logical & Block Errors

### 5.1 `Max recursion depth reached (Ln X)`

**Description**
The interpreter has reached its limit for nested blocks (usually 16 levels).

**Cause**
A function calling itself indefinitely or excessive nested `%if` statements.

**Fix**
Simplify the logic or split code into separate functions.

---

### 5.2 `Infinite loop detected (Ln X)`

**Description**
A `%while` loop exceeded **10,000 iterations**.

**Fix**
Ensure the loop condition eventually becomes false.

---

## 6. System & External Module Errors

### 6.1 `[Notification skipped: No toast module installed]`

**Description**
The `msg` command was used but the required Python library is missing.

**Fix**

Windows 11:
```
pip install win11toast
```

Windows 10:
```
pip install win10toast
```

---

## 7. Formatting & Display Pitfalls

### 7.1 "Bunching" Text

**Problem**
```
write "Hello" %var Name
```

Result:
```
HelloAldrich
```

**Fix**
Add a space inside the string:

```
write "Hello " %var Name
```

---

### 7.2 Missing Newlines

**Problem**
Multiple `write` commands appear on the same line.

**Fix**
Use:

```
send %NL%
```

---

*End of Debugging Guide*
