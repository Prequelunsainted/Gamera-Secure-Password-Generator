"""Interface gráfica do Gamera (CustomTkinter)."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk
from PIL import ImageTk

from . import __version__
from .assets import hero_image, icon_image
from .core import (
    MIN_LENGTH,
    MIN_WORDS,
    MAX_WORDS,
    GenerationError,
    PassphraseOptions,
    PasswordOptions,
    evaluate_strength,
    generate_passphrase,
    generate_password,
    passphrase_entropy,
    password_entropy,
)
from .settings import Settings

# Cores no formato (modo claro, modo escuro).
BG = ("#F6F4FC", "#0C0B14")
SIDEBAR = ("#EDE9FE", "#13111F")
CARD = ("#FFFFFF", "#17152A")
CARD_BORDER = ("#E4DEFA", "#252140")
INPUT = ("#F6F4FC", "#100E1D")
TEXT = ("#1E1B2E", "#ECEAF6")
MUTED = ("#6B6785", "#8F8AA8")
ACCENT = ("#7C3AED", "#8B5CF6")
ACCENT_HOVER = ("#6D28D9", "#7C3AED")
SUBTLE = ("#EDE9FE", "#221E38")
SUBTLE_HOVER = ("#DDD6FE", "#2E2950")
TRACK = ("#E4DEFA", "#2A2545")
CHECK_BORDER = ("#B9B1D8", "#4A4470")
SEGMENT_SELECTED = ("#C4B5FD", "#7C3AED")
SEGMENT_SELECTED_HOVER = ("#A78BFA", "#6D28D9")
DIGIT = ("#0369A1", "#38BDF8")
SYMBOL = ("#BE185D", "#F472B6")
SUCCESS = ("#047857", "#34D399")
DANGER = ("#DC2626", "#F87171")
STRENGTH_COLORS = ("#EF4444", "#F97316", "#EAB308", "#22C55E", "#10B981")

MAX_UI_LENGTH = 64
HISTORY_LIMIT = 10
CLIPBOARD_TIMEOUT = 30  # segundos
SEPARATORS = {"-": "-", ".": ".", "_": "_", "espaço": " "}
MODES = ("Senha", "Frase-senha")
APPEARANCES = ("Claro", "Escuro", "Sistema")
APPEARANCE_MODES = {"Claro": "light", "Escuro": "dark", "Sistema": "system"}


def _pick_mono_font(root: tk.Misc) -> str:
    available = set(tkfont.families(root))
    for family in ("Cascadia Mono", "JetBrains Mono", "Consolas", "SF Mono", "Menlo", "DejaVu Sans Mono"):
        if family in available:
            return family
    return "Courier New"


class GameraApp(ctk.CTk):
    def __init__(self) -> None:
        self.settings = Settings.load()
        ctk.set_appearance_mode(APPEARANCE_MODES.get(self.settings.appearance, "dark"))
        super().__init__(fg_color=BG)

        self.title("Gamera — Gerador de Senhas Seguras")
        self._center_window(1040, 740)
        self.minsize(960, 720)

        self.mono = _pick_mono_font(self)
        self.password = ""
        self.visible = True
        self.history: list[str] = []
        self._regen_job: str | None = None
        self._status_job: str | None = None
        self._copy_label_job: str | None = None
        self._clipboard_job: str | None = None
        self._clipboard_value: str | None = None
        self._clipboard_left = 0

        self._create_variables()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._bind_shortcuts()
        self._show_mode_options()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # O CustomTkinter troca o ícone da janela ~200 ms após abrir no Windows.
        self.after(300, self._set_window_icon)
        self.generate()

    # ------------------------------------------------------------------ estado

    def _create_variables(self) -> None:
        s = self.settings
        self.mode_var = ctk.StringVar(value=s.mode if s.mode in MODES else MODES[0])
        self.length_var = ctk.IntVar(value=min(max(s.length, MIN_LENGTH), MAX_UI_LENGTH))
        self.upper_var = ctk.BooleanVar(value=s.uppercase)
        self.lower_var = ctk.BooleanVar(value=s.lowercase)
        self.digits_var = ctk.BooleanVar(value=s.digits)
        self.symbols_var = ctk.BooleanVar(value=s.symbols)
        self.ambiguous_var = ctk.BooleanVar(value=s.exclude_ambiguous)
        self.exclude_var = ctk.StringVar(value=s.exclude_chars)
        self.words_var = ctk.IntVar(value=min(max(s.words, MIN_WORDS), MAX_WORDS))
        separator_label = next((k for k, v in SEPARATORS.items() if v == s.separator), "-")
        self.separator_var = ctk.StringVar(value=separator_label)
        self.capitalize_var = ctk.BooleanVar(value=s.capitalize)
        self.number_var = ctk.BooleanVar(value=s.include_number)
        self.appearance_var = ctk.StringVar(
            value=s.appearance if s.appearance in APPEARANCES else "Escuro"
        )
        self.exclude_var.trace_add("write", lambda *_: self._schedule_generate())

    def _password_options(self) -> PasswordOptions:
        return PasswordOptions(
            length=self.length_var.get(),
            uppercase=self.upper_var.get(),
            lowercase=self.lower_var.get(),
            digits=self.digits_var.get(),
            symbols=self.symbols_var.get(),
            exclude_ambiguous=self.ambiguous_var.get(),
            exclude_chars=self.exclude_var.get(),
        )

    def _passphrase_options(self) -> PassphraseOptions:
        return PassphraseOptions(
            words=self.words_var.get(),
            separator=SEPARATORS[self.separator_var.get()],
            capitalize=self.capitalize_var.get(),
            include_number=self.number_var.get(),
        )

    def _save_settings(self) -> None:
        pw, pp = self._password_options(), self._passphrase_options()
        Settings(
            appearance=self.appearance_var.get(),
            mode=self.mode_var.get(),
            length=pw.length,
            uppercase=pw.uppercase,
            lowercase=pw.lowercase,
            digits=pw.digits,
            symbols=pw.symbols,
            exclude_ambiguous=pw.exclude_ambiguous,
            exclude_chars=pw.exclude_chars,
            words=pp.words,
            separator=pp.separator,
            capitalize=pp.capitalize,
            include_number=pp.include_number,
        ).save()

    # ------------------------------------------------------------- construção

    def _font(self, size: int, weight: str = "normal", mono: bool = False) -> ctk.CTkFont:
        return ctk.CTkFont(family=self.mono if mono else None, size=size, weight=weight)

    def _card(self, master: tk.Misc) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            master, fg_color=CARD, border_color=CARD_BORDER, border_width=1, corner_radius=16
        )

    def _section_label(self, master: tk.Misc, text: str) -> ctk.CTkLabel:
        return ctk.CTkLabel(master, text=text.upper(), font=self._font(11, "bold"), text_color=MUTED)

    def _checkbox(self, master: tk.Misc, text: str, variable: ctk.BooleanVar) -> ctk.CTkCheckBox:
        return ctk.CTkCheckBox(
            master,
            text=text,
            variable=variable,
            onvalue=True,
            offvalue=False,
            command=self._schedule_generate,
            font=self._font(13),
            text_color=TEXT,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            border_color=CHECK_BORDER,
            checkmark_color="#FFFFFF",
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            border_width=2,
        )

    def _segmented(self, master: tk.Misc, **kwargs) -> ctk.CTkSegmentedButton:
        options = dict(
            selected_color=SEGMENT_SELECTED,
            selected_hover_color=SEGMENT_SELECTED_HOVER,
            unselected_color=SUBTLE,
            unselected_hover_color=SUBTLE_HOVER,
            fg_color=SUBTLE,
            text_color=TEXT,
            font=self._font(13, "bold"),
        )
        options.update(kwargs)
        return ctk.CTkSegmentedButton(master, **options)

    def _build_sidebar(self) -> None:
        bar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=SIDEBAR)
        bar.grid(row=0, column=0, sticky="nsew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_rowconfigure(3, weight=1)

        light = hero_image(top="#8B5CF6", bottom="#0EA5E9", glow="#A78BFA", glow_strength=0.45)
        dark = hero_image(top="#C4B5FD", bottom="#38BDF8", glow="#7C3AED", glow_strength=0.6)
        height = 250
        width = round(light.width * height / light.height)
        self.hero = ctk.CTkImage(light_image=light, dark_image=dark, size=(width, height))
        ctk.CTkLabel(bar, image=self.hero, text="").grid(row=0, column=0, pady=(28, 4))

        ctk.CTkLabel(bar, text="GAMERA", font=self._font(32, "bold"), text_color=TEXT).grid(
            row=1, column=0
        )
        ctk.CTkLabel(
            bar, text="Gerador de senhas seguras", font=self._font(14), text_color=MUTED
        ).grid(row=2, column=0, pady=(0, 20))

        features = ctk.CTkFrame(bar, fg_color="transparent")
        features.grid(row=3, column=0, sticky="new", padx=32)
        for title, detail in (
            ("Criptograficamente seguro", "módulo secrets do sistema"),
            ("100% offline", "nada sai do seu computador"),
            ("Área de transferência protegida", f"limpa sozinha em {CLIPBOARD_TIMEOUT}s"),
        ):
            row = ctk.CTkFrame(features, fg_color="transparent")
            row.pack(fill="x", pady=6)
            ctk.CTkLabel(row, text="●", font=self._font(10), text_color=ACCENT, width=14).pack(
                side="left", anchor="n", pady=(3, 0)
            )
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", fill="x", padx=(8, 0))
            ctk.CTkLabel(text, text=title, font=self._font(13, "bold"), text_color=TEXT, anchor="w").pack(
                fill="x"
            )
            ctk.CTkLabel(text, text=detail, font=self._font(12), text_color=MUTED, anchor="w").pack(
                fill="x"
            )

        footer = ctk.CTkFrame(bar, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=32, pady=(0, 24))
        self._section_label(footer, "Aparência").pack(anchor="w", pady=(0, 6))
        self._segmented(
            footer,
            values=list(APPEARANCES),
            variable=self.appearance_var,
            command=self._on_appearance,
            font=self._font(12),
            unselected_color=CARD,
            fg_color=CARD,
        ).pack(fill="x")
        ctk.CTkLabel(
            footer, text=f"v{__version__}", font=self._font(11), text_color=MUTED
        ).pack(anchor="w", pady=(12, 0))

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=32, pady=(26, 14))
        main.grid_columnconfigure(0, weight=3, uniform="cols")
        main.grid_columnconfigure(1, weight=2, uniform="cols")
        main.grid_rowconfigure(2, weight=1)

        # Cabeçalho
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        heading = ctk.CTkFrame(header, fg_color="transparent")
        heading.pack(side="left")
        ctk.CTkLabel(heading, text="Nova senha", font=self._font(24, "bold"), text_color=TEXT).pack(
            anchor="w"
        )
        ctk.CTkLabel(
            heading,
            text="Gerada localmente a cada alteração das opções.",
            font=self._font(13),
            text_color=MUTED,
        ).pack(anchor="w")
        self._segmented(
            header,
            values=list(MODES),
            variable=self.mode_var,
            command=lambda _: self._on_mode(),
            height=36,
            unselected_color=CARD,
            fg_color=CARD,
        ).pack(side="right")

        self._build_output_card(main)
        self._build_options_card(main)
        self._build_history_card(main)

        # Barra de status
        status = ctk.CTkFrame(main, fg_color="transparent")
        status.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.status_label = ctk.CTkLabel(status, text="", font=self._font(12), text_color=MUTED, anchor="w")
        self.status_label.pack(side="left")
        self.hint_label = ctk.CTkLabel(status, text="", font=self._font(12), text_color=MUTED, anchor="e")
        self.hint_label.pack(side="right")
        self._show_shortcuts_hint()

    def _build_output_card(self, main: ctk.CTkFrame) -> None:
        card = self._card(main)
        card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(0, weight=1)

        self.output_font = self._font(24, mono=True)
        self.output = ctk.CTkTextbox(
            card,
            height=96,
            fg_color=INPUT,
            border_width=0,
            corner_radius=12,
            font=self.output_font,
            text_color=TEXT,
            wrap="char",
            activate_scrollbars=False,
        )
        self.output.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 14))
        self.output.configure(cursor="arrow", spacing1=8, spacing3=8)
        self.output.tag_config("center", justify="center")

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        bottom.grid_columnconfigure(0, weight=1)

        meter = ctk.CTkFrame(bottom, fg_color="transparent")
        meter.grid(row=0, column=0, sticky="ew", padx=(0, 18))
        meter.grid_columnconfigure(0, weight=1)
        self.strength_bar = ctk.CTkProgressBar(meter, height=8, corner_radius=4, fg_color=TRACK)
        self.strength_bar.grid(row=0, column=0, sticky="ew", pady=(4, 8))
        labels = ctk.CTkFrame(meter, fg_color="transparent")
        labels.grid(row=1, column=0, sticky="w")
        self.strength_label = ctk.CTkLabel(labels, text="", font=self._font(14, "bold"))
        self.strength_label.pack(side="left")
        self.entropy_label = ctk.CTkLabel(labels, text="", font=self._font(13), text_color=MUTED)
        self.entropy_label.pack(side="left", padx=(8, 0))
        self.crack_label = ctk.CTkLabel(meter, text="", font=self._font(12), text_color=MUTED, anchor="w")
        self.crack_label.grid(row=2, column=0, sticky="ew")

        buttons = ctk.CTkFrame(bottom, fg_color="transparent")
        buttons.grid(row=0, column=1, sticky="e")
        secondary = dict(
            height=40,
            corner_radius=10,
            fg_color=SUBTLE,
            hover_color=SUBTLE_HOVER,
            text_color=TEXT,
            font=self._font(13, "bold"),
        )
        self.visibility_btn = ctk.CTkButton(
            buttons, text="Ocultar", width=92, command=self.toggle_visibility, **secondary
        )
        self.visibility_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="↻  Gerar", width=100, command=self.generate, **secondary).pack(
            side="left", padx=(0, 8)
        )
        self.copy_btn = ctk.CTkButton(
            buttons,
            text="Copiar",
            width=120,
            height=40,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            font=self._font(14, "bold"),
            command=self.copy_current,
        )
        self.copy_btn.pack(side="left")

    def _build_options_card(self, main: ctk.CTkFrame) -> None:
        card = self._card(main)
        card.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)

        # --- Opções de senha
        self.password_frame = ctk.CTkFrame(card, fg_color="transparent")
        f = self.password_frame
        f.grid_columnconfigure((0, 1), weight=1)

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._section_label(top, "Tamanho").pack(side="left")
        self.length_label = ctk.CTkLabel(top, text="", font=self._font(20, "bold"), text_color=ACCENT)
        self.length_label.pack(side="right")
        self.length_slider = ctk.CTkSlider(
            f,
            from_=MIN_LENGTH,
            to=MAX_UI_LENGTH,
            number_of_steps=MAX_UI_LENGTH - MIN_LENGTH,
            variable=self.length_var,
            command=lambda _: self._on_slider(),
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT,
            fg_color=TRACK,
        )
        self.length_slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        self._section_label(f, "Caracteres").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        for i, (text, var) in enumerate(
            (
                ("Maiúsculas  A–Z", self.upper_var),
                ("Minúsculas  a–z", self.lower_var),
                ("Números  0–9", self.digits_var),
                ("Símbolos  !@#", self.symbols_var),
            )
        ):
            self._checkbox(f, text, var).grid(row=3 + i // 2, column=i % 2, sticky="w", pady=4)
        self._checkbox(f, "Evitar caracteres parecidos (Il1O0)", self.ambiguous_var).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(4, 12)
        )

        self._section_label(f, "Nunca usar estes caracteres").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        ctk.CTkEntry(
            f,
            textvariable=self.exclude_var,
            font=self._font(14, mono=True),
            fg_color=INPUT,
            border_color=CARD_BORDER,
            text_color=TEXT,
            height=36,
            corner_radius=10,
        ).grid(row=7, column=0, columnspan=2, sticky="ew")

        # --- Opções de frase-senha
        self.passphrase_frame = ctk.CTkFrame(card, fg_color="transparent")
        p = self.passphrase_frame
        p.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(p, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        self._section_label(top, "Palavras").pack(side="left")
        self.words_label = ctk.CTkLabel(top, text="", font=self._font(20, "bold"), text_color=ACCENT)
        self.words_label.pack(side="right")
        ctk.CTkSlider(
            p,
            from_=MIN_WORDS,
            to=MAX_WORDS,
            number_of_steps=MAX_WORDS - MIN_WORDS,
            variable=self.words_var,
            command=lambda _: self._on_slider(),
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT,
            fg_color=TRACK,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 14))

        self._section_label(p, "Separador").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self._segmented(
            p,
            values=list(SEPARATORS),
            variable=self.separator_var,
            command=lambda _: self._schedule_generate(),
            font=self._font(14, "bold"),
            height=34,
        ).grid(row=3, column=0, sticky="ew", pady=(0, 14))

        self._checkbox(p, "Iniciais maiúsculas", self.capitalize_var).grid(row=4, column=0, sticky="w", pady=5)
        self._checkbox(p, "Incluir um número", self.number_var).grid(row=5, column=0, sticky="w", pady=5)
        ctk.CTkLabel(
            p,
            text="Frases-senha são fáceis de lembrar e de digitar,\n"
            "e continuam fortes com 6 ou mais palavras.",
            font=self._font(12),
            text_color=MUTED,
            justify="left",
        ).grid(row=6, column=0, sticky="w", pady=(12, 0))

    def _build_history_card(self, main: ctk.CTkFrame) -> None:
        card = self._card(main)
        card.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 4))
        self._section_label(top, "Copiadas recentemente").pack(side="left")
        ctk.CTkButton(
            top,
            text="Limpar",
            width=60,
            height=24,
            corner_radius=8,
            fg_color="transparent",
            hover_color=SUBTLE,
            text_color=MUTED,
            font=self._font(12),
            command=self.clear_history,
        ).pack(side="right")

        self.history_list = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=TRACK,
            scrollbar_button_hover_color=SUBTLE_HOVER,
        )
        self.history_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 12))
        self.history_list.grid_columnconfigure(0, weight=1)
        self._render_history()

    def _bind_shortcuts(self) -> None:
        for sequence in ("<Control-g>", "<Control-G>", "<F5>"):
            self.bind(sequence, lambda _: self.generate())
        self.bind("<Control-C>", lambda _: self.copy_current())  # Ctrl+Shift+C
        self.bind("<Control-H>", lambda _: self.toggle_visibility())  # Ctrl+Shift+H

    def _center_window(self, width: int, height: int) -> None:
        # O Tk informa a tela em pixels lógicos, mas o CustomTkinter só escala o
        # tamanho da janela pelo DPI — a posição é aplicada em pixels físicos.
        scale = self._get_window_scaling()
        x = max(0, int((self.winfo_screenwidth() - width) * scale / 2))
        y = max(0, int(((self.winfo_screenheight() - height) * scale - 80) / 2))  # 80: barra de título + tarefas
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _set_window_icon(self) -> None:
        self._icon = ImageTk.PhotoImage(icon_image("#8B5CF6"))
        self.iconphoto(False, self._icon)

    # ---------------------------------------------------------------- eventos

    def _on_mode(self) -> None:
        self._show_mode_options()
        self.generate()

    def _show_mode_options(self) -> None:
        is_passphrase = self.mode_var.get() == "Frase-senha"
        show, hide = (
            (self.passphrase_frame, self.password_frame)
            if is_passphrase
            else (self.password_frame, self.passphrase_frame)
        )
        hide.grid_remove()
        show.grid(row=0, column=0, sticky="nsew", padx=20, pady=18)
        self._update_value_labels()

    def _on_slider(self) -> None:
        self._update_value_labels()
        self._schedule_generate()

    def _update_value_labels(self) -> None:
        self.length_label.configure(text=str(self.length_var.get()))
        self.words_label.configure(text=str(self.words_var.get()))

    def _on_appearance(self, choice: str) -> None:
        ctk.set_appearance_mode(APPEARANCE_MODES[choice])
        self._render_output()
        self._save_settings()

    def _schedule_generate(self) -> None:
        if self._regen_job:
            self.after_cancel(self._regen_job)
        self._regen_job = self.after(90, self.generate)

    def _on_close(self) -> None:
        self._save_settings()
        self._clear_clipboard(silent=True)
        self.destroy()

    # ---------------------------------------------------------------- ações

    def generate(self) -> None:
        self._regen_job = None
        try:
            if self.mode_var.get() == "Frase-senha":
                pp = self._passphrase_options()
                self.password = generate_passphrase(pp)
                bits = passphrase_entropy(pp)
            else:
                pw = self._password_options()
                self.password = generate_password(pw)
                bits = password_entropy(pw)
        except GenerationError as error:
            self.password = ""
            self._render_output(placeholder="Ajuste as opções abaixo")
            self._render_strength(None)
            self._set_status(str(error), DANGER)
            return

        self._render_output()
        self._render_strength(bits)

    def toggle_visibility(self) -> None:
        self.visible = not self.visible
        self.visibility_btn.configure(text="Ocultar" if self.visible else "Mostrar")
        self._render_output()
        self._render_history()

    def copy_current(self) -> None:
        if not self.password:
            self._set_status("Não há senha para copiar.", DANGER)
            return
        self._copy(self.password)
        self.copy_btn.configure(text="Copiada ✓")
        if self._copy_label_job:
            self.after_cancel(self._copy_label_job)
        self._copy_label_job = self.after(1500, lambda: self.copy_btn.configure(text="Copiar"))

    def _copy(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update_idletasks()
        self._clipboard_value = value
        self._clipboard_left = CLIPBOARD_TIMEOUT
        self._add_to_history(value)
        self._set_status("Copiada para a área de transferência.", SUCCESS)
        self._tick_clipboard()

    def _tick_clipboard(self) -> None:
        if self._clipboard_job:
            self.after_cancel(self._clipboard_job)
            self._clipboard_job = None
        if self._clipboard_left <= 0:
            self._clear_clipboard()
            return
        self.hint_label.configure(
            text=f"Área de transferência será limpa em {self._clipboard_left}s",
            text_color=ACCENT,
        )
        self._clipboard_left -= 1
        self._clipboard_job = self.after(1000, self._tick_clipboard)

    def _clear_clipboard(self, silent: bool = False) -> None:
        if self._clipboard_job:
            self.after_cancel(self._clipboard_job)
            self._clipboard_job = None
        if self._clipboard_value is None:
            return
        try:
            current = self.clipboard_get()
        except tk.TclError:
            current = None
        # Só apaga se o conteúdo ainda for nosso — não destrói o que o usuário copiou depois.
        if current == self._clipboard_value:
            self.clipboard_clear()
            self.clipboard_append("")
            if not silent:
                self._set_status("Área de transferência limpa.", MUTED)
        self._clipboard_value = None
        if not silent:
            self._show_shortcuts_hint()

    def _add_to_history(self, value: str) -> None:
        if value in self.history:
            self.history.remove(value)
        self.history.insert(0, value)
        del self.history[HISTORY_LIMIT:]
        self._render_history()

    def clear_history(self) -> None:
        self.history.clear()
        self._render_history()
        self._set_status("Histórico limpo.", MUTED)

    # ------------------------------------------------------------ renderização

    def _color(self, pair: tuple[str, str]) -> str:
        return pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0]

    def _render_output(self, placeholder: str | None = None) -> None:
        box = self.output
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.tag_config("letter", foreground=self._color(TEXT))
        box.tag_config("digit", foreground=self._color(DIGIT))
        box.tag_config("symbol", foreground=self._color(SYMBOL))
        box.tag_config("muted", foreground=self._color(MUTED))

        # Diminui a fonte para senhas longas caberem sem quebrar no meio de uma palavra.
        length = len(self.password) if self.visible else 0
        size = 24 if length <= 30 else 20 if length <= 38 else 17 if length <= 46 else 15
        self.output_font.configure(size=size)

        if not self.password:
            box.insert("end", placeholder or "", ("muted", "center"))
        elif not self.visible:
            box.insert("end", "•" * min(len(self.password), 32), ("letter", "center"))
        else:
            for char in self.password:
                if char.isdigit():
                    tag = "digit"
                elif char.isalpha():
                    tag = "letter"
                else:
                    tag = "symbol"
                box.insert("end", char, (tag, "center"))
        box.configure(state="disabled")

    def _render_strength(self, bits: float | None) -> None:
        if bits is None:
            self.strength_bar.configure(progress_color=TRACK)
            self.strength_bar.set(0)
            for label in (self.strength_label, self.entropy_label, self.crack_label):
                label.configure(text="")
            return
        strength = evaluate_strength(bits)
        color = STRENGTH_COLORS[strength.level]
        self.strength_bar.configure(progress_color=color)
        self.strength_bar.set(max(0.04, min(bits / 128, 1)))
        self.strength_label.configure(text=strength.label, text_color=color)
        self.entropy_label.configure(text=f"≈ {bits:.0f} bits de entropia")
        self.crack_label.configure(text=f"Tempo para quebrar: {strength.crack_time}")

    def _render_history(self) -> None:
        for child in self.history_list.winfo_children():
            child.destroy()

        if not self.history:
            ctk.CTkLabel(
                self.history_list,
                text="As senhas que você copiar aparecem aqui. "
                "Ficam só na memória — nada é salvo em disco.",
                font=self._font(12),
                text_color=MUTED,
                justify="left",
                anchor="w",
                wraplength=200,
            ).grid(row=0, column=0, sticky="ew", padx=12, pady=8)
            return

        for i, value in enumerate(self.history):
            row = ctk.CTkFrame(self.history_list, fg_color=INPUT, corner_radius=10)
            row.grid(row=i, column=0, sticky="ew", padx=4, pady=3)
            row.grid_columnconfigure(0, weight=1)
            shown = value if self.visible else "•" * min(len(value), 16)
            if len(shown) > 26:
                shown = shown[:25] + "…"
            ctk.CTkLabel(
                row, text=shown, font=self._font(13, mono=True), text_color=TEXT, anchor="w"
            ).grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=6)
            ctk.CTkButton(
                row,
                text="Copiar",
                width=64,
                height=26,
                corner_radius=8,
                fg_color=SUBTLE,
                hover_color=SUBTLE_HOVER,
                text_color=TEXT,
                font=self._font(12),
                command=lambda v=value: self._copy(v),
            ).grid(row=0, column=1, padx=(0, 8))

    def _set_status(self, message: str, color: tuple[str, str]) -> None:
        self.status_label.configure(text=message, text_color=color)
        if self._status_job:
            self.after_cancel(self._status_job)
        self._status_job = self.after(4000, lambda: self.status_label.configure(text=""))

    def _show_shortcuts_hint(self) -> None:
        self.hint_label.configure(
            text="Ctrl+G gerar  ·  Ctrl+Shift+C copiar  ·  Ctrl+Shift+H ocultar",
            text_color=MUTED,
        )


def run_app() -> None:
    GameraApp().mainloop()
