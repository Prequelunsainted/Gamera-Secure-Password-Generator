"""Preferências da interface salvas entre execuções.

Somente as opções ficam no disco — senhas geradas nunca são gravadas.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path


def settings_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "Gamera" / "settings.json"


@dataclass
class Settings:
    appearance: str = "Escuro"
    mode: str = "Senha"
    length: int = 16
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False
    exclude_chars: str = ""
    words: int = 6
    separator: str = "-"
    capitalize: bool = True
    include_number: bool = True

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or settings_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()

        defaults = cls()
        values = {}
        for f in fields(cls):
            value = data.get(f.name, getattr(defaults, f.name))
            # Ignora valores com tipo errado (arquivo editado à mão, versão antiga...).
            if type(value) is type(getattr(defaults, f.name)):
                values[f.name] = value
        settings = cls(**values)
        # Não reabre o app num estado em que nenhuma senha pode ser gerada.
        if not (settings.uppercase or settings.lowercase or settings.digits or settings.symbols):
            settings.uppercase = settings.lowercase = settings.digits = settings.symbols = True
        return settings

    def save(self, path: Path | None = None) -> None:
        path = path or settings_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # Preferências são conveniência; não vale derrubar o app por isso.
