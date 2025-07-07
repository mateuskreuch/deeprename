import re, functools, itertools

RE_BOUNDARIES = r'([_-]+|(?<=[a-z0-9])(?=[A-Z]))'

@functools.cache
def matchcase(a, b):
   if a.isupper():
      return b.upper()
   elif a.islower():
      return b[0].lower() + b[1:] # Keep as inputted
   else:
      return b[0].upper() + b[1:] # Keep as inputted

def safe_get(lst, i):
   return lst[min(i, len(lst) - 1)]

class CaseAwareReplacer:
    def __init__(self, old_str, new_str):
        self._old = old_str.split('/')
        self._new = new_str.split('/')
        self._pattern = re.compile(RE_BOUNDARIES.join([f"{x}" for x in self._old]), re.IGNORECASE)

    def part_difference(self):
       return len(self._new) - len(self._old)

    def replace(self, base_str: str):
        def replacer(match):
            parts = re.split(RE_BOUNDARIES, match.group(0))
            separators = parts[1:len(self._new):2]
            parts = parts[0::2]
            buffer = [matchcase(safe_get(parts, i), x) for i, x in enumerate(self._new)]

            if not separators:
               return ''.join(buffer)

            buffer = itertools.zip_longest(buffer, separators, fillvalue=separators[-1])
            buffer = itertools.chain.from_iterable(buffer)

            return ''.join(list(buffer)[:-1])

        return self._pattern.sub(replacer, base_str)