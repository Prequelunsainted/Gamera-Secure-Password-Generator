import {
  DEFAULT_PASSPHRASE,
  DEFAULT_PASSWORD,
  GenerationError,
  MAX_WORDS,
  MIN_LENGTH,
  MIN_WORDS,
  evaluateStrength,
  generatePassphrase,
  generatePassword,
  passphraseEntropy,
  passwordEntropy,
} from "./core.js";

const VERSION = "2.0.0";
const STORAGE_KEY = "gamera.settings.v1";
const MAX_UI_LENGTH = 64;
const HISTORY_LIMIT = 10;
const CLIPBOARD_TIMEOUT = 30; // segundos
const SEPARATORS = ["-", ".", "_", " "];
const APPEARANCES = ["auto", "light", "dark"];
const THEME_BG = { light: "#F6F4FC", dark: "#0C0B14" };

const $ = (id) => document.getElementById(id);
const clamp = (value, low, high) => Math.min(Math.max(Math.trunc(value), low), high);

const state = {
  mode: "password",
  appearance: "auto",
  password: { ...DEFAULT_PASSWORD },
  passphrase: { ...DEFAULT_PASSPHRASE },
  current: "",
  visible: true,
  history: [],
};

// ---------------------------------------------------------------- preferências
// Só as opções ficam no aparelho (localStorage) — as senhas nunca são gravadas.

function mergeTyped(target, source) {
  if (!source || typeof source !== "object") return;
  for (const key of Object.keys(target)) {
    if (typeof source[key] === typeof target[key]) target[key] = source[key];
  }
}

function loadSettings() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
    state.mode = data.mode === "passphrase" ? "passphrase" : "password";
    state.appearance = APPEARANCES.includes(data.appearance) ? data.appearance : "auto";
    mergeTyped(state.password, data.password);
    mergeTyped(state.passphrase, data.passphrase);
  } catch {
    /* armazenamento indisponível ou corrompido: segue com os padrões */
  }
  const pw = state.password;
  pw.length = clamp(pw.length, MIN_LENGTH, MAX_UI_LENGTH);
  pw.excludeChars = pw.excludeChars.slice(0, 40);
  if (!(pw.uppercase || pw.lowercase || pw.digits || pw.symbols)) {
    Object.assign(pw, { uppercase: true, lowercase: true, digits: true, symbols: true });
  }
  const pp = state.passphrase;
  pp.words = clamp(pp.words, MIN_WORDS, MAX_WORDS);
  if (!SEPARATORS.includes(pp.separator)) pp.separator = DEFAULT_PASSPHRASE.separator;
}

function saveSettings() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        mode: state.mode,
        appearance: state.appearance,
        password: state.password,
        passphrase: state.passphrase,
      }),
    );
  } catch {
    /* modo privado / sem espaço: preferências são só conveniência */
  }
}

// -------------------------------------------------------------------- controles

const bindings = [
  ["length", "password", "length", "number"],
  ["uppercase", "password", "uppercase", "bool"],
  ["lowercase", "password", "lowercase", "bool"],
  ["digits", "password", "digits", "bool"],
  ["symbols", "password", "symbols", "bool"],
  ["exclude-ambiguous", "password", "excludeAmbiguous", "bool"],
  ["exclude", "password", "excludeChars", "text"],
  ["words", "passphrase", "words", "number"],
  ["capitalize", "passphrase", "capitalize", "bool"],
  ["include-number", "passphrase", "includeNumber", "bool"],
];

function syncControls() {
  for (const [id, group, key, type] of bindings) {
    const el = $(id);
    if (type === "bool") el.checked = state[group][key];
    else el.value = state[group][key];
  }
  for (const [name, value] of [
    ["mode", state.mode],
    ["separator", state.passphrase.separator],
    ["appearance", state.appearance],
  ]) {
    const radio = document.querySelector(`input[name="${name}"][value="${CSS.escape(value)}"]`);
    if (radio) radio.checked = true;
  }
  updateLabels();
  showMode();
}

function bindControls() {
  for (const [id, group, key, type] of bindings) {
    $(id).addEventListener("input", (event) => {
      const el = event.currentTarget;
      state[group][key] = type === "bool" ? el.checked : type === "number" ? Number(el.value) : el.value;
      updateLabels();
      generate();
    });
  }
  for (const radio of document.querySelectorAll('input[name="mode"]')) {
    radio.addEventListener("change", () => {
      state.mode = radio.value;
      showMode();
      generate();
    });
  }
  for (const radio of document.querySelectorAll('input[name="separator"]')) {
    radio.addEventListener("change", () => {
      state.passphrase.separator = radio.value;
      generate();
    });
  }
  for (const radio of document.querySelectorAll('input[name="appearance"]')) {
    radio.addEventListener("change", () => {
      state.appearance = radio.value;
      applyTheme();
      saveSettings();
    });
  }
  $("generate").addEventListener("click", generate);
  $("copy").addEventListener("click", copyCurrent);
  $("toggle-visible").addEventListener("click", toggleVisible);
  $("clear-history").addEventListener("click", () => {
    state.history = [];
    renderHistory();
    showToast("Histórico limpo.");
  });
}

function updateLabels() {
  const { length } = state.password;
  const { words } = state.passphrase;
  $("length-value").textContent = String(length);
  $("words-value").textContent = String(words);
  setFill($("length"), length);
  setFill($("words"), words);
}

function setFill(range, value) {
  const low = Number(range.min);
  const high = Number(range.max);
  range.style.setProperty("--fill", `${((value - low) / (high - low)) * 100}%`);
}

function showMode() {
  const isPassphrase = state.mode === "passphrase";
  $("password-options").hidden = isPassphrase;
  $("passphrase-options").hidden = !isPassphrase;
}

// ------------------------------------------------------------------- aparência

const themeMetas = [...document.querySelectorAll('meta[name="theme-color"]')];
const themeMetaOriginals = themeMetas.map((meta) => meta.content);

function applyTheme() {
  const root = document.documentElement;
  if (state.appearance === "auto") {
    delete root.dataset.theme;
    themeMetas.forEach((meta, i) => (meta.content = themeMetaOriginals[i]));
  } else {
    root.dataset.theme = state.appearance;
    themeMetas.forEach((meta) => (meta.content = THEME_BG[state.appearance]));
  }
}

// ------------------------------------------------------------------- geração

function generate() {
  let bits = null;
  let message = "";
  try {
    if (state.mode === "passphrase") {
      state.current = generatePassphrase(state.passphrase);
      bits = passphraseEntropy(state.passphrase);
    } else {
      state.current = generatePassword(state.password);
      bits = passwordEntropy(state.password);
    }
  } catch (error) {
    if (!(error instanceof GenerationError)) throw error;
    state.current = "";
    message = error.message;
  }
  renderOutput(message);
  renderStrength(bits);
  $("error").textContent = message;
  saveSettings();
}

// ------------------------------------------------------------------ renderização

function charClass(char) {
  if (/[0-9]/.test(char)) return "d";
  if (/[A-Za-z]/.test(char)) return "";
  return "s";
}

function renderOutput(message = "") {
  const box = $("pw-text");
  box.replaceChildren();

  if (!state.current) {
    const note = document.createElement("span");
    note.className = "placeholder";
    note.textContent = message ? "Ajuste as opções abaixo" : "";
    box.append(note);
  } else if (!state.visible) {
    box.textContent = "•".repeat(Math.min(state.current.length, 32));
  } else {
    // Agrupa caracteres consecutivos da mesma cor para criar poucos nós.
    let run = "";
    let runClass = null;
    const flush = () => {
      if (!run) return;
      const span = document.createElement("span");
      if (runClass) span.className = runClass;
      span.textContent = run;
      box.append(span);
    };
    for (const char of state.current) {
      const cls = charClass(char);
      if (cls !== runClass) {
        flush();
        run = "";
        runClass = cls;
      }
      run += char;
    }
    flush();
  }

  const length = state.visible ? state.current.length : 0;
  $("output").dataset.size = length <= 20 ? "l" : length <= 32 ? "m" : length <= 48 ? "s" : "xs";
  $("copy").disabled = !state.current;
}

function renderStrength(bits) {
  const meter = $("meter");
  if (bits === null) {
    delete meter.dataset.level;
    $("meter-fill").style.width = "0";
    meter.setAttribute("aria-valuenow", "0");
    meter.removeAttribute("aria-valuetext");
    for (const id of ["strength-label", "strength-bits", "crack"]) $(id).textContent = "";
    return;
  }
  const strength = evaluateStrength(bits);
  meter.dataset.level = String(strength.level);
  $("meter-fill").style.width = `${Math.max(4, Math.min(bits / 128, 1) * 100)}%`;
  meter.setAttribute("aria-valuenow", String(Math.round(Math.min(bits, 128))));
  meter.setAttribute("aria-valuetext", strength.label);
  $("strength-label").textContent = strength.label;
  $("strength-bits").textContent = `≈ ${Math.round(bits)} bits de entropia`;
  $("crack").textContent = `Tempo para quebrar: ${strength.crackTime}`;
}

function toggleVisible() {
  state.visible = !state.visible;
  const button = $("toggle-visible");
  button.textContent = state.visible ? "Ocultar" : "Mostrar";
  button.setAttribute("aria-pressed", String(!state.visible));
  renderOutput();
  renderHistory();
}

function renderHistory() {
  const list = $("history");
  list.replaceChildren();
  $("clear-history").hidden = state.history.length === 0;

  if (state.history.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "As senhas que você copiar aparecem aqui. Ficam só na memória — nada é salvo.";
    list.append(empty);
    return;
  }

  for (const value of state.history) {
    const item = document.createElement("li");
    const text = document.createElement("span");
    text.className = "pw";
    text.textContent = state.visible ? value : "•".repeat(Math.min(value.length, 16));
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn";
    button.textContent = "Copiar";
    button.setAttribute("aria-label", "Copiar senha do histórico");
    button.addEventListener("click", () => copyText(value));
    item.append(text, button);
    list.append(item);
  }
}

// ----------------------------------------------------------------------- avisos

let toastTimer = null;

function showToast(message, { error = false, actionLabel = "", onAction = null, sticky = false } = {}) {
  clearTimeout(toastTimer);
  const toast = $("toast");
  toast.classList.toggle("error", error);
  $("toast-text").textContent = message;
  const action = $("toast-action");
  action.hidden = !actionLabel;
  action.textContent = actionLabel;
  action.onclick = onAction;
  toast.hidden = false;
  if (!sticky) toastTimer = setTimeout(hideToast, error ? 5000 : 2500);
}

function hideToast() {
  clearTimeout(toastTimer);
  $("toast").hidden = true;
}

// ------------------------------------------------------- área de transferência

const clip = { value: null, timer: null, left: 0, leftPage: false };
let copyLabelTimer = null;

function legacyCopy(value) {
  const area = document.createElement("textarea");
  area.value = value;
  area.setAttribute("readonly", "");
  area.style.cssText = "position:fixed;top:0;left:0;opacity:0;font-size:16px";
  document.body.append(area);
  area.focus();
  area.select();
  area.setSelectionRange(0, value.length);
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  area.remove();
  return ok;
}

async function copyText(value) {
  if (!value) return;
  let ok = false;
  try {
    await navigator.clipboard.writeText(value);
    ok = true;
  } catch {
    ok = legacyCopy(value);
  }
  if (!ok) {
    showToast("Não foi possível copiar. Segure sobre a senha e escolha Copiar.", { error: true });
    return;
  }

  state.history = [value, ...state.history.filter((v) => v !== value)].slice(0, HISTORY_LIMIT);
  renderHistory();
  startClipboardTimer(value);

  const copyButton = $("copy");
  copyButton.textContent = "Copiada ✓";
  clearTimeout(copyLabelTimer);
  copyLabelTimer = setTimeout(() => (copyButton.textContent = "Copiar"), 1500);
  showToast("Copiada para a área de transferência.");
}

const copyCurrent = () => copyText(state.current);

function startClipboardTimer(value) {
  clearInterval(clip.timer);
  clip.value = value;
  clip.left = CLIPBOARD_TIMEOUT;
  clip.leftPage = document.hidden;
  tickClipboard();
  clip.timer = setInterval(tickClipboard, 1000);
}

function tickClipboard() {
  if (clip.left <= 0) {
    clearInterval(clip.timer);
    clip.timer = null;
    $("hint").textContent = "";
    expireClipboard();
    return;
  }
  $("hint").textContent = `Área de transferência será limpa em ${clip.left}s`;
  clip.left -= 1;
}

// O navegador não deixa comparar o conteúdo da área de transferência sem pedir
// permissão. Se você saiu do app depois de copiar, pode ter copiado outra coisa;
// nesse caso pedimos um toque antes de apagar, para não destruir o que é seu.
function expireClipboard() {
  if (clip.leftPage) {
    showToast("Limpar a senha copiada da área de transferência?", {
      actionLabel: "Limpar",
      onAction: clearClipboard,
      sticky: true,
    });
  } else {
    clearClipboard();
  }
}

async function clearClipboard() {
  clip.value = null;
  try {
    await navigator.clipboard.writeText("");
    showToast("Área de transferência limpa.");
  } catch {
    showToast("Não consegui limpar sozinho. Copie outra coisa para substituir a senha.", { error: true });
  }
}

document.addEventListener("visibilitychange", () => {
  if (document.hidden && clip.value) clip.leftPage = true;
});

// ----------------------------------------------------------------- instalação

let installPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  $("install").hidden = false;
});

window.addEventListener("appinstalled", () => {
  installPrompt = null;
  $("install").hidden = true;
});

$("install").addEventListener("click", async () => {
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  $("install").hidden = true;
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {
      /* sem offline, mas o app continua funcionando */
    });
  });
}

// ---------------------------------------------------------------------- início

loadSettings();
syncControls();
bindControls();
applyTheme();
$("version").textContent = `v${VERSION}`;
renderHistory();
generate();
