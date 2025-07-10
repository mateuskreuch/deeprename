import os
from pathlib import Path
import re, functools, itertools

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
RE_BOUNDARIES = r'([_-]+|(?<=[a-z0-9])(?=[A-Z]))'

@functools.cache
def matchcase(a, b):
    if a.isupper():
        return b.upper()
    elif a[0].isupper():
        return b[0].upper() + b[1:] # Keep as inputted
    else:
        return b[0].lower() + b[1:] # Keep as inputted

def safe_get(lst, i):
    return lst[min(i, len(lst) - 1)]

def is_binary(file_path: Path):
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk

    except IOError:
        return True

class FileIsBinaryError(Exception):
    pass

class CaseAwareReplacer:
    def __init__(self, old_str, new_str, dry_run=False):
        self._replacements = {}
        self._delta = len(new_str) - len(old_str)
        self._old = old_str.split('/')
        self._new = new_str.split('/')
        self._dry_run = dry_run
        self._pattern = re.compile(RE_BOUNDARIES.join([f"({x})" for x in self._old]), re.IGNORECASE)

    def get_replacements_made(self):
        return self._replacements

    def iter_replace_paths(self, paths: list[Path]):
        def sort_by_length(path: Path):
            return (len(path.parts), len(path.name) * self._delta)

        for old_path in sorted(paths, key=sort_by_length, reverse=True):
            yield old_path, self.replace_path(old_path)

    def replace(self, base_str: str):
        def replacer(match):
            parts = match.groups()
            old_str = ''.join(parts)
            separators = parts[1:len(self._new):2]
            parts = parts[0::2]
            # TODO: on numbers, match the case of the previous word, if first word, keep as inputted
            buffer = [matchcase(safe_get(parts, i), x) for i, x in enumerate(self._new)]

            if not separators:
               return ''.join(buffer)

            buffer = itertools.zip_longest(buffer, separators, fillvalue=separators[-1])
            buffer = itertools.chain.from_iterable(buffer)
            new_str = ''.join(list(buffer)[:-1])

            self._replacements[old_str] = new_str

            return new_str

        return self._pattern.sub(replacer, base_str)

    def replace_file_contents(self, file_path: Path):
        if not file_path.is_file():
            raise IsADirectoryError()

        if is_binary(file_path):
            raise FileIsBinaryError()

        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            raise AssertionError("File size exceeds maximum limit")

        content = file_path.read_text(encoding='utf-8')
        new_content = self.replace(content)

        if content == new_content:
            raise AssertionError()

        if not self._dry_run:
            file_path.write_text(new_content, encoding='utf-8')

    def replace_path(self, old_path: Path):
        return old_path.parent / self.replace(old_path.name)

    def rename_file(self, old_path: Path):
        new_path = self.replace_path(old_path)

        if old_path != new_path:
            if new_path.exists():
                raise FileExistsError(new_path)

            elif not self._dry_run:
                os.rename(old_path, new_path)