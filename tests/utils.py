import random
import tempfile
import os

# Gives a random path in /tmp to create a random file (wiki) etc.
def get_tmp_path():
    dir = tempfile.gettempdir()
    file = random.randint(100_000, 999_999)
    return os.path.join(dir, str(file))
