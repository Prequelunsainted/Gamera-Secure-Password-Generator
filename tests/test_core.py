import math
import string
import tempfile
import unittest
from pathlib import Path

from gamera.__main__ import main
from gamera.core import (
    AMBIGUOUS,
    SYMBOLS,
    GenerationError,
    PassphraseOptions,
    PasswordOptions,
    evaluate_strength,
    format_duration,
    generate_passphrase,
    generate_password,
    passphrase_entropy,
    password_entropy,
)
from gamera.settings import Settings
from gamera.wordlist import WORDS


class PasswordTests(unittest.TestCase):
    def test_length_is_respected(self):
        for length in (4, 16, 64, 128):
            self.assertEqual(len(generate_password(PasswordOptions(length=length))), length)

    def test_every_selected_group_appears(self):
        # Repetido para pegar o caso em que o sorteio "esquece" um grupo.
        for _ in range(300):
            pw = generate_password(PasswordOptions(length=4))
            self.assertTrue(any(c in string.ascii_uppercase for c in pw))
            self.assertTrue(any(c in string.ascii_lowercase for c in pw))
            self.assertTrue(any(c in string.digits for c in pw))
            self.assertTrue(any(c in SYMBOLS for c in pw))

    def test_only_selected_groups(self):
        pw = generate_password(
            PasswordOptions(length=200 // 2, uppercase=False, symbols=False)
        )
        self.assertTrue(set(pw) <= set(string.ascii_lowercase + string.digits))

    def test_exclusions(self):
        opts = PasswordOptions(length=100, exclude_ambiguous=True, exclude_chars="abc!")
        for _ in range(50):
            pw = generate_password(opts)
            self.assertFalse(set(pw) & AMBIGUOUS)
            self.assertFalse(set(pw) & set("abc!"))

    def test_invalid_options(self):
        with self.assertRaises(GenerationError):
            generate_password(
                PasswordOptions(uppercase=False, lowercase=False, digits=False, symbols=False)
            )
        with self.assertRaises(GenerationError):
            generate_password(PasswordOptions(length=2))
        with self.assertRaises(GenerationError):
            generate_password(PasswordOptions(digits=False, uppercase=False, symbols=False,
                                              exclude_chars=string.ascii_lowercase))

    def test_passwords_differ(self):
        self.assertEqual(len({generate_password(PasswordOptions()) for _ in range(200)}), 200)

    def test_entropy(self):
        opts = PasswordOptions(length=10, uppercase=False, lowercase=False, symbols=False)
        self.assertAlmostEqual(password_entropy(opts), 10 * math.log2(10))


class PassphraseTests(unittest.TestCase):
    def test_wordlist(self):
        self.assertGreaterEqual(len(WORDS), 500)
        self.assertEqual(len(WORDS), len(set(WORDS)))
        self.assertTrue(all(w.isascii() and w.isalpha() and w.islower() for w in WORDS))

    def test_shape(self):
        opts = PassphraseOptions(words=6, separator=".", capitalize=True, include_number=True)
        phrase = generate_passphrase(opts)
        parts = phrase.split(".")
        self.assertEqual(len(parts), 6)
        self.assertTrue(all(p[0].isupper() for p in parts))
        self.assertEqual(sum(c.isdigit() for c in phrase), 1)

    def test_plain(self):
        phrase = generate_passphrase(PassphraseOptions(words=4, separator=" ", capitalize=False,
                                                       include_number=False))
        self.assertTrue(all(w in WORDS for w in phrase.split(" ")))

    def test_invalid(self):
        with self.assertRaises(GenerationError):
            generate_passphrase(PassphraseOptions(words=1))

    def test_entropy(self):
        opts = PassphraseOptions(words=5, include_number=False)
        self.assertAlmostEqual(passphrase_entropy(opts), 5 * math.log2(len(WORDS)))


class StrengthTests(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(evaluate_strength(20).level, 0)
        self.assertEqual(evaluate_strength(70).level, 2)
        self.assertEqual(evaluate_strength(200).level, 4)
        self.assertEqual(evaluate_strength(5000).level, 4)  # não estoura

    def test_durations(self):
        self.assertEqual(format_duration(0.1), "instantâneo")
        self.assertEqual(format_duration(1), "1 segundo")
        self.assertEqual(format_duration(3 * 86400), "3 dias")
        self.assertEqual(format_duration(1e20), "bilhões de anos")


class SettingsTests(unittest.TestCase):
    def test_roundtrip_and_bad_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "settings.json"
            self.assertEqual(Settings.load(path), Settings())
            Settings(length=42, mode="Frase-senha").save(path)
            self.assertEqual(Settings.load(path).length, 42)
            path.write_text('{"length": "muito", "words": 7}', encoding="utf-8")
            loaded = Settings.load(path)
            self.assertEqual((loaded.length, loaded.words), (16, 7))
            path.write_text("não é json", encoding="utf-8")
            self.assertEqual(Settings.load(path), Settings())


class CliTests(unittest.TestCase):
    def test_cli_runs(self):
        self.assertEqual(main(["--cli", "-n", "2", "-l", "20"]), 0)
        self.assertEqual(main(["-p", "-w", "4"]), 0)

    def test_cli_error(self):
        self.assertEqual(main(["--no-upper", "--no-lower", "--no-digits", "--no-symbols"]), 2)


if __name__ == "__main__":
    unittest.main()
