import {
  AMBIGUOUS,
  DEFAULT_PASSPHRASE,
  DEFAULT_PASSWORD,
  DIGITS,
  GenerationError,
  LOWERCASE,
  SYMBOLS,
  UPPERCASE,
  evaluateStrength,
  formatDuration,
  generatePassphrase,
  generatePassword,
  passphraseEntropy,
  passwordEntropy,
  randomInt,
} from "../core.js";
import { WORDS } from "../wordlist.js";
import { assert, equal, report, test, throws } from "./harness.js";

const has = (text, group) => [...text].some((c) => group.includes(c));
const opts = (extra = {}) => ({ ...DEFAULT_PASSWORD, ...extra });
const phrase = (extra = {}) => ({ ...DEFAULT_PASSPHRASE, ...extra });

test("randomInt respeita os limites e cobre todos os valores", () => {
  const seen = new Set();
  for (let i = 0; i < 2000; i++) {
    const n = randomInt(6);
    assert(n >= 0 && n < 6, `fora do intervalo: ${n}`);
    seen.add(n);
  }
  equal(seen.size, 6);
  equal(randomInt(1), 0);
});

test("randomInt é aproximadamente uniforme", () => {
  const counts = Array(10).fill(0);
  for (let i = 0; i < 20000; i++) counts[randomInt(10)]++;
  assert(counts.every((c) => c > 1700 && c < 2300), `distribuição torta: ${counts}`);
});

test("tamanho é respeitado", () => {
  for (const length of [4, 16, 64, 128]) equal(generatePassword(opts({ length })).length, length);
});

test("todo grupo selecionado aparece, mesmo com tamanho mínimo", () => {
  for (let i = 0; i < 300; i++) {
    const pw = generatePassword(opts({ length: 4 }));
    assert(has(pw, UPPERCASE) && has(pw, LOWERCASE) && has(pw, DIGITS) && has(pw, SYMBOLS), pw);
  }
});

test("só usa os grupos selecionados", () => {
  const pw = generatePassword(opts({ length: 100, uppercase: false, symbols: false }));
  assert([...pw].every((c) => (LOWERCASE + DIGITS).includes(c)), pw);
});

test("exclusões são respeitadas", () => {
  for (let i = 0; i < 50; i++) {
    const pw = generatePassword(opts({ length: 100, excludeAmbiguous: true, excludeChars: "abc!" }));
    assert(![...pw].some((c) => (AMBIGUOUS + "abc!").includes(c)), pw);
  }
});

test("opções inválidas lançam GenerationError", () => {
  throws(
    () => generatePassword(opts({ uppercase: false, lowercase: false, digits: false, symbols: false })),
    GenerationError,
  );
  throws(() => generatePassword(opts({ length: 2 })), GenerationError);
  throws(() => generatePassword(opts({ length: 500 })), GenerationError);
  throws(() => generatePassword(opts({ length: Number.NaN })), GenerationError);
  throws(
    () => generatePassword(opts({ uppercase: false, digits: false, symbols: false, excludeChars: LOWERCASE })),
    GenerationError,
  );
});

test("senhas geradas são diferentes entre si", () => {
  equal(new Set(Array.from({ length: 200 }, () => generatePassword(opts()))).size, 200);
});

test("entropia da senha", () => {
  const bits = passwordEntropy(opts({ length: 10, uppercase: false, lowercase: false, symbols: false }));
  assert(Math.abs(bits - 10 * Math.log2(10)) < 1e-9, String(bits));
  equal(passwordEntropy(opts({ uppercase: false, lowercase: false, digits: false, symbols: false })), 0);
});

test("lista de palavras é válida", () => {
  assert(WORDS.length >= 500, `só ${WORDS.length} palavras`);
  equal(new Set(WORDS).size, WORDS.length);
  assert(WORDS.every((w) => /^[a-z]+$/.test(w)), "palavra fora do padrão");
});

test("formato da frase-senha", () => {
  const text = generatePassphrase(phrase({ words: 6, separator: "." }));
  const parts = text.split(".");
  equal(parts.length, 6);
  assert(parts.every((p) => /^[A-Z]/.test(p)), text);
  equal([...text].filter((c) => DIGITS.includes(c)).length, 1);
});

test("frase-senha simples só usa palavras da lista", () => {
  const text = generatePassphrase(phrase({ words: 4, separator: " ", capitalize: false, includeNumber: false }));
  assert(text.split(" ").every((w) => WORDS.includes(w)), text);
});

test("frase-senha com quantidade inválida", () => {
  throws(() => generatePassphrase(phrase({ words: 1 })), GenerationError);
  throws(() => generatePassphrase(phrase({ words: 99 })), GenerationError);
});

test("entropia da frase-senha", () => {
  const bits = passphraseEntropy(phrase({ words: 5, includeNumber: false }));
  assert(Math.abs(bits - 5 * Math.log2(WORDS.length)) < 1e-9, String(bits));
});

test("níveis de força", () => {
  equal(evaluateStrength(20).level, 0);
  equal(evaluateStrength(70).level, 2);
  equal(evaluateStrength(200).level, 4);
  equal(evaluateStrength(5000).level, 4);
});

test("duração legível (igual ao desktop)", () => {
  equal(formatDuration(0.1), "instantâneo");
  equal(formatDuration(1), "1 segundo");
  equal(formatDuration(3 * 86400), "3 dias");
  equal(formatDuration(1e20), "bilhões de anos");
});

test("mesmos resultados de força que o app desktop", () => {
  // Valores conferidos com gamera/core.py (16 caracteres, 4 grupos = 104 bits).
  const bits = passwordEntropy(opts());
  assert(Math.round(bits) === 104, String(bits));
  equal(evaluateStrength(bits).label, "Forte");
});

export const outcome = report();
