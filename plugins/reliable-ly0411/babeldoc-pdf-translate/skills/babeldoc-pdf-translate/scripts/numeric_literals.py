"""Conservative signed numeric tokens shared by translation and repair guards.

Only the Unicode mathematical minus is a spelling alias for ASCII minus.
Decimal/group separators, signs, precision and exponent spelling remain exact;
this performs no arithmetic, rounding or identifier-number exemption.
"""
import re

TOKEN=re.compile(r'[+\-\u2212]?\d+(?:[.,]\d+)*(?:[eE][+\-\u2212]?\d+)?')

def tokens(text):
    return [match[0].replace('\u2212','-') for match in TOKEN.finditer(text)]
