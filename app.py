import sys
import time
import argparse
import re
import os

def clear_console():
    # Clears the terminal screen based on OS [cite: 1]
    os.system('cls' if os.name == 'nt' else 'clear')

HAVE_TOAST = False
try:
    from win11toast import toast as toast_fn
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

variables = {} 
functions = {} 

def error(message, line_num=None):
    loc = f" (Ln {line_num})" if line_num else ""
    print(f"\n\033[91m\u274c Error: {message}{loc}\033[0m\n")
    sys.exit(1)

def resolve_value(token, input_val, line_num):
    token = token.strip()
    if not token: return ""
    
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        return token[1:-1]
    
    if token == "%1": return str(input_val)
    
    # Handle %var Name or %varName 
    if token.startswith("%var"):
        vname = token[4:].strip()
        if vname in variables:
            return str(variables[vname]["value"])
        error(f"Undefined variable: {vname}", line_num)

    if token in variables:
        return str(variables[token]["value"])

    return token

def evaluate_condition(line, input_val, line_num):
    # Prioritizes 2-char operators to prevent "7.5 > = 10" errors [cite: 3]
    match = re.match(r"%if\s+(.+?)\s*(>=|<=|X=|=|>|<)\s*(.+)", line)
    if not match: error("Invalid condition syntax", line_num)
    
    lhs, op, rhs = match.groups()
    v1 = resolve_value(lhs, input_val, line_num)
    v2 = resolve_value(rhs, input_val, line_num)

    try:
        n1, n2 = float(v1), float(v2)
        ops = {"=": n1==n2, "X=": n1!=n2, ">": n1>n2, "<": n1<n2, ">=": n1>=n2, "<=": n1<=n2}
        return ops[op]
    except ValueError:
        if op == "=": return str(v1) == str(v2)
        if op == "X=": return str(v1) != str(v2)
    
    error(f"Invalid comparison: {v1} {op} {v2}", line_num)

def get_indent(line):
    return len(line) - len(line.lstrip())

def execute_block(lines, start_idx, input_val):
    i = start_idx
    if i >= len(lines): return i, input_val
    base_indent = get_indent(lines[i][1])
    
    while i < len(lines):
        ln, content = lines[i]
        current_indent = get_indent(content)
        if not content.strip(): 
            i += 1
            continue
        if current_indent < base_indent: break

        stripped = content.strip()
        if stripped.startswith("%if"):
            i, input_val = handle_if_else(lines, i, input_val)
        else:
            input_val = execute_line(stripped, ln, input_val)
            i += 1
    return i, input_val

def handle_if_else(lines, idx, input_val):
    ln, content = lines[idx]
    condition_met = evaluate_condition(content.strip(), input_val, ln)
    
    if_start = idx + 1
    if_end = if_start
    if if_start < len(lines):
        target_indent = get_indent(lines[if_start][1])
        while if_end < len(lines) and (not lines[if_end][1].strip() or get_indent(lines[if_end][1]) >= target_indent):
            if_end += 1

    else_start = -1
    else_end = -1
    if if_end < len(lines) and lines[if_end][1].strip() == "%else":
        else_start = if_end + 1
        else_end = else_start
        if else_start < len(lines):
            target_indent = get_indent(lines[else_start][1])
            while else_end < len(lines) and (not lines[else_end][1].strip() or get_indent(lines[else_end][1]) >= target_indent):
                else_end += 1

    if condition_met:
        execute_block(lines, if_start, input_val)
    elif else_start != -1:
        execute_block(lines, else_start, input_val)

    return (else_end if else_end != -1 else if_end), input_val

def execute_line(line, line_num, input_val):
    global variables
    
    # 1. NEW: Clear Screen Command [cite: 1]
    if line == "%cls":
        clear_console()
        return input_val

    # 2. Assignment [cite: 1]
    m_val = re.match(r"(\w+)%value\s*=\s*(.+)", line)
    if m_val:
        vname, raw_val = m_val.groups()
        if vname not in variables: error(f"Variable '{vname}' not declared", line_num)
        final_val = resolve_value(raw_val, input_val, line_num)
        v_type = variables[vname]["type"]
        try:
            if v_type == "%int": variables[vname]["value"] = int(float(final_val))
            elif v_type == "%dec": variables[vname]["value"] = float(final_val)
            else: variables[vname]["value"] = str(final_val)
        except:
            variables[vname]["value"] = final_val
        return input_val

    # 3. Declarations [cite: 1, 2]
    if line.startswith("%newestvar"):
        vname = line.split("=")[1].strip()
        variables[vname] = {"type": None, "value": None}
        return input_val
    
    m_type = re.match(r"(\w+)\s*=\s*(%int|%dec|%txt|%string)", line)
    if m_type:
        vname, vtype = m_type.groups()
        if vname in variables: variables[vname]["type"] = vtype
        return input_val

    # 4. Input & Write [cite: 1, 2]
    if line.startswith("%icq"):
        prompt = re.search(r'"([^"]*)"', line).group(1)
        return input(prompt + " ")

    if line.startswith("write"):
        content = line[5:].strip()
        # Better tokenizing to separate %var and strings [cite: 3]
        tokens = re.findall(r'%var\s*\w+|"[^"]*"|\S+', content)
        for t in tokens:
            if t in COLOR_CODES: 
                print(COLOR_CODES[t], end="")
            else: 
                print(resolve_value(t, input_val, line_num), end=" ")
        print(COLOR_CODES["%normal"])
        return input_val

    if line == "send %NL%":
        print()
        return input_val

    if line.startswith("wait"):
        time.sleep(float(resolve_value(line.split()[1], input_val, line_num)))
        return input_val

    if line.startswith("msg"):
        if HAVE_TOAST:
            m = re.search(r'%title\s+"([^"]+)"\s+%subtitle\s+(.+)', line)
            if m:
                title, sub = m.groups()
                toast_fn(title, resolve_value(sub, input_val, line_num))
        return input_val

    if line in functions:
        execute_block(functions[line], 0, input_val)
        return input_val

    if line == "einid cimidisiciriiipit": sys.exit(0)
    return input_val

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script")
    args = parser.parse_args()

    with open(args.script, "r", encoding="utf-8") as f:
        lines = [(i+1, l.rstrip()) for i, l in enumerate(f.readlines()) if l.strip() and not l.strip().startswith("#")]

    main_body = []
    i = 0
    while i < len(lines):
        ln, content = lines[i]
        if content.strip().startswith("%f"):
            fname = content.strip()[2:].rstrip(":").strip()
            functions[fname] = []
            i += 1
            while i < len(lines) and (get_indent(lines[i][1]) > 0 or not lines[i][1].strip()):
                functions[fname].append(lines[i])
                i += 1
        else:
            main_body.append(lines[i])
            i += 1

    execute_block(main_body, 0, "")
    print("\n✔ Script finished.")

if __name__ == "__main__":
    main()
