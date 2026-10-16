"""Ponto de entrada: ``python -m gamera`` abre a interface gráfica.

Com ``--cli`` (ou qualquer opção de geração) a senha é impressa no terminal,
sem abrir janela — útil em scripts.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import (
    MAX_LENGTH,
    MAX_WORDS,
    MIN_LENGTH,
    MIN_WORDS,
    GenerationError,
    PassphraseOptions,
    PasswordOptions,
    evaluate_strength,
    generate_passphrase,
    generate_password,
    passphrase_entropy,
    password_entropy,
)


def _bounded(low: int, high: int):
    def parse(value: str) -> int:
        number = int(value)
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"use um valor entre {low} e {high}")
        return number

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamera",
        description="Gamera — gerador de senhas seguras.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--cli", action="store_true", help="gera no terminal, sem abrir a janela")
    parser.add_argument("-n", "--count", type=_bounded(1, 100), default=1, help="quantas senhas gerar")
    parser.add_argument("-l", "--length", type=_bounded(MIN_LENGTH, MAX_LENGTH), default=16, help="tamanho da senha")
    parser.add_argument("--no-upper", action="store_true", help="sem letras maiúsculas")
    parser.add_argument("--no-lower", action="store_true", help="sem letras minúsculas")
    parser.add_argument("--no-digits", action="store_true", help="sem números")
    parser.add_argument("--no-symbols", action="store_true", help="sem símbolos")
    parser.add_argument("--no-ambiguous", action="store_true", help="evita caracteres parecidos (Il1O0)")
    parser.add_argument("--exclude", default="", metavar="CHARS", help="caracteres a nunca usar")
    parser.add_argument("-p", "--passphrase", action="store_true", help="gera uma frase-senha")
    parser.add_argument("-w", "--words", type=_bounded(MIN_WORDS, MAX_WORDS), default=6, help="palavras na frase-senha")
    parser.add_argument("--separator", default="-", help="separador entre as palavras")
    parser.add_argument("-s", "--stats", action="store_true", help="mostra entropia e força")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    try:
        if args.passphrase:
            opts = PassphraseOptions(words=args.words, separator=args.separator)
            bits = passphrase_entropy(opts)
            results = [generate_passphrase(opts) for _ in range(args.count)]
        else:
            opts = PasswordOptions(
                length=args.length,
                uppercase=not args.no_upper,
                lowercase=not args.no_lower,
                digits=not args.no_digits,
                symbols=not args.no_symbols,
                exclude_ambiguous=args.no_ambiguous,
                exclude_chars=args.exclude,
            )
            bits = password_entropy(opts)
            results = [generate_password(opts) for _ in range(args.count)]
    except GenerationError as error:
        print(f"erro: {error}", file=sys.stderr)
        return 2

    print("\n".join(results))
    if args.stats:
        strength = evaluate_strength(bits)
        print(
            f"\n{strength.label} · {bits:.0f} bits · tempo estimado para quebrar: {strength.crack_time}",
            file=sys.stderr,
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)

    # Qualquer opção de geração implica modo terminal.
    if args.cli or any(a.startswith("-") for a in argv):
        return run_cli(args)

    from .app import run_app

    run_app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
