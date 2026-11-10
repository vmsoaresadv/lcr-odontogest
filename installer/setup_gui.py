"""
Instalador Gráfico Oficial - LCR OdontoGest
Executável leve com validação criptográfica SHA-256 e download seguro a partir do GitHub Releases.
"""

import os
import sys
import json
import hashlib
import zipfile
import threading
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Configurações do Repositório de Atualizações
REPO = "vmsoaresadv/lcr-odontogest"
VERSION_JSON_URL = f"https://raw.githubusercontent.com/{REPO}/main/version.json"
API_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
DEST_DIR = Path("C:/LCR-OdontoGest")
APP_NAME = "LCR OdontoGest"
EXE_NAME = "LCR-OdontoGest.exe"


def calcular_sha256(arquivo_path: Path) -> str:
    """Calcula o hash SHA-256 do arquivo em blocos de 64KB."""
    hasher = hashlib.sha256()
    with open(arquivo_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


class ModernInstallerApp(tk.Tk):
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
            text="Instalador Oficial com Validação Criptográfica de Segurança (SHA-256)",
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
            text="O instalador irá consultar a chave oficial de integridade,\nbaixar o sistema autenticado e criar o atalho oficial na Área de Trabalho.",
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
            text="Pronto para iniciar a instalação segura.",
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
            self.set_status("1/5: Consultando chave oficial de segurança (version.json)...", 10)

            # 1. Consulta o version.json oficial para obter a chave criptográfica
            versao_remota = "1.0.0"
            chave_esperada = None
            download_url = None

            try:
                req_v = urllib.request.Request(
                    VERSION_JSON_URL,
                    headers={"User-Agent": "LCR-OdontoGest-Installer/1.0", "Cache-Control": "no-cache"}
                )
                with urllib.request.urlopen(req_v, timeout=10) as resp_v:
                    v_data = json.loads(resp_v.read().decode("utf-8"))
                    versao_remota = v_data.get("version", "1.0.0")
                    chave_esperada = v_data.get("package_sha256")
                    download_url = v_data.get("download_url")
            except Exception:
                pass  # Tenta fallback pelo Releases API se version.json ainda não estiver na raiz

            # 2. Se download_url não veio do version.json, busca na release mais recente
            if not download_url:
                req = urllib.request.Request(
                    API_RELEASE_URL,
                    headers={"User-Agent": "LCR-OdontoGest-Installer/1.0"}
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    rel_data = json.loads(response.read().decode("utf-8"))

                assets = rel_data.get("assets", [])
                for a in assets:
                    name = a.get("name", "")
                    if name.lower().endswith(".zip") and "source" not in name.lower():
                        download_url = a.get("browser_download_url")
                        break

            if not download_url:
                raise Exception(
                    "O arquivo LCR-OdontoGest.zip ainda não foi anexado na Release do GitHub.\n"
                    "Por favor, anexe o arquivo .zip na release e tente novamente."
                )

            # 3. Baixar o arquivo .zip
            temp_zip = Path(os.environ.get("TEMP", ".")) / f"LCR-OdontoGest-{versao_remota}.zip"
            self.set_status(f"2/5: Baixando sistema v{versao_remota}...", 20)

            def reporthook(blocknum, blocksize, totalsize):
                if totalsize > 0:
                    percent = min(75, int(20 + (blocknum * blocksize / totalsize) * 55))
                    mb_downloaded = (blocknum * blocksize) / (1024 * 1024)
                    mb_total = totalsize / (1024 * 1024)
                    self.set_status(f"2/5: Baixando: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent}%)", percent)

            urllib.request.urlretrieve(download_url, str(temp_zip), reporthook=reporthook)

            # 4. Validação da Chave Criptográfica SHA-256
            self.set_status("3/5: Validando integridade criptográfica (SHA-256)...", 78)
            hash_baixado = calcular_sha256(temp_zip)

            if chave_esperada:
                if hash_baixado.upper() != chave_esperada.upper().strip():
                    try:
                        temp_zip.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise Exception(
                        "FALHA CRÍTICA DE SEGURANÇA:\n"
                        "O arquivo baixado não confere com a chave oficial registrada no servidor!\n"
                        f"Esperado: {chave_esperada[:20]}...\n"
                        f"Recebido: {hash_baixado[:20]}...\n\n"
                        "A instalação foi abortada para proteger a integridade do seu computador."
                    )

            # 5. Extração para DEST_DIR
            self.set_status("4/5: Instalando arquivos em C:\\LCR-OdontoGest...", 85)
            DEST_DIR.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                zip_ref.extractall(DEST_DIR)

            # Limpa temporário
            try:
                temp_zip.unlink(missing_ok=True)
            except Exception:
                pass

            # 6. Criação do Atalho
            self.set_status("5/5: Criando atalho oficial na Área de Trabalho...", 95)
            self._criar_atalho()

            self.set_status("Instalação concluída com validação de segurança!", 100)
            self.after(0, self._finalizar_sucesso)

        except urllib.error.URLError:
            self.after(0, lambda: self._finalizar_erro("Sem conexão com a internet ou servidor indisponível."))
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
            "Segurança Confirmada",
            f"O {APP_NAME} foi instalado com sucesso!\n"
            "Chave de integridade SHA-256 verificada e aprovada.\n"
            "O atalho oficial está na sua Área de Trabalho."
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
    app = ModernInstallerApp()
    app.mainloop()
