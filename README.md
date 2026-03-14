# CMDScript Interpreter
## Technical Documentation & User Guide

---

## 1. Introduction
CMDScript is a lightweight, custom scripting language interpreter built in Python. It is designed for straightforward console automation, allowing users to manage data with typed variables, implement complex branching logic, and create reusable functions.

---

## 2. Language Features

### 2.1 Variables & Data Types
CMDScript uses a three-step process for memory management to ensure type safety.

**1. Declaration**: Use `%newestvar` to create a name.

```cmdscript
%newestvar = Score
```

**2. Typing**: Define the data type.

- `%int` – Whole numbers  
- `%dec` – Decimal numbers  
- `%string` / `%txt` – Text data  

```cmdscript
Score = %int
```

**3. Assignment & Arithmetic**: Use `%value` to store data. You can perform math directly during assignment.

```cmdscript
# Basic assignment
Score%value = 10

# Arithmetic assignment (Addition, Subtraction, Multiplication, Division)
Score%value = Score + 5
```

---

### 2.2 Input & Output

**User Input (`%icq`)** – Displays a prompt and stores the result in the `%1` buffer.

```cmdscript
%icq "Enter your name:" %string
PlayerName%value = %1
```

**Console Output (`write`)** – Displays text or variables.

```cmdscript
write %bluetext "Current Score: " %var Score
```

**Newlines** – Use `send %NL%` to move to the next line.

---

### 2.3 System Commands

**Clear Screen (`%cls`)** – Instantly clears the terminal window.

**Wait (`wait`)** – Pauses execution for a specified number of seconds.

**Notifications (`msg`)** – Sends a desktop toast notification. Requires `win11toast`.

---

## 3. Control Flow & Structure

### 3.1 File Requirements

Scripts must follow these structural rules:

1. **Extensions**: Files must end in `.cmdscript` or `.cscript`.
2. **Mandatory Footer**: Every script must end with either `end cmdscript` or `end script`.

---

### 3.2 Functions (`%f`)

Define reusable code blocks using indentation.

```cmdscript
%f Victory:
    write "You reached the end!"
    send %NL%
```

---

### 3.3 Conditionals (`%if / %else`)

Supports numeric and string comparisons.

```cmdscript
%if Score >= 15
    Victory
%else
    write "Keep playing..."
```

---

## 4. How to Run

**Execution**

```bash
python app.py your_script.cscript
```

---

*Generated for CMDScript Version 1.3*
