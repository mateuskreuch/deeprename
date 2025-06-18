from difflib import ndiff
from pathlib import Path
from rich import print
from rich.live import Live
from rich.table import Table
import os, re, sys

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

old_str = None
new_str = None

def case_preserving_rename(base_str: str):
    def replacer(match):
        original_match_value = match.group(0)
        replacement_value = []

        old_len = len(old_str)
        new_len = len(new_str)

        for i in range(min(old_len, new_len)):
            original_char = original_match_value[i]
            new_char_base = new_str[i]

            if original_char.isupper():
                replacement_value.append(new_char_base.upper())

            elif original_char.islower():
                replacement_value.append(new_char_base.lower())

            else:
                replacement_value.append(new_char_base)

        if new_len > old_len:
            replacement_value.append(new_str[old_len:])

        return "".join(replacement_value)

    old_str_re = re.compile(re.escape(old_str), re.IGNORECASE)

    if not old_str_re.search(base_str):
        return base_str

    return old_str_re.sub(replacer, base_str)

def is_binary(file_path: Path):
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk

    except IOError:
        return True

class FileIsBinaryError(Exception):
    pass

class PathIsDirectoryError(Exception):
    pass

def rename_in_file(file_path: Path):
    if not file_path.is_file():
        raise PathIsDirectoryError()

    if is_binary(file_path):
        raise FileIsBinaryError()

    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise AssertionError("File size exceeds maximum limit")

    content = file_path.read_text(encoding='utf-8')
    new_content = case_preserving_rename(content)

    if content == new_content:
        raise AssertionError()

    file_path.write_text(new_content, encoding='utf-8')

def no_hidden_flat_walk(path: Path):
    file_objects: list[Path] = []

    for root_str, dir_names, file_names in os.walk(path):
        dir_names[:] = [d for d in dir_names if not d.startswith('.')]
        root_path = Path(root_str)
        file_objects += [root_path / f for f in file_names if not f.startswith('.')] + \
                        [root_path / d for d in dir_names]

    # Sort in a way so that no conflicts occur
    file_objects.sort(key=lambda x: (len(x.parts), len(x.name) * (len(new_str) - len(old_str))), reverse=True)

    return file_objects

def rich_diff(old: str, new: str):
    if old == new:
        return str(old)

    diff = list(ndiff(str(old), str(new)))
    result = []

    for d in diff:
        code = d[0]
        char = d[2]

        if code == ' ':
            result.append(char)

        elif code == '-':
            result.append(f"[red]{char}[/red]")

        elif code == '+':
            result.append(f"[green]{char}[/green]")

    return "".join(result)

def main(root_dir: Path):
    table = Table()

    table.add_column("Type")
    table.add_column("Path")
    table.add_column("Errors")

    with Live(table, auto_refresh=False) as live:
        for old_path in no_hidden_flat_walk(root_dir):
            new_path = old_path.parent / case_preserving_rename(old_path.name)
            relative_old_path = old_path.relative_to(root_dir)
            relative_new_path = new_path.relative_to(root_dir)
            type_text = ""
            errors = []

            try:
                rename_in_file(old_path)
                type_text = "[yellow]File[/]"

            except PathIsDirectoryError:
                type_text = "[bright_black]Directory[/]"

            except FileIsBinaryError:
                type_text = "[bright_black]File (binary)[/]"

            except AssertionError as e:
                type_text = "[bright_black]File[/]"

                if str(e):
                    errors.append(str(e))

            if old_path != new_path:
                if new_path.exists():
                    errors.append(f"{relative_new_path} (conflict)")

                else:
                    try:
                        os.rename(old_path, new_path)

                    except OSError as e:
                        errors.append("OS failed")

            table.add_row(type_text, rich_diff(relative_old_path, relative_new_path), "[red]" + "; ".join(errors) + "[/]")
            live.update(table)

if __name__ == "__main__":
    arguments = sys.argv[1:]

    if "--help" in arguments or len(arguments) != 2:
        print("[bold]Usage:[/]\n"
              "  drename old new\n\n"
              "[bold]Options:[/]\n"
              "  --help           Show this help message\n")
        sys.exit(0)

    old_str = arguments[0]
    new_str = arguments[1]

    if old_str == new_str:
        print("[red]Old and new are the same. No actions will be taken.[/]")
        sys.exit(1)

    main(Path(os.getcwd()))