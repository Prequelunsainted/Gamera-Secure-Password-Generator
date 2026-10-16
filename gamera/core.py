"""Lógica de geração de senhas — sem dependência de interface gráfica.

Tudo aqui usa o módulo ``secrets`` (CSPRNG do sistema operacional), então pode
ser reutilizado pela GUI, pela linha de comando e pelos testes.
"""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass, field

from .wordlist import WORDS

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~"
AMBIGUOUS = frozenset("Il1|O0o`'\"")

MIN_LENGTH = 4
MAX_LENGTH = 128
MIN_WORDS = 3
MAX_WORDS = 12

# Hipótese pessimista para o tempo de quebra: atacante offline com GPUs
# testando 10 bilhões de combinações por segundo contra um hash rápido.
GUESSES_PER_SECOND = 1e10

_rng = secrets.SystemRandom()


@dataclass(frozen=True)
class PasswordOptions:
    length: int = 16
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False
    exclude_chars: str = ""

    def pools(self) -> list[str]:
        """Grupos de caracteres ativos, já sem os caracteres excluídos."""
        excluded = set(self.exclude_chars)
        if self.exclude_ambiguous:
            excluded |= AMBIGUOUS

        selected = [
            (self.uppercase, UPPERCASE),
            (self.lowercase, LOWERCASE),
            (self.digits, DIGITS),
            (self.symbols, SYMBOLS),
        ]
        pools = []
        for enabled, chars in selected:
            if enabled:
                pool = "".join(c for c in chars if c not in excluded)
                if pool:
                    pools.append(pool)
        return pools


@dataclass(frozen=True)
class PassphraseOptions:
    words: int = 6
    separator: str = "-"
    capitalize: bool = True
    include_number: bool = True
    wordlist: tuple[str, ...] = field(default=WORDS, repr=False)


class GenerationError(ValueError):
    """Opções que não permitem gerar uma senha válida."""


def generate_password(options: PasswordOptions) -> str:
    """Gera uma senha com pelo menos um caractere de cada grupo selecionado."""
    if not MIN_LENGTH <= options.length <= MAX_LENGTH:
        raise GenerationError(
            f"O tamanho deve estar entre {MIN_LENGTH} e {MAX_LENGTH}."
        )

    pools = options.pools()
    if not pools:
        raise GenerationError("Selecione ao menos um tipo de caractere.")
    if options.length < len(pools):
        raise GenerationError(
            f"O tamanho mínimo para {len(pools)} grupos é {len(pools)}."
        )

    alphabet = "".join(pools)
    chars = [secrets.choice(pool) for pool in pools]
    chars += [secrets.choice(alphabet) for _ in range(options.length - len(chars))]
    _rng.shuffle(chars)
    return "".join(chars)


def generate_passphrase(options: PassphraseOptions) -> str:
    """Gera uma frase-senha no estilo Diceware (palavras aleatórias)."""
    if not MIN_WORDS <= options.words <= MAX_WORDS:
        raise GenerationError(
            f"A quantidade de palavras deve estar entre {MIN_WORDS} e {MAX_WORDS}."
        )

    words = [secrets.choice(options.wordlist) for _ in range(options.words)]
    if options.capitalize:
        words = [w.capitalize() for w in words]
    if options.include_number:
        index = secrets.randbelow(len(words))
        words[index] += str(secrets.randbelow(10))
    return options.separator.join(words)


def password_entropy(options: PasswordOptions) -> float:
    """Entropia aproximada (em bits) de uma senha gerada com essas opções."""
    alphabet_size = sum(len(pool) for pool in options.pools())
    if alphabet_size <= 1:
        return 0.0
    return options.length * math.log2(alphabet_size)


def passphrase_entropy(options: PassphraseOptions) -> float:
    """Entropia (em bits) de uma frase-senha gerada com essas opções."""
    bits = options.words * math.log2(len(options.wordlist))
    if options.include_number:
        bits += math.log2(10) + math.log2(options.words)
    return bits


@dataclass(frozen=True)
class Strength:
    level: int  # 0 (muito fraca) a 4 (muito forte)
    label: str
    bits: float
    crack_time: str


_LEVELS = (
    (40, "Muito fraca"),
    (60, "Fraca"),
    (80, "Razoável"),
    (110, "Forte"),
    (math.inf, "Muito forte"),
)


def evaluate_strength(bits: float) -> Strength:
    for level, (limit, label) in enumerate(_LEVELS):
        if bits < limit:
            break
    seconds = (2 ** min(bits, 1023)) / 2 / GUESSES_PER_SECOND
    return Strength(level, label, bits, format_duration(seconds))


def format_duration(seconds: float) -> str:
    """Formata um intervalo em português de forma legível ("3 dias", "séculos")."""
    if seconds < 1:
        return "instantâneo"
    units = (
        ("ano", "anos", 365.25 * 24 * 3600),
        ("dia", "dias", 24 * 3600),
        ("hora", "horas", 3600),
        ("minuto", "minutos", 60),
        ("segundo", "segundos", 1),
    )
    for singular, plural, size in units:
        if seconds >= size:
            value = seconds / size
            if singular == "ano":
                if value >= 1e9:
                    return "bilhões de anos"
                if value >= 1e6:
                    return "milhões de anos"
                if value >= 1e3:
                    return "milhares de anos"
                if value >= 100:
                    return "séculos"
            count = int(value)
            return f"{count} {singular if count == 1 else plural}"
    return "instantâneo"
