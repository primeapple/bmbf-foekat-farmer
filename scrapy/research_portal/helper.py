from typing import List

################ HELPERS ################
def replace_whitespace(string: str, replace_with: str = ' ', whitespace_chars: str = None) -> str:
    """Replaces all whitespace from string with replace_with (single space by default). By default every whitespace char is replaced, if you don't want this, please provide a sequence of whitespace chars like \n\t\r"""
    if whitespace_chars is None:
        return replace_with.join(string.split())
    else:
        return string.translate(str.maketrans('', '', whitespace_chars))