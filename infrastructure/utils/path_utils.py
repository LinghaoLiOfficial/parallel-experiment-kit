import random
import re
import string
import uuid
from pathlib import Path


def remove_specific_prefixes(value: str) -> str:
    pattern = r"^(\.\./|\./|/|\.\\|\\)"
    return re.sub(pattern, "", value)


class StrGenerator:
    @classmethod
    def safe_path_join(cls, *paths):
        return Path("/".join(remove_specific_prefixes(str(path)) for path in paths))

    @classmethod
    def generate_5_random_str(cls):
        characters = string.digits + string.ascii_uppercase
        return "".join(random.choice(characters) for _ in range(5))

    @classmethod
    def generate_uuid(cls):
        return str(uuid.uuid4())
