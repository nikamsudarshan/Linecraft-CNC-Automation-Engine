import textwrap
import numpy as np
from collections import defaultdict

def wrap_text_block(text, max_chars_per_line=50):
    """
    Wraps text into lines that fit the specified width.
    """
    wrapper = textwrap.TextWrapper(
        width=max_chars_per_line,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False
    )

    # Handle existing newlines in the input
    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        wrapped = wrapper.wrap(line)
        if not wrapped: # Handle empty lines
            formatted_lines.append("")
        else:
            formatted_lines.extend(wrapped)

    return formatted_lines

# --- RNN HELPER (Keep this for later use) ---
alphabet = [
    '\x00', ' ', '!', '"', '#', "'", '(', ')', ',', '-', '.',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';',
    '?', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
    'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'Y',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
    'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
    'y', 'z'
]
alpha_to_num = defaultdict(int, list(map(reversed, enumerate(alphabet))))

def encode_ascii(ascii_string):
    return np.array(list(map(lambda x: alpha_to_num[x], ascii_string)) + [0])
