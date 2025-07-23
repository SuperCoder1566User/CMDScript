import sys
import time
import argparse
import re

try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    HAVE_TOAST = True
except ImportError:
    HAVE_TOAST = False

COLOR_CODES = {
    "%redtext": "\033[91m",
    "%greentext": "\033[92m",
    "%bluetext": "\033[94m",
    "%purpletext": "\033[95m",
    "%normal": "\033[0m",
}

variables = {}  # {varname: {"alias": alias, "type": type, "value": val}}
functions = {}  # {funcname: [ (line_num, line), ... ] }
current_function = None


def error(message, line_num=None):
    if line_num:
        print(f"\n❌ Error: {message} (Ln {line_num})\n")
    else:
        print(f"\n❌ Error: {message}\n")
    sys.exit(1)


def validate_variable_type(var_type, value):
    # Validate value matches type
    if var_type == "%int":
        try:
            int(value)
            return True
        except:
            return False
    elif var_type == "%dec":
        try:
            float(value)
            return True
        except:
            return False
    elif var_type in ["%txt", "%string"]:
        # For %string, accept any text including special chars
        return isinstance(value, str)
    return False


def parse_script(lines):
    global current_function
    parsed = []
    current_function = None
    inside_function = False

    for idx, line in enumerate(lines):
        ln = idx + 1
        line = line.rstrip("\n").rstrip("\r")

        stripped = line.strip()
        # Skip comments
        if stripped.startswith("##") or stripped.startswith("#") or stripped == "":
            continue

        # Function start
        mfunc = re.match(r"%f\s+(.+):", stripped)
        if mfunc:
            current_function = mfunc.group(1).strip()
            functions[current_function] = []
            inside_function = True
            continue

        # Function body lines must be indented by at least 1 space or tab
        if inside_function:
            if line.startswith(" ") or line.startswith("\t"):
                functions[current_function].append((ln, line.strip()))
                continue
            else:
                inside_function = False
                current_function = None

        parsed.append((ln, stripped))

    return parsed


def run_function(func_name, input_val):
    if func_name not in functions:
        error(f"Function '{func_name}' not found")
    for (ln, line) in functions[func_name]:
        execute_line(line, ln, input_val)


def execute_line(line, line_num, input_val):
    global variables

    # Comments are ignored
    if line.startswith("##") or line.startswith("#") or line.strip() == "":
        return

    # Variable declaration %alias = VarName
    mvar_alias = re.match(r"%(\w+)\s*=\s*(\w+)$", line)
    if mvar_alias:
        alias, varname = mvar_alias.groups()
        # Validate varname and alias are identifiers
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", alias) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", varname):
            error("Bad variable declaration", line_num)
        # Check not already declared
        if varname in variables:
            error(f"Variable '{varname}' already declared", line_num)
        variables[varname] = {"alias": alias, "type": None, "value": None}
        return

    # Variable type declaration VarName = %type
    mvar_type = re.match(r"(\w+)\s*=\s*(%int|%dec|%txt|%string)$", line)
    if mvar_type:
        varname, vartype = mvar_type.groups()
        if varname not in variables:
            error("Bad variable declaration", line_num)
        variables[varname]["type"] = vartype
        return

    # Variable value assignment VarName%value = something
    mvar_value = re.match(r"(\w+)%value\s*=\s*(.+)$", line)
    if mvar_value:
        varname, val = mvar_value.groups()
        if varname not in variables:
            error(f"Variable '{varname}' not declared", line_num)
        vartype = variables[varname]["type"]
        # Substitute %1 input if present
        if val.strip() == "%1":
            val = input_val
        # Validate type
        if not validate_variable_type(vartype, val):
            error(f"Type mismatch assigning to variable '{varname}'", line_num)
        # Store value as appropriate type
        if vartype == "%int":
            val = int(val)
        elif vartype == "%dec":
            val = float(val)
        else:
            val = str(val)
        variables[varname]["value"] = val
        return

    # Input Change Question %icq "Prompt" %type
    micq = re.match(r'%icq\s+"(.+)"\s+(%int|%dec|%txt|%string)', line)
    if micq:
        prompt, expected_type = micq.groups()
        user_input = input(prompt + " ")
        # Validate type
        if not validate_variable_type(expected_type, user_input):
            error(f"Input type mismatch for icq", line_num)
        # Update input_val for later %1 substitution
        input_val = user_input
        return input_val

    # Write command
    if line.startswith("write"):
        # The pattern: write [color] "text" %1 %var VarName "text" ...
        # We'll parse with regex that splits quotes and tokens preserving spaces
        # First verify no % inside quotes (not allowed)
        quote_parts = re.findall(r'"[^"]*"', line)
        for q in quote_parts:
            if "%" in q:
                error("%[anything] isn't allowed inside double quotes", line_num)

        # Tokenize (quotes and words)
        tokens = re.findall(r'\"[^\"]*\"|%var \w+|%[a-z]+|%1|[^ \t]+', line[6:].strip())
        output = ""
        i = 0
        expecting_float = False
        while i < len(tokens):
            t = tokens[i]
            if t.startswith('"') and t.endswith('"'):
                output += t[1:-1]
            elif t in COLOR_CODES:
                output += COLOR_CODES[t]
            elif t == "%1":
                output += str(input_val)
            elif t.startswith("%var"):
                parts = t.split()
                if len(parts) != 2:
                    error("Bad %var usage", line_num)
                vname = parts[1]
                if vname not in variables:
                    error(f"Unknown variable '{vname}'", line_num)
                val = variables[vname]["value"]
                if val is None:
                    error(f"Variable '{vname}' has no value", line_num)
                output += str(val)
            else:
                # If any token is outside quotes and not recognized, error
                # Only allow tokens inside quotes or known tokens (%1, %var, colors)
                error("Extra text found floating without quotes", line_num)
            i += 1
        print(output + COLOR_CODES["%normal"])
        return input_val

    # send %NL%
    if line.startswith("send") and "%NL%" in line:
        print()
        return input_val

    # msg %title "title" %subtitle "subtitle"
    if line.startswith("msg"):
        if not HAVE_TOAST:
            print("[Notification skipped: win10toast not installed]")
            return input_val
        mt = re.findall(r'%title\s+("[^"]*"|%1)\s+%subtitle\s+("[^"]*"|%1)', line)
        if not mt:
            error("Bad msg syntax", line_num)
        title, subtitle = mt[0]
        # Replace %1 in title/subtitle with input_val if used
        if title == "%1":
            title = str(input_val)
        else:
            title = title.strip('"')
        if subtitle == "%1":
            subtitle = str(input_val)
        else:
            subtitle = subtitle.strip('"')
        toaster.show_toast(title, subtitle, duration=5)
        return input_val

    # wait seconds
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

    # Function call? If line matches a function name, call it
    if line in functions:
        run_function(line, input_val)
        return input_val

    # End line code (final encoded line)
    if re.match(r"einid cimidisiciriiipit", line):
        sys.exit(0)

    # Unknown command
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

    parsed_lines = parse_script(lines)

    input_val = args.input
    for line_num, line in parsed_lines:
        new_input = execute_line(line, line_num, input_val)
        if new_input is not None:
            input_val = new_input

    # Run a "Main" function if it exists
    if "Main" in functions:
        run_function("Main", input_val)

    print("\n✔️ Script finished.")


if __name__ == "__main__":
    main()
