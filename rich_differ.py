from difflib import ndiff


DIFF_COLORS = {
    '-': 'red',
    '+': 'green'
}

def rich_diff(old: str, new: str):
    if old == new:
        return str(old)

    diff = list(ndiff(str(old), str(new)))
    last_code = " "
    result = []

    for d in diff:
        code = d[0]
        char = d[2]

        if last_code != code:
            if last_code in DIFF_COLORS:
                result.append(f"[/]")

            if code in DIFF_COLORS:
                result.append(f"[{DIFF_COLORS[code]}]")

        result.append(char)

        last_code = code

    if last_code in DIFF_COLORS:
        result.append(f"[/]")

    return "".join(result)