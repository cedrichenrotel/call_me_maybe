
def bracket_validator(s: str) -> bool:

    stock: list[str] = []
    ref: dict = {'}': '{'}

    if not s:
        return False

    for i in s:
        if i == '{':
            stock.append(i)
        elif i == '}':
            if not stock or stock[-1] != ref[i]:
                return False
    return len(stock) == 0
