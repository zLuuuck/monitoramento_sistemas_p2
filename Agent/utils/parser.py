# utils/parser.py
def parse_key_value(text, separator=":"):
    data = {}

    for line in text.splitlines():
        if separator in line:
            key, value = line.split(separator, 1)
            data[key.strip()] = value.strip()

    return data