// Lógica de geração — porta de gamera/core.py, sem dependência de interface.
// Usa crypto.getRandomValues (CSPRNG do navegador) com amostragem sem viés.

import { WORDS } from "./wordlist.js";

export const UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
export const LOWERCASE = "abcdefghijklmnopqrstuvwxyz";
export const DIGITS = "0123456789";
export const SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~";
export const AMBIGUOUS = "Il1|O0o`'\"";

export const MIN_LENGTH = 4;
export const MAX_LENGTH = 128;
export const MIN_WORDS = 3;
export const MAX_WORDS = 12;

// Atacante offline pessimista: 10 bilhões de tentativas por segundo.
const GUESSES_PER_SECOND = 1e10;

export class GenerationError extends Error {}

export const DEFAULT_PASSWORD = Object.freeze({
  length: 16,
  uppercase: true,
  lowercase: true,
  digits: true,
  symbols: true,
  excludeAmbiguous: false,
  excludeChars: "",
});

export const DEFAULT_PASSPHRASE = Object.freeze({
  words: 6,
  separator: "-",
  capitalize: true,
  includeNumber: true,
});

/** Inteiro uniforme em [0, max), sem viés de módulo. */
export function randomInt(max) {
  if (!Number.isInteger(max) || max < 1 || max > 0x100000000) {
    throw new RangeError("max deve estar entre 1 e 2^32");
  }
  const limit = Math.floor(0x100000000 / max) * max;
  const buffer = new Uint32Array(1);
  do {
    crypto.getRandomValues(buffer);
  } while (buffer[0] >= limit);
  return buffer[0] % max;
}

const pick = (items) => items[randomInt(items.length)];

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = randomInt(i + 1);
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

/** Grupos de caracteres ativos, já sem os caracteres excluídos. */
export function pools(options) {
  const excluded = new Set(options.excludeChars);
  if (options.excludeAmbiguous) for (const c of AMBIGUOUS) excluded.add(c);

  return [
    [options.uppercase, UPPERCASE],
    [options.lowercase, LOWERCASE],
    [options.digits, DIGITS],
    [options.symbols, SYMBOLS],
  ]
    .filter(([enabled]) => enabled)
    .map(([, chars]) => [...chars].filter((c) => !excluded.has(c)).join(""))
    .filter((pool) => pool.length > 0);
}

/** Senha com pelo menos um caractere de cada grupo selecionado. */
export function generatePassword(options) {
  if (!(options.length >= MIN_LENGTH && options.length <= MAX_LENGTH)) {
    throw new GenerationError(`O tamanho deve estar entre ${MIN_LENGTH} e ${MAX_LENGTH}.`);
  }
  const groups = pools(options);
  if (groups.length === 0) throw new GenerationError("Selecione ao menos um tipo de caractere.");
  if (options.length < groups.length) {
    throw new GenerationError(`O tamanho mínimo para ${groups.length} grupos é ${groups.length}.`);
  }

  const alphabet = [...groups.join("")];
  const chars = groups.map((group) => pick([...group]));
  while (chars.length < options.length) chars.push(pick(alphabet));
  return shuffle(chars).join("");
}

/** Frase-senha estilo Diceware. */
export function generatePassphrase(options, wordlist = WORDS) {
  if (!(options.words >= MIN_WORDS && options.words <= MAX_WORDS)) {
    throw new GenerationError(
      `A quantidade de palavras deve estar entre ${MIN_WORDS} e ${MAX_WORDS}.`,
    );
  }
  let words = Array.from({ length: options.words }, () => pick(wordlist));
  if (options.capitalize) words = words.map((w) => w[0].toUpperCase() + w.slice(1));
  if (options.includeNumber) words[randomInt(words.length)] += String(randomInt(10));
  return words.join(options.separator);
}

export function passwordEntropy(options) {
  const size = pools(options).reduce((total, pool) => total + pool.length, 0);
  return size <= 1 ? 0 : options.length * Math.log2(size);
}

export function passphraseEntropy(options, wordlist = WORDS) {
  let bits = options.words * Math.log2(wordlist.length);
  if (options.includeNumber) bits += Math.log2(10) + Math.log2(options.words);
  return bits;
}

const LEVELS = [
  [40, "Muito fraca"],
  [60, "Fraca"],
  [80, "Razoável"],
  [110, "Forte"],
  [Infinity, "Muito forte"],
];

export function evaluateStrength(bits) {
  const level = LEVELS.findIndex(([limit]) => bits < limit);
  const seconds = 2 ** Math.min(bits, 1023) / 2 / GUESSES_PER_SECOND;
  return { level, label: LEVELS[level][1], bits, crackTime: formatDuration(seconds) };
}

/** Intervalo em português legível ("3 dias", "séculos"). */
export function formatDuration(seconds) {
  if (seconds < 1) return "instantâneo";
  const units = [
    ["ano", "anos", 365.25 * 24 * 3600],
    ["dia", "dias", 24 * 3600],
    ["hora", "horas", 3600],
    ["minuto", "minutos", 60],
    ["segundo", "segundos", 1],
  ];
  for (const [singular, plural, size] of units) {
    if (seconds >= size) {
      const value = seconds / size;
      if (singular === "ano") {
        if (value >= 1e9) return "bilhões de anos";
        if (value >= 1e6) return "milhões de anos";
        if (value >= 1e3) return "milhares de anos";
        if (value >= 100) return "séculos";
      }
      const count = Math.floor(value);
      return `${count} ${count === 1 ? singular : plural}`;
    }
  }
  return "instantâneo";
}
