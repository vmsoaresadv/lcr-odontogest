import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QFrame, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon

from services.updater_service import verificar_atualizacao, criar_script_substituicao_windows
from version import __version__, APP_NAME

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo_clean.png"
ICO_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico"


class CheckUpdateThread(QThread):
    finished_check = Signal(bool, object, str)

    def run(self):
        tem_update, info, msg = verificar_atualizacao()
        self.finished_check.emit(tem_update, info, msg)


class DownloadUpdateThread(QThread):
    progress_signal = Signal(int)
    finished_download = Signal(bool, str)

    def __init__(self, download_url: str, destino_path: str):
        super().__init__()
        self.download_url = download_url
        self.destino_path = destino_path

    def run(self):
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"{APP_NAME}-Updater/{__version__}"}
            )
            with urllib.request.urlopen(req) as resp, open(self.destino_path, "wb") as out_file:
                total_size = resp.length or 0
                downloaded = 0
                bloco = 1024 * 64
                while True:
                    buffer = resp.read(bloco)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 100)
                        self.progress_signal.emit(pct)

            self.finished_download.emit(True, self.destino_path)
        except Exception as e:
            self.finished_download.emit(False, str(e))


class UpdaterDialog(QDialog):
    """Diálogo visual de verificação e aplicação de atualizações do LCR OdontoGest."""
    def __init__(self, silensioso: bool = False, parent=None):
        super().__init__(parent)
        self.silencioso = silensioso
        self.setWindowTitle(f"Atualizações - {APP_NAME}")
        self.setFixedSize(520, 420)

        icon_to_use = ICO_PATH if ICO_PATH.exists() else LOGO_PATH
        if icon_to_use.exists():
            self.setWindowIcon(QIcon(str(icon_to_use)))

        self.update_info: Optional[dict] = None
        self.check_thread: Optional[CheckUpdateThread] = None
        self.download_thread: Optional[DownloadUpdateThread] = None

        self.init_ui()
        self.iniciar_verificacao()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Cabeçalho
        header_card = QFrame(self)
        header_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(10, 8, 10, 8)

        lbl_ico = QLabel("🔄")
        lbl_ico.setStyleSheet("font-size: 26px;")
        h_layout.addWidget(lbl_ico)

        txt_info = QVBoxLayout()
        self.lbl_titulo = QLabel(f"Verificando atualizações do {APP_NAME}...")
        self.lbl_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: #0f172a;")
        self.lbl_subtitulo = QLabel(f"Versão atual instalada: v{__version__}")
        self.lbl_subtitulo.setStyleSheet("font-size: 12px; color: #64748b;")
        txt_info.addWidget(self.lbl_titulo)
        txt_info.addWidget(self.lbl_subtitulo)
        h_layout.addLayout(txt_info)
        h_layout.addStretch()

        layout.addWidget(header_card)

        # Status / Mensagem
        self.lbl_status = QLabel("Consultando servidores do GitHub...")
        self.lbl_status.setStyleSheet("color: #475569; font-size: 13px;")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        # Barra de Progresso
        self.progresso = QProgressBar(self)
        self.progresso.setRange(0, 100)
        self.progresso.setValue(0)
        self.progresso.setTextVisible(True)
        self.progresso.setStyleSheet("""
            QProgressBar {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                height: 22px;
                color: #0f172a;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0d9488;
                border-radius: 5px;
            }
        """)
        self.progresso.setVisible(False)
        layout.addWidget(self.progresso)

        # Caixa com Notas da Versão (Changelog)
        self.lbl_changelog = QLabel("O que há de novo nesta versão:")
        self.lbl_changelog.setStyleSheet("font-weight: bold; font-size: 12px; color: #334155;")
        self.lbl_changelog.setVisible(False)
        layout.addWidget(self.lbl_changelog)

        self.txt_notas = QTextEdit(self)
        self.txt_notas.setReadOnly(True)
        self.txt_notas.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: #1e293b;
            }
        """)
        self.txt_notas.setVisible(False)
        layout.addWidget(self.txt_notas)

        layout.addStretch()

        # Botões de Ação
        self.btn_box = QHBoxLayout()
        self.btn_cancelar = QPushButton("Fechar")
        self.btn_cancelar.setStyleSheet("""
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        """)
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_box.addWidget(self.btn_cancelar)

        self.btn_atualizar = QPushButton("⚡ Atualizar Agora")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #0d9488;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0f766e;
            }
        """)
        self.btn_atualizar.setVisible(False)
        self.btn_atualizar.clicked.connect(self.iniciar_download_atualizacao)
        self.btn_box.addWidget(self.btn_atualizar)

        layout.addLayout(self.btn_box)

    def iniciar_verificacao(self):
        self.check_thread = CheckUpdateThread()
        self.check_thread.finished_check.connect(self.ao_finalizar_verificacao)
        self.check_thread.start()

    def ao_finalizar_verificacao(self, tem_update: bool, info: Optional[dict], msg: str):
        if tem_update and info:
            self.update_info = info
            self.lbl_titulo.setText(f"🎉 Nova versão {info['versao_tag']} disponível!")
            self.lbl_titulo.setStyleSheet("font-weight: bold; font-size: 15px; color: #0d9488;")
            self.lbl_status.setText("Uma nova versão do sistema está pronta para download e instalação automática.")
            self.lbl_changelog.setVisible(True)
            self.txt_notas.setVisible(True)
            self.txt_notas.setPlainText(info.get("corpo", "Melhorias gerais no sistema."))
            self.btn_atualizar.setVisible(True)
            self.btn_cancelar.setText("Lembrar Mais Tarde")
            if self.silencioso:
                self.show()
        else:
            if self.silencioso:
                self.close()
                return
            self.lbl_titulo.setText(f"✅ {APP_NAME} está atualizado")
            self.lbl_status.setText(msg)

    def iniciar_download_atualizacao(self):
        if not self.update_info or not self.update_info.get("download_url"):
            # Se não houver link direto do asset executável, abre o link da release no navegador
            url = self.update_info.get("html_url", "")
            QMessageBox.information(
                self,
                "Download Manual",
                f"A página da versão oficial será aberta no seu navegador para download:\n\n{url}"
            )
            import webbrowser
            if url:
                webbrowser.open(url)
            self.accept()
            return

        self.btn_atualizar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self.progresso.setVisible(True)
        self.lbl_status.setText("Baixando atualização... Por favor, aguarde.")

        url = self.update_info["download_url"]
        temp_dir = Path(tempfile.gettempdir())
        file_name = self.update_info.get("file_name") or f"LCR-OdontoGest-{self.update_info['versao_tag']}.exe"
        destino_path = str(temp_dir / file_name)

        self.download_thread = DownloadUpdateThread(url, destino_path)
        self.download_thread.progress_signal.connect(self.progresso.setValue)
        self.download_thread.finished_download.connect(self.ao_finalizar_download)
        self.download_thread.start()

    def ao_finalizar_download(self, sucesso: bool, caminho_ou_erro: str):
        if sucesso:
            self.progresso.setValue(100)
            self.lbl_status.setText("Download concluído! Preparando reinicialização...")

            # Identifica executável atual
            exe_atual = sys.executable
            if exe_atual.lower().endswith("python.exe"):
                # Modo desenvolvimento
                QMessageBox.information(
                    self,
                    "Atualização Concluída",
                    f"O pacote foi baixado com sucesso em:\n{caminho_ou_erro}\n\n"
                    "(Em ambiente de desenvolvimento .py, o sistema não reinicia o interpretador automaticamente)."
                )
                self.accept()
                return

            # Modo Executável Windows (.exe compilado)
            script_bat = criar_script_substituicao_windows(caminho_ou_erro, exe_atual)
            subprocess.Popen([str(script_bat)], shell=True)
            QApplication.quit()
        else:
            QMessageBox.critical(self, "Falha no Download", f"Não foi possível concluir o download:\n\n{caminho_ou_erro}")
            self.btn_atualizar.setEnabled(True)
            self.btn_cancelar.setEnabled(True)
