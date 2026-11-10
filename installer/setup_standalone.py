"""
Instalador Autocontido Oficial - LCR OdontoGest
Executável único que contém todo o sistema embutido (SEM necessidade de .zip externo no GitHub).
"""

import os
import sys
import hashlib
import zipfile
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "LCR OdontoGest"
EXE_NAME = "LCR-OdontoGest.exe"
DEST_DIR = Path("C:/LCR-OdontoGest")


class StandaloneInstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Instalador — {APP_NAME}")
        self.geometry("540x380")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # Centraliza a janela na tela
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Tenta aplicar ícone se existir
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        icon_path = base_dir / "assets" / "app_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.setup_ui()

    def setup_ui(self):
        # Header com fundo Teal (#0f766e)
        header = tk.Frame(self, bg="#0f766e", height=90)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        lbl_title = tk.Label(
            header,
            text=APP_NAME,
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg="#0f766e"
        )
        lbl_title.pack(anchor="w", padx=24, pady=(16, 2))

        lbl_sub = tk.Label(
            header,
            text="Instalador Oficial Completo — Sistema Integrado de Gestão",
            font=("Segoe UI", 9),
            fg="#ccfbf1",
            bg="#0f766e"
        )
        lbl_sub.pack(anchor="w", padx=24)

        # Corpo principal
        body = tk.Frame(self, bg="#f8fafc")
        body.pack(fill="both", expand=True, padx=28, pady=18)

        # Destino
        lbl_dest_info = tk.Label(
            body,
            text=f"Pasta de Destino: {DEST_DIR}",
            font=("Segoe UI", 9, "bold"),
            fg="#334155",
            bg="#f8fafc"
        )
        lbl_dest_info.pack(anchor="w", pady=(0, 4))

        lbl_desc = tk.Label(
            body,
            text="Este instalador contém todos os arquivos do sistema embutidos.\n"
                 "Nenhum arquivo externo ou download adicional é necessário.",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#f8fafc",
            justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(0, 14))

        # Barra de Progresso
        self.progress = ttk.Progressbar(body, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 8))

        # Status do progresso
        self.lbl_status = tk.Label(
            body,
            text="Pronto para iniciar a instalação.",
            font=("Segoe UI", 9),
            fg="#0f766e",
            bg="#f8fafc"
        )
        self.lbl_status.pack(anchor="w")

        # Rodapé com Botões
        footer = tk.Frame(self, bg="#f1f5f9", height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.btn_cancel = tk.Button(
            footer,
            text="Cancelar",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#475569",
            activebackground="#e2e8f0",
            relief="groove",
            bd=1,
            padx=14,
            pady=4,
            command=self.destroy
        )
        self.btn_cancel.pack(side="right", padx=(0, 24), pady=14)

        self.btn_action = tk.Button(
            footer,
            text="Instalar Agora",
            font=("Segoe UI", 9, "bold"),
            bg="#0f766e",
            fg="#ffffff",
            activebackground="#115e59",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2",
            command=self.iniciar_instalacao
        )
        self.btn_action.pack(side="right", padx=(0, 10), pady=14)

    def iniciar_instalacao(self):
        self.btn_action.config(state="disabled", text="Instalando...")
        self.btn_cancel.config(state="disabled")
        t = threading.Thread(target=self._processo_instalacao, daemon=True)
        t.start()

    def set_status(self, text, progress_val=None):
        def _update():
            self.lbl_status.config(text=text)
            if progress_val is not None:
                self.progress["value"] = progress_val
        self.after(0, _update)

    def _processo_instalacao(self):
        try:
            self.set_status("1/4: Localizando pacote interno de dados...", 15)

            # Localiza o arquivo payload embutido no executável
            base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            payload_zip = base_dir / "payload" / "LCR-OdontoGest.zip"

            if not payload_zip.exists():
                # Fallback para desenvolvimento local
                payload_zip = Path(__file__).resolve().parent.parent / "dist" / "LCR-OdontoGest.zip"

            if not payload_zip.exists():
                raise Exception("Pacote de dados interno não encontrado dentro do instalador.")

            # 2. Descompactação direta para DEST_DIR
            self.set_status("2/4: Extraindo e configurando arquivos em C:\\LCR-OdontoGest...", 30)
            DEST_DIR.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(payload_zip, "r") as zip_ref:
                total_files = len(zip_ref.infolist())
                for i, item in enumerate(zip_ref.infolist()):
                    zip_ref.extract(item, DEST_DIR)
                    if i % 20 == 0 or i == total_files - 1:
                        pct = int(30 + (i / total_files) * 55)
                        self.set_status(f"2/4: Instalando arquivos ({i+1}/{total_files})...", pct)

            # 3. Criação de pastas de dados seguras (se não existirem)
            self.set_status("3/4: Inicializando estrutura segura de dados...", 88)
            (DEST_DIR / "data").mkdir(parents=True, exist_ok=True)
            (DEST_DIR / "uploads").mkdir(parents=True, exist_ok=True)

            # 4. Criar Atalho na Área de Trabalho
            self.set_status("4/4: Criando atalho oficial na Área de Trabalho...", 95)
            self._criar_atalho()

            self.set_status("Instalação concluída com sucesso!", 100)
            self.after(0, self._finalizar_sucesso)

        except Exception as e:
            self.after(0, lambda: self._finalizar_erro(str(e)))

    def _criar_atalho(self):
        try:
            exe_path = DEST_DIR / EXE_NAME
            if not exe_path.exists():
                for found in DEST_DIR.glob(f"**/{EXE_NAME}"):
                    exe_path = found
                    break

            ico_path = exe_path.parent / "assets" / "app_icon.ico"
            desktop = Path(os.environ.get("USERPROFILE", "C:/")) / "Desktop"
            if not desktop.exists():
                desktop = Path(os.environ.get("HOMEDRIVE", "C:") + os.environ.get("HOMEPATH", "/")) / "Desktop"

            shortcut_path = desktop / f"{APP_NAME}.lnk"

            cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                f"$w = New-Object -ComObject WScript.Shell; "
                f"$s = $w.CreateShortcut('{shortcut_path}'); "
                f"$s.TargetPath = '{exe_path}'; "
                f"$s.WorkingDirectory = '{exe_path.parent}'; "
                f"$ico = '{ico_path}'; if (Test-Path $ico) {{ $s.IconLocation = $ico; }}; "
                f"$s.Save();"
            ]
            subprocess.run(cmd, capture_output=True)
        except Exception:
            pass

    def _finalizar_sucesso(self):
        self.btn_cancel.config(text="Fechar", state="normal", command=self.destroy)
        self.btn_action.config(
            text="✓ Iniciar Sistema",
            state="normal",
            command=self._iniciar_sistema
        )
        messagebox.showinfo(
            "Instalação Concluída",
            f"O {APP_NAME} foi instalado com sucesso!\n"
            f"Local: {DEST_DIR}\n"
            "O atalho oficial com ícone foi criado na sua Área de Trabalho."
        )

    def _iniciar_sistema(self):
        try:
            exe_path = DEST_DIR / EXE_NAME
            if not exe_path.exists():
                for found in DEST_DIR.glob(f"**/{EXE_NAME}"):
                    exe_path = found
                    break
            subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
        except Exception as e:
            messagebox.showerror("Aviso", f"Não foi possível iniciar automaticamente:\n{e}")
        self.destroy()

    def _finalizar_erro(self, msg):
        self.lbl_status.config(text="Falha na instalação.", fg="#dc2626")
        self.btn_action.config(state="normal", text="Tentar Novamente", command=self.iniciar_instalacao)
        self.btn_cancel.config(state="normal")
        messagebox.showerror("Erro na Instalação", f"Ocorreu um problema:\n\n{msg}")


if __name__ == "__main__":
    app = StandaloneInstallerApp()
    app.mainloop()
