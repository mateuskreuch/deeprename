from pathlib import Path
from replacer import CaseAwareReplacer, FileIsBinaryError
from rich import print
from rich_differ import rich_diff
from rich.live import Live
from rich.table import Table
import os, sys

replacer = None

def get_all_paths_to_replace(path: Path):
    file_objects: list[Path] = []

    for root_str, dir_names, file_names in os.walk(path):
        dir_names[:] = [d for d in dir_names if not d.startswith('.')]
        root_path = Path(root_str)
        file_objects += [root_path / f for f in file_names if not f.startswith('.')] \
                      + [root_path / d for d in dir_names]

    # Sort in a way so that no conflicts occur
    file_objects.sort(key=lambda x: (len(x.parts), len(x.name) * replacer.len_difference()), reverse=True)

    return file_objects

def main(root_dir: Path):
    table = Table()

    table.add_column("Type")
    table.add_column("Path")
    table.add_column("Errors")

    with Live(table, auto_refresh=False) as live:
        for old_path in get_all_paths_to_replace(root_dir):
            new_path = replacer.replace_path(old_path)
            relative_old_path = old_path.relative_to(root_dir)
            relative_new_path = new_path.relative_to(root_dir)
            type_text = ""
            errors = []

            try:
                replacer.replace_file_contents(old_path)
                type_text = "[yellow]File[/]"

            except IsADirectoryError:
                type_text = "[bright_black]Directory[/]"

            except FileIsBinaryError:
                type_text = "[bright_black]File (binary)[/]"

            except AssertionError as e:
                type_text = "[bright_black]File[/]"

                if str(e):
                    errors.append(str(e))

            try:
                replacer.rename_file(old_path)

            except FileExistsError as e:
                errors.append(f"{relative_new_path} (conflict)")

            except OSError as e:
                errors.append(f"OS failed")

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

    replacer = CaseAwareReplacer(old_str, new_str)

    main(Path(os.getcwd()))