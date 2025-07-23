import sys
import time
import argparse
import re
import ctypes

from win10toast import ToastNotifier

toaster = ToastNotifier()

# ANSI color codes
COLOR_CODES = {
    "%redtext": "\033[91m",
    "%greentext": "\033[92m",
    "%bluetext": "\033[94m",
    "%purpletext": "\033[95m",
    "%normal": "\033[0m",
}

variables = {}  # Store declared variables
functions = {}  # Store functions

def error(message):
    print(f"\n\033[91mError: {message}\033[0m\n")
    sys.exit(1)

def validate_variable_type(var_type, value):
    try:
        if var_type == "%int":
            int(value)
        elif var_type == "%dec":
            float(value)
        elif var_type in ["%txt", "%string"]:
            str(value)
        else:
            raise ValueError("Unknown type")
    except ValueError:
        return False
    return True

def parse_script(script_lines):
    parsed = []
    inside_function = False
    current_function = None

    for i, line in enumerate(script_lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("##"):
            continue

        if line.startswith("%f"):
            match = re.match(r"%f (.+):", line)
            if not match:
                error(f"Malformed function declaration (Ln {i+1})")
            inside_function = True
            current_function = match.group(1).strip()
            functions[current_function] = []
            continue

        if inside_function:
            if line:
                functions[current_function].append((i+1, line))
            continue

        parsed.append((i + 1, line))

    return parsed

def run_script(parsed_lines, input_value):
    global variables
    input_value = input_value.strip()
    
    for line_num, line in parsed_lines:
        if line.startswith("write"):
            parts = line.split()
            if len(parts) < 2:
                error(f"Syntax error in write (Ln {line_num})")

            output = ""
            expecting_string = False
            for part in parts[1:]:
                if part.startswith("\""):
                    if part.endswith("\"") and len(part) > 1:
                        output += part[1:-1] + " "
                        expecting_string = False
                    else:
                        output += part[1:] + " "
                        expecting_string = True
                elif part.endswith("\""):
                    if not expecting_string:
                        error(f"Unexpected text after quoted string in write (Ln {line_num})")
                    output += part[:-1] + " "
                    expecting_string = False
                elif part in COLOR_CODES:
                    output += COLOR_CODES[part]
                elif part == "%1":
                    if expecting_string:
                        error(f"%1 isn't allowed inside quotes (Ln {line_num})")
                    output += input_value + " "
                elif part.startswith("%var"):
                    var_name = parts[parts.index(part)+1] if parts.index(part)+1 < len(parts) else ""
                    if var_name not in variables:
                        error(f"Unknown variable '{var_name}' (Ln {line_num})")
                    output += str(variables[var_name]['value']) + " "
                elif expecting_string:
                    output += part + " "
                else:
                    error(f"Extra text found floating without quotes (Ln {line_num})")

            print(output.strip() + COLOR_CODES["%normal"])

        elif line.startswith("send %NL%"):
            print()

        elif line.startswith("msg"):
            parts = line.split()
            title = ""
            subtitle = ""
            for i in range(len(parts)):
                if parts[i] == "%title":
                    title = input_value if parts[i+1] == "%1" else parts[i+1].strip('"')
                if parts[i] == "%subtitle":
                    subtitle = input_value if parts[i+1] == "%1" else parts[i+1].strip('"')
            toaster.show_toast(title, subtitle, duration=3)

        elif line.startswith("wait"):
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                time.sleep(int(parts[1]))
            else:
                error(f"Invalid wait syntax (Ln {line_num})")

        elif line.startswith("%newestvar"):
            match = re.match(r"%newestvar = (\w+)", line)
            if not match:
                error(f"Bad variable declaration (Ln {line_num})")
            var = match.group(1)
            variables[var] = {'type': None, 'value': None}

        elif re.match(r"\w+ = %\w+", line):
            varname, vartype = line.split("=")
            varname = varname.strip()
            vartype = vartype.strip()
            if varname not in variables:
                error(f"Variable '{varname}' not declared (Ln {line_num})")
            variables[varname]['type'] = vartype

        elif re.match(r"\w+%value = .+", line):
            match = re.match(r"(\w+)%value = (.+)", line)
            varname = match.group(1)
            value = match.group(2).strip()
            if varname not in variables:
                error(f"Variable '{varname}' not declared (Ln {line_num})")

            vartype = variables[varname]['type']
            if value == "%1":
                value = input_value

            if not validate_variable_type(vartype, value):
                error(f"Type mismatch assigning to variable '{varname}' (Ln {line_num})")

            variables[varname]['value'] = value

        elif line.startswith("%icq"):
            match = re.match(r"%icq \"(.+?)\" (%\w+)", line)
            if not match:
                error(f"Invalid icq syntax (Ln {line_num})")
            prompt, expected_type = match.groups()
            user_input = input(prompt + " ")
            if not validate_variable_type(expected_type, user_input):
                error(f"Input type mismatch for icq (Ln {line_num})")
            input_value = user_input

        elif line.startswith("einid cimidisiciriiipit"):
            print("\033[90m[Script End]\033[0m")
            break

        elif line in functions:
            run_script(functions[line], input_value)

        else:
            error(f"Unknown command (Ln {line_num}): {line}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CMDScript Interpreter")
    parser.add_argument("script", help="Path to the .cmdscript file")
    parser.add_argument("--input", help="Input value to use as %1", required=True)
    args = parser.parse_args()

    try:
        with open(args.script, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        error("Script file not found.")

    print(f"Running {args.script} with input: {args.input}\n\n")
    parsed_script = parse_script(lines)
    run_script(parsed_script, args.input)
