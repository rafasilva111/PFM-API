
import re
strings = ["1 frasco (540 g)", "1 frasco (420 g escorrido)", "600 g (3uni.)"]
pattern = r"(\d+)\s*g"


if '__main__':
    for string in strings:
        match = re.search(pattern, string)
        if match:
            value = match.group(1)
            print(f"{value} g")