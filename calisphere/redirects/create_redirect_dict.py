import os
from sys import getsizeof

def get_redirects():
    redirects = {}
    with open(os.path.join(os.path.dirname(__file__), 'off_csphere.txt')) as f:
        for line in f:
            line = line.strip()

            if line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) == 2:
                redirects[parts[0]] = parts[1]
            elif len(parts) == 1:
                redirects[parts[0]] = ''
    
    with open(os.path.join(os.path.dirname(__file__), 'csphere_ids.txt')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) == 2:
                redirects[f"item/{parts[0]}"] = parts[1]
            elif len(parts) == 1:
                redirects[parts[0]] = ''

    print(
        f"Size of redirects: {getsizeof(redirects)} bytes"
        f" ({round(getsizeof(redirects) / 1024, 2)} KB)"
        f" ({round(getsizeof(redirects) / 1024 / 1024, 2)} MB)"
    )
    return redirects
