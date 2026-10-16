"""Gera o executável do Windows em ``dist/Gamera.exe``.

Uso:
    pip install -r requirements.txt pyinstaller
    python build_exe.py
"""

from __future__ import annotations

import os
from pathlib import Path

import PyInstaller.__main__

from gamera import __version__
from gamera.assets import icon_image

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"


def make_icon() -> Path:
    BUILD.mkdir(exist_ok=True)
    path = BUILD / "gamera.ico"
    icon_image("#8B5CF6", size=256).save(
        path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    return path


def main() -> None:
    icon = make_icon()
    PyInstaller.__main__.run(
        [
            str(ROOT / "password_generator.py"),
            "--name=Gamera",
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            f"--icon={icon}",
            f"--add-data={ROOT / 'gamera' / 'assets' / 'gamera.png'}{os.pathsep}gamera/assets",
            "--collect-data=customtkinter",
            f"--distpath={ROOT / 'dist'}",
            f"--workpath={BUILD}",
            f"--specpath={BUILD}",
        ]
    )
    print(f"\nGamera {__version__} pronto em {ROOT / 'dist' / 'Gamera.exe'}")


if __name__ == "__main__":
    main()
