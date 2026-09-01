import os
import secrets
import string
import tkinter as tk
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class PasswordGeneratorApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Gamera — Gerador de Senhas")
        self.geometry("500x520")
        self.minsize(450, 480)
        self.resizable(True, True)

        # Garante a busca do arquivo na mesma pasta do script
        base_path = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_path, "gamera_bg.png")

        # Label da imagem de fundo ocupando toda a tela
        try:
            raw_img = Image.open(img_path)
            self.bg_image = ctk.CTkImage(
                light_image=raw_img, dark_image=raw_img, size=(320, 420)
            )
            self.bg_label = ctk.CTkLabel(
                self, image=self.bg_image, text=""
            )
            self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            print(f"Erro ao carregar a imagem: {e}")

        # Interface sobreposta
        self.title_label = ctk.CTkLabel(
            self,
            text="🐢 GAMERA",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#8B5CF6",
        )
        self.title_label.pack(pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Gerador de Senhas Seguras",
            font=ctk.CTkFont(size=14),
            text_color="#94A3B8",
        )
        self.subtitle_label.pack(pady=(0, 15))

        self.password_entry = ctk.CTkEntry(
            self,
            width=320,
            height=45,
            font=ctk.CTkFont(size=16),
            justify="center",
        )
        self.password_entry.pack(pady=10)

        self.length_label = ctk.CTkLabel(
            self, text="Tamanho da Senha: 16", font=ctk.CTkFont(size=14)
        )
        self.length_label.pack(pady=(10, 0))

        self.length_slider = ctk.CTkSlider(
            self,
            from_=8,
            to=32,
            number_of_steps=24,
            command=self.update_length_label,
            width=300,
        )
        self.length_slider.set(16)
        self.length_slider.pack(pady=10)

        # Checkboxes sem frame opaco por trás
        self.upper_var = ctk.CTkCheckBox(
            self, text="Letras Maiúsculas (A-Z)"
        )
        self.upper_var.select()
        self.upper_var.pack(anchor="center", pady=5)

        self.lower_var = ctk.CTkCheckBox(
            self, text="Letras Minúsculas (a-z)"
        )
        self.lower_var.select()
        self.lower_var.pack(anchor="center", pady=5)

        self.digits_var = ctk.CTkCheckBox(self, text="Números (0-9)")
        self.digits_var.select()
        self.digits_var.pack(anchor="center", pady=5)

        self.symbols_var = ctk.CTkCheckBox(
            self, text="Símbolos (!@#$%...)"
        )
        self.symbols_var.select()
        self.symbols_var.pack(anchor="center", pady=5)

        # Botões
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=15)

        self.generate_btn = ctk.CTkButton(
            self.btn_frame,
            text="Gerar Senha",
            command=self.generate_password,
            width=130,
            height=35,
        )
        self.generate_btn.grid(row=0, column=0, padx=5)

        self.copy_btn = ctk.CTkButton(
            self.btn_frame,
            text="Copiar",
            command=self.copy_to_clipboard,
            width=100,
            height=35,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
        )
        self.copy_btn.grid(row=0, column=1, padx=5)

        self.status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#38BDF8"
        )
        self.status_label.pack(pady=(5, 0))

    def update_length_label(self, value):
        self.length_label.configure(
            text=f"Tamanho da Senha: {int(value)}"
        )

    def generate_password(self):
        length = int(self.length_slider.get())
        char_pool = ""

        if self.upper_var.get():
            char_pool += string.ascii_uppercase
        if self.lower_var.get():
            char_pool += string.ascii_lowercase
        if self.digits_var.get():
            char_pool += string.digits
        if self.symbols_var.get():
            char_pool += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not char_pool:
            self.password_entry.delete(0, tk.END)
            self.status_label.configure(
                text="Selecione ao menos uma opção!", text_color="#EF4444"
            )
            return

        password = "".join(secrets.choice(char_pool) for _ in range(length))

        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self.status_label.configure(
            text="Senha gerada com sucesso!", text_color="#38BDF8"
        )

    def copy_to_clipboard(self):
        password = self.password_entry.get()
        if password:
            self.clipboard_clear()
            self.clipboard_append(password)
            self.status_label.configure(
                text="Senha copiada para a área de transferência!",
                text_color="#10B981",
            )


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()