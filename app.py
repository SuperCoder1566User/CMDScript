import sys
import time
import argparse
import re
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


HAVE_TOAST = False
TOAST_MODULE = None

try:
    from win11toast import toast
    HAVE_TOAST = True
    TOAST_MODULE = toast
except ImportError:
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        HAVE_TOAST = True
        TOAST_MODULE = toaster.show_toast
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

clear_console()
print("HAVE_TOAST: ", HAVE_TOAST)

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
    """Run a function by executing each line in it, including handling %if/%else."""
    if func_name not in functions:
        error(f"Function '{func_name}' not found")

    func_lines = functions[func_name]
    i = 0
    total = len(func_lines)

    while i < total:
        line_num, line = func_lines[i]

        if line.startswith("%if") or line == "%else":
            i, input_val = execute_if_else(func_lines, i, input_val)
        elif line.startswith("%while"): # Added for while loops
            i, input_val = execute_while_loop(func_lines, i, input_val) # Added for while loops
        else:
            input_val = execute_line(line, line_num, input_val)
            i += 1

    return input_val

def resolve_value(token, input_val, line_num):
    """
    Resolve a token which can be:
    - a literal string (with quotes stripped)
    - a %var variable name (return variable value)
    - %1 input substitution
    - variable name (return variable value)
    - A simple expression (e.g., FavNumber + 1)
    """
    if isinstance(token, str):
        token = token.strip()
        
        # Priority 1: Literal string with quotes
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]

        # Priority 2: %1 input substitution
        if token == "%1":
            return str(input_val)

        # Priority 3: %var varname
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
            # FIX: Strip quotes from variable's stored string value if it has them
            if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            return str(val)

        # Priority 4: Variable name itself (not %var, just the name)
        if token in variables:
            val = variables[token]["value"]
            if val is None:
                error(f"Variable '{token}' has no value", line_num)
            # FIX: Strip quotes from variable's stored string value if it has them
            if isinstance(val, str) and val.startswith('"') and val.endswith('"'):
                return val[1:-1]
            return str(val)

        # Priority 5: Check for simple arithmetic expressions now that other types are handled
        m_expr = re.match(r"(.+?)\s*([+\-*/])\s*(.+)", token)
        if m_expr:
            op1_str, op, op2_str = m_expr.groups()
            
            # Recursively resolve operands
            op1_val = resolve_value(op1_str.strip(), input_val, line_num)
            op2_val = resolve_value(op2_str.strip(), input_val, line_num)

            try:
                # Try as float first for flexibility
                op1_num = float(op1_val)
                op2_num = float(op2_val)

                if op == "+": return str(op1_num + op2_num)
                elif op == "-": return str(op1_num - op2_num)
                elif op == "*": return str(op1_num * op2_num)
                elif op == "/": 
                    if op2_num == 0: error("Division by zero", line_num)
                    return str(op1_num / op2_num)
            except ValueError:
                error(f"Cannot perform arithmetic on non-numeric values: '{op1_str}' and '{op2_str}'", line_num)
            
            return token # Should not be reached for valid expressions.

        # Priority 6: Return as is (literal string or number that didn't match other patterns)
        return token
    else:
        return str(token)

def evaluate_condition(lhs_token, operator, rhs_token, input_val, line_num):
    """
    Evaluate a condition for %if or %while:
    lhs_token and rhs_token can be resolved values.
    Operators: =, X= (not equals), >, <, >=, <= (numeric/string exact/not-exact)
               ~ (string contains, case-sensitive)
               ~= (string contains, case-insensitive)
    """
    lhs_val = resolve_value(lhs_token, input_val, line_num)
    rhs_val = resolve_value(rhs_token, input_val, line_num)

    # Attempt numeric comparison first
    try:
        lhs_num = float(lhs_val)
        rhs_num = float(rhs_val)
        
        if operator == "=": return lhs_num == rhs_num
        elif operator == "X=": return lhs_num != rhs_num
        elif operator == ">": return lhs_num > rhs_num
        elif operator == "<": return lhs_num < rhs_num
        elif operator == ">=": return lhs_num >= rhs_num
        elif operator == "<=": return lhs_num <= rhs_num
        # For numeric, '~' and '~=' are not valid
        elif operator == "~" or operator == "~=":
            error(f"Invalid operator '{operator}' for numeric comparison.", line_num)
        else:
            error(f"Unknown numeric operator '{operator}' in condition", line_num)
    except ValueError:
        # If not numeric, perform string comparison
        if operator == "=": # Exact match, case-sensitive
            return lhs_val == rhs_val
        elif operator == "X=": # Not exact match, case-sensitive
            return lhs_val != rhs_val
        elif operator == "~": # Contains, case-sensitive
            return rhs_val in lhs_val
        elif operator == "~=": # Contains, case-insensitive
            return rhs_val.lower() in lhs_val.lower()
        elif operator in [">", "<", ">=", "<="]:
             error(f"Invalid operator '{operator}' for string comparison. Use '=' or 'X=' or '~' or '~='.", line_num)
        else:
            error(f"Unknown string operator '{operator}' in condition", line_num)

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
    i = start_index # Start checking from the current line's indentation level
    while i < total:
        _, line = lines[i]
        if line.strip() == "": # Empty line breaks block
            break
        if get_indent_level(line) < indent and i > start_index: # Dedented line breaks block, but not if it's the very first line
            break
        i += 1
    return i # Returns the index of the first line *outside* the block


def execute_if_else(lines, start_idx, input_val, depth=0):
    """
    Executes an entire %if/%else if/%else chain starting at start_idx.
    Returns index after the entire chain and updated input_val.
    Limits nesting depth to 16.
    """
    if depth >= 16:
        line_num, _ = lines[start_idx]
        error("%if has too much depth", line_num)

    idx = start_idx
    total = len(lines)
    executed_a_branch_in_this_chain = False

    # Loop through the current if/else chain at the same indentation level
    initial_indent = get_indent_level(lines[start_idx][1])

    while idx < total:
        line_num, line_text = lines[idx]
        stripped_line = line_text.strip()

        # Check for lines that end the conditional chain (dedented or empty)
        if stripped_line == "" or (get_indent_level(line_text) < initial_indent and idx > start_idx):
            break

        m_if = re.match(r"%if\s+(.+?)\s+(=|X=|>|<|>=|<=|~|~=)\s+(.+)", stripped_line)
        m_else = re.match(r"%else$", stripped_line)

        if m_if:
            # If a branch has already executed in this chain, skip this %if
            if executed_a_branch_in_this_chain:
                block_start_after_if_line = idx + 1
                block_end = find_block(lines, block_start_after_if_line)
                idx = block_end # Move index past this %if's block
                continue
            
            # Evaluate condition
            lhs, op, rhs = m_if.groups()
            cond = evaluate_condition(lhs.strip(), op.strip(), rhs.strip(), input_val, line_num)

            block_start_after_if_line = idx + 1
            block_end = find_block(lines, block_start_after_if_line)

            if cond:
                # Execute the lines within this %if block
                current_block_idx = block_start_after_if_line
                while current_block_idx < block_end:
                    ln, blk_line = lines[current_block_idx]
                    if blk_line.startswith("%if") or blk_line == "%else":
                        current_block_idx, input_val = execute_if_else(lines, current_block_idx, input_val, depth + 1)
                    elif blk_line.startswith("%while"): # Added for while loops
                        current_block_idx, input_val = execute_while_loop(lines, current_block_idx, input_val, depth + 1) # Added for while loops
                    else:
                        input_val = execute_line(blk_line, ln, input_val)
                        current_block_idx += 1
                executed_a_branch_in_this_chain = True # Mark that a branch has executed
                idx = block_end # Move index past this %if's block
            else:
                # Condition is false, skip this %if block
                idx = block_end # Move index past this %if's block
            continue # Continue to next line in the outer while loop (could be %else or end of chain)

        elif m_else:
            # If a branch has already executed in this chain, skip this %else
            if executed_a_branch_in_this_chain:
                block_start_after_else_line = idx + 1
                block_end = find_block(lines, block_start_after_else_line)
                idx = block_end # Move index past this %else's block
            else:
                # No branch executed yet, so execute this %else block
                block_start_after_else_line = idx + 1
                block_end = find_block(lines, block_start_after_else_line)
                current_block_idx = block_start_after_else_line
                while current_block_idx < block_end:
                    ln, blk_line = lines[current_block_idx]
                    if blk_line.startswith("%if") or blk_line == "%else":
                        current_block_idx, input_val = execute_if_else(lines, current_block_idx, input_val, depth + 1)
                    elif blk_line.startswith("%while"): # Added for while loops
                        current_block_idx, input_val = execute_while_loop(lines, current_block_idx, input_val, depth + 1) # Added for while loops
                    else:
                        input_val = execute_line(blk_line, ln, input_val)
                        current_block_idx += 1
                executed_a_branch_in_this_chain = True # Mark that a branch has executed
                idx = block_end # Move index past this %else's block
            continue # Continue to next line in the outer while loop (end of chain)
        else:
            # This line is not an %if or %else at the same level, so the chain ends
            break

    return idx, input_val

def execute_while_loop(lines, start_idx, input_val, depth=0):
    """
    Executes a %while loop starting at start_idx.
    Returns index after the entire loop block and updated input_val.
    Limits nesting depth to 16.
    """
    if depth >= 16:
        line_num, _ = lines[start_idx]
        error("%while has too much depth", line_num)

    line_num, line_text = lines[start_idx]
    stripped_line = line_text.strip()
    # Updated regex to include new string operators for while loop condition
    m_while = re.match(r"%while\s+(.+?)\s+(=|X=|>|<|>=|<=|~|~=)\s+(.+)", stripped_line) 
    if not m_while:
        error("Bad %while syntax", line_num)

    lhs_cond, op_cond, rhs_cond = m_while.groups()

    block_start = start_idx + 1
    block_end = find_block(lines, block_start)
    
    loop_count = 0
    MAX_LOOP_ITERATIONS = 10000 # Safety break for very long/infinite loops

    while True:
        loop_count += 1
        if loop_count > MAX_LOOP_ITERATIONS:
            error(f"Infinite loop detected or exceeded {MAX_LOOP_ITERATIONS} iterations.", line_num)

        # Re-evaluate condition at each iteration
        cond_result = evaluate_condition(lhs_cond, op_cond, rhs_cond, input_val, line_num)

        if not cond_result:
            break # Condition is false, exit loop

        # Execute the block lines
        current_block_idx = block_start
        while current_block_idx < block_end:
            ln, blk_line = lines[current_block_idx]
            # Handle nested conditionals or loops within the while block
            if blk_line.startswith("%if") or blk_line == "%else":
                current_block_idx, input_val = execute_if_else(lines, current_block_idx, input_val, depth + 1)
            elif blk_line.startswith("%while"):
                current_block_idx, input_val = execute_while_loop(lines, current_block_idx, input_val, depth + 1)
            else:
                input_val = execute_line(blk_line, ln, input_val)
                current_block_idx += 1
        # After executing the block, the loop condition will be re-evaluated
    
    return block_end, input_val # Return index after the loop block


def execute_line(line, line_num, input_val):
    """
    Main command executor.
    Handles variable declarations, assignments, if/else, write, send, msg, wait, functions, and exit command.
    """

    global variables

    # Skip comments or blank lines (already handled in parse_script and find_block but good for safety)
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
        varname, val_str = mvar_value.groups() # Renamed 'val' to 'val_str' for clarity
        if varname not in variables:
            error(f"Variable '{varname}' not declared", line_num)
        vartype = variables[varname]["type"]

        # Resolve the value string before validation/assignment
        # This will correctly handle %1, %var, and literal strings (stripping quotes)
        val = resolve_value(val_str, input_val, line_num)

        if not validate_variable_type(vartype, val):
            error(f"Type mismatch assigning to variable '{varname}'", line_num)
        if vartype == "%int":
            val = int(val)
        elif vartype == "%dec":
            val = float(val)
        # For %txt/%string, val is already str from resolve_value
        
        variables[varname]["value"] = val
        return input_val

    # Handle input question: %icq "Prompt" %type
    micq = re.match(r'%icq\s+"(.+)"\s+(%int|%dec|%txt|%string)', line)
    if micq:
        prompt, expected_type = micq.groups()
        user_input = input(prompt + " ")
        if not validate_variable_type(expected_type, user_input):
            error(f"Input type mismatch for icq", line_num)
        return user_input # Return user_input to be used as %1

    # Handle if/else block starting with %if or %else (should be handled outside by execute_if_else)
    if line.startswith("%if") or line == "%else":
        error("Direct %if or %else line execution not allowed, must be handled in block", line_num)

    # Handle while loop block starting with %while (should be handled outside by execute_while_loop)
    if line.startswith("%while"):
        error("Direct %while line execution not allowed, must be handled in block", line_num)

    # Handle write command
    if line.startswith("write"):
        # Use a more robust regex to find quoted strings or individual tokens
        # Allows for spaces within quotes, and then separates other tokens
        tokens = re.findall(r'"[^"]*"|(?:\S+)', line[len("write"):].strip())
        
        output_parts = []
        for t in tokens:
            t = t.strip()
            if not t: continue # Skip empty strings from regex
            
            if t in COLOR_CODES:
                output_parts.append(COLOR_CODES[t])
            elif t == "%NL%":
                output_parts.append("\n")
            else: 
                # resolve_value will handle quoted strings, %var, %1, and literals
                output_parts.append(resolve_value(t, input_val, line_num))
        
        # Ensure the output resets to normal color at the end if not explicitly done
        if not output_parts or (output_parts and output_parts[-1] not in COLOR_CODES.values()):
             output_parts.append(COLOR_CODES["%normal"])

        print("".join(output_parts), end="") # Print all parts concatenated, no extra newline by default
        return input_val

    # Handle send %NL% - outputs a blank line
    if line.startswith("send") and "%NL%" in line:
        print()
        return input_val

    # Handle msg command (desktop notifications) using win11toast or win10toast
    if line.startswith("msg"):
        if not HAVE_TOAST:
            print("[Notification skipped: No toast module installed]")
            return input_val
        # Parse: msg %title "Title" %subtitle "Subtitle" - allow %var varname or %1 for each
        mt = re.findall(r'%title\s+("[^"]*"|%1|%var \w+)\s+%subtitle\s+("[^"]*"|%1|%var \w+)', line)
        if not mt:
            error("Bad msg syntax", line_num)
        title, subtitle = mt[0]
        title_val = resolve_value(title, input_val, line_num)
        subtitle_val = resolve_value(subtitle, input_val, line_num)

        # Call the appropriate toast function
        if 'win11toast' in sys.modules:
            TOAST_MODULE(title=title_val, msg=subtitle_val, duration=5)
        elif 'win10toast' in sys.modules:
            # win10toast's show_toast takes title, msg, then icon, duration
            TOAST_MODULE(title_val, subtitle_val, duration=5)
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

    # Handle clear_console command
    if line.startswith("clear_console"):
        parts = line.split(maxsplit=1) # Split into "clear_console" and the rest
        delay = 0.0 # Default to instant clear
        
        if len(parts) > 1: # If there's an argument
            delay_token = parts[1].strip()
            resolved_delay_val = resolve_value(delay_token, input_val, line_num)
            try:
                delay = float(resolved_delay_val)
            except ValueError:
                error(f"Invalid delay time for 'clear_console': '{delay_token}'", line_num)
        
        if delay > 0:
            time.sleep(delay)
        clear_console()
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

    # --- ADDED VALIDATION FOR .cmdscript EXTENSION ---
    if not args.script.endswith(".cmdscript"):
        error(f"Invalid file extension. Only '.cmdscript' files are allowed.")
    # --- END ADDITION ---

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
        # If line starts with %while, handle loop block
        elif line.startswith("%while"): # Added for while loops
            i, input_val = execute_while_loop(parsed_lines, i, input_val) # Added for while loops
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
