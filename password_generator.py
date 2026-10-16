"""Atalho mantido por compatibilidade: ``python password_generator.py``.

O código agora vive no pacote ``gamera``; prefira ``python -m gamera``.
"""

import sys

from gamera.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
