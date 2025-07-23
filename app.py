import os
import sys
import time
import ctypes
import platform

class CmdScriptError(Exception):
    pass

class InputQuotationError(Exception):
    pass

def is_end_line(line):
    line = line.strip()
    return "ii" in line

def send_windows_notification(title, subtitle):
    if platform.system() != "Windows":
        print(f"(Notification) {title}: {subtitle}")
        return

    MB_OK = 0x0
    MB_ICONINFORMATION = 0x40
    ctypes.windll.user32.MessageBoxW(0, subtitle, title, MB_OK | MB_ICONINFORMATION)

def print_colored_text(color_code, text):
    colors = {
        '%redtext': '\033[31m',
        '%greentext': '\033[32m',
        '%bluetext': '\033[34m',
        '%purpletext': '\033[35m',
    }
    reset = '\033[0m'
    color = colors.get(color_code.lower(), '')
    print(f"{color}{text}{reset}", end='')

def run_cmdscript(file_path, input_text):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    skip_next = False

    for i, line in enumerate(lines, start=1):
        line = line.rstrip('\n')
        if skip_next:
            skip_next = False
            continue

        stripped = line.strip()

        if stripped.startswith('##'):
            skip_next = True
            continue

        if stripped.startswith('#'):
            continue

        if not stripped:
            continue

        if is_end_line(stripped):
            break

        if stripped == "send %NL%":
            print()
            continue

        if stripped.startswith('wait '):
            parts = stripped.split()
            if len(parts) != 2:
                raise CmdScriptError(f'Invalid wait command format (Ln {i})')
            try:
                secs = float(parts[1])
                time.sleep(secs)
                continue
            except ValueError:
                raise CmdScriptError(f'Invalid number for wait command (Ln {i})')

        if stripped.startswith('msg '):
            import re
            pattern = r'msg\s+%title\s+"([^"]+)"\s+%Subtitle\s+"([^"]+)"'
            m = re.match(pattern, stripped, re.IGNORECASE)
            if not m:
                raise CmdScriptError(f'Invalid msg syntax (Ln {i})')
            title = m.group(1)
            subtitle = m.group(2)
            send_windows_notification(title, subtitle)
            continue

        if stripped.startswith('write '):
            content = stripped[6:].strip()

            color_codes = ['%redtext', '%greentext', '%bluetext', '%purpletext']
            color_code = None
            for code in color_codes:
                if content.lower().startswith(code):
                    color_code = code
                    content = content[len(code):].strip()
                    break

            # Now expect: quoted string, optionally followed by %1 only (no extra floating text)
            if not content.startswith('"'):
                raise CmdScriptError(f'write statement must start with quoted string (Ln {i})')

            end_quote_idx = content.find('"', 1)
            if end_quote_idx == -1:
                raise CmdScriptError(f'Missing closing quote in write statement (Ln {i})')

            quoted_text = content[1:end_quote_idx]

            # Check that quoted_text does NOT contain % (so no %1 inside quotes)
            if '%' in quoted_text:
                raise CmdScriptError(f'%[...] syntax is not allowed inside quotes (Ln {i})')

            after_quote = content[end_quote_idx+1:].strip()

            # after_quote can be empty OR exactly "%1"
            if after_quote == "":
                # just print quoted text
                final_text = quoted_text
            elif after_quote == "%1":
                final_text = quoted_text + " " + input_text
            else:
                # Extra floating text detected
                raise CmdScriptError(f'Extra text found floating without quotes (Ln {i})')

            if color_code:
                print_colored_text(color_code, final_text)
            else:
                print(final_text, end='')

            continue

        print(f"Warning: unrecognized command: {line}")

def find_first_cmdscript_file():
    files = [f for f in os.listdir('.') if f.endswith('.cmdscript')]
    if not files:
        print("No .cmdscript files found in current directory.")
        return None
    files.sort()
    return files[0]

def parse_args():
    filename = None
    input_text = ""

    args = sys.argv[1:]
    if not args:
        filename = find_first_cmdscript_file()
    else:
        if args[0].endswith('.cmdscript'):
            filename = args[0]
            args = args[1:]
        else:
            filename = find_first_cmdscript_file()

    if '--input' in args:
        idx = args.index('--input')
        input_parts = []
        for val in args[idx + 1:]:
            if val.startswith('-'):
                break
            input_parts.append(val)

        joined = " ".join(input_parts)
        if (joined.count('"') % 2) != 0:
            raise InputQuotationError(
                'Input string quotes are not balanced. Did you forget to put quotes around your input?'
            )
        for part in input_parts:
            if part.count('"') == 1:
                raise InputQuotationError(
                    f'Input argument "{part}" has unmatched quote. Did you forget to quote your input properly?'
                )

        input_text = joined.replace('"', '')

    return filename, input_text

def main():
    try:
        filename, input_text = parse_args()

        if not filename:
            print("No .cmdscript file to run.")
            return

        print(f"Running {filename} with input: {input_text}\n")
        run_cmdscript(filename, input_text)
    except CmdScriptError as e:
        print(f"Error: {e}")
    except InputQuotationError as e:
        print(f"InputQuotationError: {e}")

if __name__ == "__main__":
    main()
