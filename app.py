import sys
import time
import argparse
import re

try:
    from win11toast import toast
    HAVE_TOAST = True
except ImportError:
    HAVE_TOAST = False

# Color codes for terminal output
COLOR_CODES = {
    "%redtext": "\033[91m",
    "%greentext": "\033[92m",
    "%bluetext": "\033[94m",
    "%purpletext": "\033[95m",
    "%normal": "\033[0m",
}

# Global dictionaries to hold variables and functions
variables = {}  # varname -> dict {alias, type, value}
functions = {}  # funcname -> list of (line_num, line_text)
current_function = None  # Tracks currently parsing function

def error(message, line_num=None):
    """Print error message and exit."""
    if line_num:
        print(f"\n\u274c Error: {message} (Ln {line_num})\n")
    else:
        print(f"\n\u274c Error: {message}\n")
    sys.exit(1)

def validate_variable_type(var_type, value):
    """Validate that value matches var_type."""
    try:
        if var_type == "%int":
            int(value)
        elif var_type == "%dec":
            float(value)
        elif var_type in ["%txt", "%string"]:
            # Accept any string
            return True
        else:
            return False
        return True
    except Exception:
        return False

def parse_script(lines):
    """
    Parse script lines into main lines and functions.
    Function lines are grouped under functions dict.
    """
    global current_function
    parsed = []
    current_function = None
    inside_function = False

    for idx, line in enumerate(lines):
        ln = idx + 1
        raw_line = line.rstrip("\n").rstrip("\r")
        stripped = raw_line.strip()

        # Skip empty and comment lines
        if stripped == "" or stripped.startswith("##") or stripped.startswith("#"):
            continue

        # Detect function start line
        mfunc = re.match(r"%f\s+(.+):", stripped)
        if mfunc:
            current_function = mfunc.group(1).strip()
            functions[current_function] = []
            inside_function = True
            continue

        # Function body lines must be indented
        if inside_function:
            if raw_line.startswith(" ") or raw_line.startswith("\t"):
                # Strip leading whitespace for consistency
                functions[current_function].append((ln, stripped))
                continue
            else:
                # End function block
                inside_function = False
                current_function = None

        # Normal main script line
        parsed.append((ln, stripped))

    return parsed

def run_function(func_name, input_val):
    """Run a function by executing each line in it."""
    if func_name not in functions:
        error(f"Function '{func_name}' not found")
    for ln, line in functions[func_name]:
        input_val = execute_line(line, ln, input_val)
    return input_val

def resolve_value(token, input_val, line_num):
    """
    Resolve a token which can be:
    - a literal string (with quotes stripped)
    - a %var variable name (return variable value)
    - %1 input substitution
    - variable name (return variable value)
    """
    if isinstance(token, str):
        token = token.strip()
        # %var varname
        if token.startswith("%var"):
            parts = token.split()
            if len(parts) != 2:
                error("Bad %var usage", line_num)
            vname = parts[1]
            if vname not in variables:
                error(f"Unknown variable '{vname}'", line_num)
            val = variables[vname]["value"]
            if val is None:
                error(f"Variable '{vname}' has no value", line_num)
            return str(val)

        # %1 input substitution
        if token == "%1":
            return str(input_val)

        # Literal string with quotes
        if token.startswith('"') and token.endswith('"'):
            # Inside quotes, % is not allowed (enforced elsewhere)
            return token[1:-1]

        # Variable name itself
        if token in variables:
            val = variables[token]["value"]
            if val is None:
                error(f"Variable '{token}' has no value", line_num)
            return str(val)

        # Return as is (literal string)
        return token
    else:
        return str(token)

def evaluate_condition(lhs_token, operator, rhs_token, input_val, line_num):
    """
    Evaluate a condition for %if:
    lhs_token and rhs_token can be resolved values.
    Operators: =, X= (not equals), >, <, >=, <=
    """
    lhs_val = resolve_value(lhs_token, input_val, line_num)
    rhs_val = resolve_value(rhs_token, input_val, line_num)

    # Try to cast to numbers for numeric comparisons
    try:
        lhs_num = float(lhs_val)
        rhs_num = float(rhs_val)
        lhs_val = lhs_num
        rhs_val = rhs_num
    except Exception:
        pass  # keep as strings if conversion fails

    if operator == "=":
        return lhs_val == rhs_val
    elif operator == "X=":
        return lhs_val != rhs_val
    elif operator == ">":
        return lhs_val > rhs_val
    elif operator == "<":
        return lhs_val < rhs_val
    elif operator == ">=":
        return lhs_val >= rhs_val
    elif operator == "<=":
        return lhs_val <= rhs_val
    else:
        error(f"Unknown operator '{operator}' in condition", line_num)

def get_indent_level(line):
    """
    Count leading spaces/tabs for indentation level.
    Tabs count as 4 spaces.
    """
    count = 0
    for ch in line:
        if ch == " ":
            count += 1
        elif ch == "\t":
            count += 4
        else:
            break
    return count

def find_block(lines, start_index):
    """
    Given lines list and start index,
    find end of block of indented lines (until dedent or empty line).
    """
    total = len(lines)
    if start_index >= total:
        return start_index
    _, first_line = lines[start_index]
    indent = get_indent_level(first_line)
    i = start_index
    while i < total:
        _, line = lines[i]
        if line.strip() == "":
            break
        if get_indent_level(line) < indent:
            break
        i += 1
    return i

def execute_if_else(lines, start_idx, input_val, depth=0):
    """
    Executes nested %if/%else blocks starting at start_idx.
    Returns index after the block and updated input_val.
    Limits nesting depth to 16.
    """

    if depth >= 16:
        line_num, _ = lines[start_idx]
        error("%if has too much depth", line_num)

    idx = start_idx
    total = len(lines)
    executed = False  # To track if an if condition has been executed (to skip else blocks)

    while idx < total:
        line_num, line = lines[idx]

        # Match if or else
        m_if = re.match(r"%if\s+(.+?)\s+(=|X=|>|<|>=|<=)\s+(.+)", line)
        m_else = re.match(r"%else$", line)

        if m_if:
            # If we already executed a block before, skip this one
            if executed:
                # Skip this if block and all nested inside it
                block_start = idx + 1
                block_end = find_block(lines, block_start)
                idx = block_end
                continue

            lhs, op, rhs = m_if.groups()
            cond = evaluate_condition(lhs.strip(), op.strip(), rhs.strip(), input_val, line_num)

            # Find block after this %if
            block_start = idx + 1
            block_end = find_block(lines, block_start)

            if cond:
                # Execute block lines recursively handling nested if/else with depth + 1
                i = block_start
                while i < block_end:
                    ln, blk_line = lines[i]
                    if blk_line.startswith("%if") or blk_line == "%else":
                        i, input_val = execute_if_else(lines, i, input_val, depth + 1)
                    else:
                        input_val = execute_line(blk_line, ln, input_val)
                        i += 1
                executed = True
                idx = block_end
            else:
                # Skip block
                idx = block_end
            continue

        elif m_else:
            # If already executed if-block, skip else block
            if executed:
                # Skip else block lines
                block_start = idx + 1
                block_end = find_block(lines, block_start)
                idx = block_end
            else:
                # Execute else block lines recursively with depth + 1
                block_start = idx + 1
                block_end = find_block(lines, block_start)
                i = block_start
                while i < block_end:
                    ln, blk_line = lines[i]
                    if blk_line.startswith("%if") or blk_line == "%else":
                        i, input_val = execute_if_else(lines, i, input_val, depth + 1)
                    else:
                        input_val = execute_line(blk_line, ln, input_val)
                        i += 1
                executed = True
                idx = block_end
            continue

        else:
            # Not an if/else, end the if-else processing
            break

    return idx, input_val

def execute_line(line, line_num, input_val):
    """
    Main command executor.
    Handles variable declarations, assignments, if/else, write, send, msg, wait, functions, and exit command.
    """

    global variables

    # Skip comments or blank lines
    if line.startswith("##") or line.startswith("#") or line.strip() == "":
        return input_val

    # Handle variable alias declaration: %alias = varname
    mvar_alias = re.match(r"%(\w+)\s*=\s*(\w+)$", line)
    if mvar_alias:
        alias, varname = mvar_alias.groups()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", varname):
            error("Bad variable declaration", line_num)
        if varname in variables:
            error(f"Variable '{varname}' already declared", line_num)
        variables[varname] = {"alias": alias, "type": None, "value": None}
        return input_val

    # Handle variable type declaration: varname = %int|%dec|%txt|%string
    mvar_type = re.match(r"(\w+)\s*=\s*(%int|%dec|%txt|%string)$", line)
    if mvar_type:
        varname, vartype = mvar_type.groups()
        if varname not in variables:
            error("Bad variable declaration", line_num)
        variables[varname]["type"] = vartype
        return input_val

    # Handle variable value assignment: varname%value = value
    mvar_value = re.match(r"(\w+)%value\s*=\s*(.+)$", line)
    if mvar_value:
        varname, val = mvar_value.groups()
        if varname not in variables:
            error(f"Variable '{varname}' not declared", line_num)
        vartype = variables[varname]["type"]
        if val.strip() == "%1":
            val = input_val
        if not validate_variable_type(vartype, val):
            error(f"Type mismatch assigning to variable '{varname}'", line_num)
        if vartype == "%int":
            val = int(val)
        elif vartype == "%dec":
            val = float(val)
        else:
            val = str(val)
        variables[varname]["value"] = val
        return input_val

    # Handle input question: %icq "Prompt" %type
    micq = re.match(r'%icq\s+"(.+)"\s+(%int|%dec|%txt|%string)', line)
    if micq:
        prompt, expected_type = micq.groups()
        user_input = input(prompt + " ")
        if not validate_variable_type(expected_type, user_input):
            error(f"Input type mismatch for icq", line_num)
        return user_input

    # Handle if/else block starting with %if or %else (should be handled outside)
    if line.startswith("%if") or line == "%else":
        error("Direct %if or %else line execution not allowed, must be handled in block", line_num)

    # Handle write command
    if line.startswith("write"):
        quote_parts = re.findall(r'"[^"]*"', line)
        for q in quote_parts:
            if "%" in q:
                error("%[anything] isn't allowed inside double quotes", line_num)

        tokens = re.findall(r'"[^"]*"|%var \w+|%[a-z]+|%1|[^ \t]+', line[6:].strip())
        output = ""
        for t in tokens:
            t = t.strip()
            if t in COLOR_CODES:
                output += COLOR_CODES[t]
            else:
                output += resolve_value(t, input_val, line_num)
        print(output + COLOR_CODES["%normal"])
        return input_val

    # Handle send %NL% - outputs a blank line
    if line.startswith("send") and "%NL%" in line:
        print()
        return input_val

    # Handle msg command (desktop notifications) using win11toast
    if line.startswith("msg"):
        if not HAVE_TOAST:
            print("[Notification skipped: win11toast not installed]")
            return input_val
        # Parse: msg %title "Title" %subtitle "Subtitle" - allow %var varname or %1 for each
        mt = re.findall(r'%title\s+("[^"]*"|%1|%var \w+)\s+%subtitle\s+("[^"]*"|%1|%var \w+)', line)
        if not mt:
            error("Bad msg syntax", line_num)
        title, subtitle = mt[0]
        title_val = resolve_value(title, input_val, line_num)
        subtitle_val = resolve_value(subtitle, input_val, line_num)

        toast(title=title_val, msg=subtitle_val, duration=5)
        return input_val

    # Handle wait command: wait seconds
    if line.startswith("wait"):
        parts = line.split()
        if len(parts) != 2:
            error("Bad wait syntax", line_num)
        try:
            t = float(parts[1])
            time.sleep(t)
        except:
            error("Invalid wait time", line_num)
        return input_val

    # Handle function calls (lines matching function names)
    if line in functions:
        input_val = run_function(line, input_val)
        return input_val

    # Handle end of script command (encoded)
    if re.match(r"einid cimidisiciriiipit", line):
        sys.exit(0)

    error(f"Unknown command", line_num)

def main():
    parser = argparse.ArgumentParser(description="CMDScript Interpreter")
    parser.add_argument("script", help="Path to .cmdscript file")
    parser.add_argument("--input", help="Input to substitute as %1", default="")
    args = parser.parse_args()

    try:
        with open(args.script, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {args.script}")
        sys.exit(1)

    # Parse script lines into main lines and functions
    parsed_lines = parse_script(lines)

    # To process main lines, we must support %if/%else blocks spanning multiple lines
    i = 0
    input_val = args.input
    total = len(parsed_lines)

    while i < total:
        line_num, line = parsed_lines[i]

        # If line starts with %if or %else, handle block
        if line.startswith("%if") or line == "%else":
            i, input_val = execute_if_else(parsed_lines, i, input_val)
            continue
        else:
            # Regular line
            input_val = execute_line(line, line_num, input_val)
            i += 1

    # After main lines, run Main function if exists
    if "Main" in functions:
        input_val = run_function("Main", input_val)

    print("\n\u2714\ufe0f Script finished.")

if __name__ == "__main__":
    main()
