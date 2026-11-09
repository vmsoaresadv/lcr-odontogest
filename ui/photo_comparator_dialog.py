"""
Comparador Visual de Fotos Antes e Depois
LCR OdontoGest - Dra. Lara Camila (CRO-BA 15247)
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from PIL import Image, ImageOps

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QLineEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QFont, QColor, QBrush, QPen, QTransform
)

from services.patient_service import list_attachments, add_attachment, get_patient
from services.report_service import exportar_html_para_pdf


class PhotoComparatorDialog(QDialog):
    """Diálogo Interativo de Comparação de Fotos Clínicas Antes e Depois com Rotação Livre."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.patient = get_patient(patient_id)

        self.path_antes: Optional[Path] = None
        self.path_depois: Optional[Path] = None

        self.img_antes_base: Optional[QImage] = None
        self.rotacao_antes: int = 0  # em graus: 0, 90, 180, 270

        self.img_depois_base: Optional[QImage] = None
        self.rotacao_depois: int = 0  # em graus: 0, 90, 180, 270

        self.setWindowTitle(f"Comparador Antes e Depois — {self.patient.get('nome', 'Paciente')}")
        self.resize(1060, 710)
        self.init_ui()
        self.carregar_anexos_disponiveis()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # 1. Barra Superior com Tratamento e Identificação
        top_bar = QFrame(self)
        top_bar.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        h_top = QHBoxLayout(top_bar)
        h_top.setContentsMargins(8, 4, 8, 4)
        h_top.setSpacing(12)

        v_tit = QVBoxLayout()
        v_tit.setSpacing(2)
        v_tit.addWidget(QLabel("Procedimento / Tratamento Realizado:"))
        self.txt_tratamento = QLineEdit("Clareamento Dental e Restaurações Estéticas")
        self.txt_tratamento.setStyleSheet("font-weight: 600; font-size: 13px; color: #0f766e;")
        v_tit.addWidget(self.txt_tratamento)
        h_top.addLayout(v_tit, stretch=3)

        v_data = QVBoxLayout()
        v_data.setSpacing(2)
        v_data.addWidget(QLabel("Data do Resultado:"))
        self.txt_data_resultado = QLineEdit(datetime.now().strftime("%d/%m/%Y"))
        self.txt_data_resultado.setFixedWidth(120)
        v_data.addWidget(self.txt_data_resultado)
        h_top.addLayout(v_data, stretch=1)

        main_layout.addWidget(top_bar)

        # 2. Área Central de Visualização Lado a Lado
        h_visualizadores = QHBoxLayout()
        h_visualizadores.setSpacing(16)

        # PAINEL DA ESQUERDA: ANTES
        box_antes = QFrame(self)
        box_antes.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")
        v_antes = QVBoxLayout(box_antes)
        v_antes.setContentsMargins(12, 10, 12, 10)
        v_antes.setSpacing(8)

        h_ctrl_antes = QHBoxLayout()
        lbl_tag_antes = QLabel("ANTES (Inicial)")
        lbl_tag_antes.setStyleSheet("""
            background-color: #fee2e2;
            color: #b91c1c;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 4px;
        """)
        h_ctrl_antes.addWidget(lbl_tag_antes)

        # Botão de Rotação Antes
        btn_rot_antes = QPushButton("↻ Girar 90°")
        btn_rot_antes.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #0f766e;
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_rot_antes.clicked.connect(self.girar_imagem_antes)
        h_ctrl_antes.addWidget(btn_rot_antes)

        h_ctrl_antes.addStretch()

        self.cmb_anexos_antes = QComboBox()
        self.cmb_anexos_antes.setMinimumWidth(150)
        self.cmb_anexos_antes.currentIndexChanged.connect(self.ao_selecionar_anexo_antes)
        h_ctrl_antes.addWidget(self.cmb_anexos_antes)

        btn_pick_antes = QPushButton("Buscar...")
        btn_pick_antes.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px;")
        btn_pick_antes.clicked.connect(self.escolher_arquivo_antes)
        h_ctrl_antes.addWidget(btn_pick_antes)

        v_antes.addLayout(h_ctrl_antes)

        # Imagem do Antes
        self.lbl_img_antes = QLabel("Nenhuma foto selecionada para o ANTES.\nClique em 'Buscar...' ou selecione nos anexos da ficha.", box_antes)
        self.lbl_img_antes.setAlignment(Qt.AlignCenter)
        self.lbl_img_antes.setStyleSheet("color: #94a3b8; background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; font-size: 12px; padding: 20px;")
        self.lbl_img_antes.setMinimumSize(380, 360)
        v_antes.addWidget(self.lbl_img_antes, stretch=1)

        h_visualizadores.addWidget(box_antes, stretch=1)

        # PAINEL DA DIREITA: DEPOIS
        box_depois = QFrame(self)
        box_depois.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")
        v_depois = QVBoxLayout(box_depois)
        v_depois.setContentsMargins(12, 10, 12, 10)
        v_depois.setSpacing(8)

        h_ctrl_depois = QHBoxLayout()
        lbl_tag_depois = QLabel("DEPOIS (Resultado)")
        lbl_tag_depois.setStyleSheet("""
            background-color: #dcfce7;
            color: #15803d;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 4px;
        """)
        h_ctrl_depois.addWidget(lbl_tag_depois)

        # Botão de Rotação Depois
        btn_rot_depois = QPushButton("↻ Girar 90°")
        btn_rot_depois.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #0f766e;
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        btn_rot_depois.clicked.connect(self.girar_imagem_depois)
        h_ctrl_depois.addWidget(btn_rot_depois)

        h_ctrl_depois.addStretch()

        self.cmb_anexos_depois = QComboBox()
        self.cmb_anexos_depois.setMinimumWidth(150)
        self.cmb_anexos_depois.currentIndexChanged.connect(self.ao_selecionar_anexo_depois)
        h_ctrl_depois.addWidget(self.cmb_anexos_depois)

        btn_pick_depois = QPushButton("Buscar...")
        btn_pick_depois.setStyleSheet("padding: 4px 10px; font-size: 11px; background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px;")
        btn_pick_depois.clicked.connect(self.escolher_arquivo_depois)
        h_ctrl_depois.addWidget(btn_pick_depois)

        v_depois.addLayout(h_ctrl_depois)

        # Imagem do Depois
        self.lbl_img_depois = QLabel("Nenhuma foto selecionada para o DEPOIS.\nClique em 'Buscar...' ou selecione nos anexos da ficha.", box_depois)
        self.lbl_img_depois.setAlignment(Qt.AlignCenter)
        self.lbl_img_depois.setStyleSheet("color: #94a3b8; background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; font-size: 12px; padding: 20px;")
        self.lbl_img_depois.setMinimumSize(380, 360)
        v_depois.addWidget(self.lbl_img_depois, stretch=1)

        h_visualizadores.addWidget(box_depois, stretch=1)
        main_layout.addLayout(h_visualizadores, stretch=1)

        # 3. Barra de Operações Inferior
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        lbl_info = QLabel("Use o botão '↻ Girar 90°' para ajustar a orientação de fotos de celular.")
        lbl_info.setStyleSheet("color: #64748b; font-size: 12px;")
        bottom_bar.addWidget(lbl_info)
        bottom_bar.addStretch()

        btn_salvar_anexo = QPushButton("Salvar Comparativo nos Anexos")
        btn_salvar_anexo.setStyleSheet("""
            QPushButton {
                background-color: #0f766e;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #115e59;
            }
        """)
        btn_salvar_anexo.clicked.connect(self.salvar_como_anexo)
        bottom_bar.addWidget(btn_salvar_anexo)

        btn_exportar_pdf = QPushButton("Exportar Comparativo em PDF")
        btn_exportar_pdf.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_exportar_pdf.clicked.connect(self.exportar_pdf)
        bottom_bar.addWidget(btn_exportar_pdf)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("padding: 8px 16px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
        btn_fechar.clicked.connect(self.close)
        bottom_bar.addWidget(btn_fechar)

        main_layout.addLayout(bottom_bar)

    def carregar_anexos_disponiveis(self):
        anexos = list_attachments(self.patient_id)
        exts_img = [".png", ".jpg", ".jpeg", ".bmp", ".webp"]

        self.cmb_anexos_antes.clear()
        self.cmb_anexos_depois.clear()

        self.cmb_anexos_antes.addItem("Anexos da Ficha...", "")
        self.cmb_anexos_depois.addItem("Anexos da Ficha...", "")

        for a in anexos:
            nome = a["nome_arquivo"]
            caminho = a["caminho_arquivo"]
            if any(nome.lower().endswith(ext) for ext in exts_img):
                self.cmb_anexos_antes.addItem(nome, caminho)
                self.cmb_anexos_depois.addItem(nome, caminho)

    def ao_selecionar_anexo_antes(self, idx: int):
        caminho = self.cmb_anexos_antes.currentData()
        if caminho and Path(caminho).exists():
            self.definir_imagem_antes(Path(caminho))

    def ao_selecionar_anexo_depois(self, idx: int):
        caminho = self.cmb_anexos_depois.currentData()
        if caminho and Path(caminho).exists():
            self.definir_imagem_depois(Path(caminho))

    def escolher_arquivo_antes(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem do Antes", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if arquivo:
            self.definir_imagem_antes(Path(arquivo))

    def escolher_arquivo_depois(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem do Depois", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if arquivo:
            self.definir_imagem_depois(Path(arquivo))

    def _carregar_qimage_com_exif(self, path: Path) -> Optional[QImage]:
        """Carrega a imagem corrigindo automaticamente a orientação EXIF de celulares."""
        try:
            with Image.open(str(path)) as pil_img:
                pil_img = ImageOps.exif_transpose(pil_img)
                pil_img = pil_img.convert("RGBA")
                data = pil_img.tobytes("raw", "RGBA")
                qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888).copy()
                return qimg
        except Exception:
            qimg = QImage(str(path))
            return qimg if not qimg.isNull() else None

    def definir_imagem_antes(self, path: Path):
        self.path_antes = path
        self.rotacao_antes = 0
        self.img_antes_base = self._carregar_qimage_com_exif(path)
        self.atualizar_preview_antes()

    def definir_imagem_depois(self, path: Path):
        self.path_depois = path
        self.rotacao_depois = 0
        self.img_depois_base = self._carregar_qimage_com_exif(path)
        self.atualizar_preview_depois()

    def girar_imagem_antes(self):
        if not self.img_antes_base:
            return
        self.rotacao_antes = (self.rotacao_antes + 90) % 360
        self.atualizar_preview_antes()

    def girar_imagem_depois(self):
        if not self.img_depois_base:
            return
        self.rotacao_depois = (self.rotacao_depois + 90) % 360
        self.atualizar_preview_depois()

    def _obter_imagem_rotacionada(self, qimg: QImage, angulo: int) -> QImage:
        if angulo % 360 == 0:
            return qimg
        transform = QTransform().rotate(angulo)
        return qimg.transformed(transform, Qt.SmoothTransformation)

    def atualizar_preview_antes(self):
        if not self.img_antes_base:
            return
        img_rot = self._obter_imagem_rotacionada(self.img_antes_base, self.rotacao_antes)
        pix = QPixmap.fromImage(img_rot)
        scaled = pix.scaled(self.lbl_img_antes.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_img_antes.setPixmap(scaled)
        self.lbl_img_antes.setText("")

    def atualizar_preview_depois(self):
        if not self.img_depois_base:
            return
        img_rot = self._obter_imagem_rotacionada(self.img_depois_base, self.rotacao_depois)
        pix = QPixmap.fromImage(img_rot)
        scaled = pix.scaled(self.lbl_img_depois.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_img_depois.setPixmap(scaled)
        self.lbl_img_depois.setText("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.img_antes_base:
            self.atualizar_preview_antes()
        if self.img_depois_base:
            self.atualizar_preview_depois()

    def gerar_imagem_composta(self) -> Optional[QImage]:
        """Cria uma imagem composta de alta resolução com cabeçalho oficial e o Antes e Depois."""
        if not self.img_antes_base or not self.img_depois_base:
            QMessageBox.warning(self, "Aviso", "Selecione as fotos do Antes e do Depois para gerar o comparativo.")
            return None

        img_a = self._obter_imagem_rotacionada(self.img_antes_base, self.rotacao_antes)
        img_d = self._obter_imagem_rotacionada(self.img_depois_base, self.rotacao_depois)

        # Dimensões da imagem final
        w_quadro = 600
        h_quadro = 500
        w_total = (w_quadro * 2) + 60
        h_total = h_quadro + 180

        resultado = QImage(w_total, h_total, QImage.Format_ARGB32)
        resultado.fill(QColor("#ffffff"))

        painter = QPainter(resultado)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Cabeçalho da Clínica
        painter.setPen(QColor("#0f766e"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(QRectF(30, 20, w_total - 60, 30), Qt.AlignLeft, "LCR CLÍNICA ODONTOLÓGICA")

        painter.setPen(QColor("#475569"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Normal))
        painter.drawText(QRectF(30, 52, w_total - 60, 22), Qt.AlignLeft, "Dra. Lara Camila • CRO-BA 15247 • Irecê/BA")

        # Dados do Paciente e Procedimento
        tratamento = self.txt_tratamento.text().strip() or "Procedimento Clínico"
        data_str = self.txt_data_resultado.text().strip() or datetime.now().strftime("%d/%m/%Y")
        paciente_nome = self.patient.get("nome", "Paciente")

        painter.setPen(QColor("#1e293b"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(QRectF(30, 84, w_total - 60, 24), Qt.AlignLeft, f"Evolução Clínica: {tratamento}")

        painter.setFont(QFont("Segoe UI", 10, QFont.Normal))
        painter.setPen(QColor("#64748b"))
        painter.drawText(QRectF(30, 110, w_total - 60, 20), Qt.AlignLeft, f"Paciente: {paciente_nome}   |   Data do Registro: {data_str}")

        # Linha divisória suave
        painter.setPen(QPen(QColor("#e2e8f0"), 1.5))
        painter.drawLine(30, 138, w_total - 30, 138)

        # Desenhar Quadros de Fotos
        y_fotos = 150
        x_antes = 30
        x_depois = 30 + w_quadro + 20

        # Foto Antes
        scaled_a = img_a.scaled(w_quadro, h_quadro, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_ax = (w_quadro - scaled_a.width()) // 2
        offset_ay = (h_quadro - scaled_a.height()) // 2
        painter.drawImage(x_antes + offset_ax, y_fotos + offset_ay, scaled_a)

        # Tag Antes
        painter.setBrush(QBrush(QColor("#b91c1c")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(x_antes + 10, y_fotos + 10, 90, 28, 4, 4)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(x_antes + 10, y_fotos + 10, 90, 28), Qt.AlignCenter, "ANTES")

        # Foto Depois
        scaled_d = img_d.scaled(w_quadro, h_quadro, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_dx = (w_quadro - scaled_d.width()) // 2
        offset_dy = (h_quadro - scaled_d.height()) // 2
        painter.drawImage(x_depois + offset_dx, y_fotos + offset_dy, scaled_d)

        # Tag Depois
        painter.setBrush(QBrush(QColor("#15803d")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(x_depois + 10, y_fotos + 10, 90, 28, 4, 4)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(x_depois + 10, y_fotos + 10, 90, 28), Qt.AlignCenter, "DEPOIS")

        painter.end()
        return resultado

    def salvar_como_anexo(self):
        img = self.gerar_imagem_composta()
        if not img:
            return

        import tempfile
        hoje_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"comparativo_antes_depois_{hoje_slug}.png"

        img.save(str(temp_file), "PNG")

        ok, msg = add_attachment(
            patient_id=self.patient_id,
            source_file_path=str(temp_file),
            user_id=self.current_user["id"],
            user_nome=self.current_user["nome"]
        )

        try:
            temp_file.unlink()
        except Exception:
            pass

        if ok:
            QMessageBox.information(
                self, "Comparativo Salvo",
                "A imagem comparativa oficial foi gerada e arquivada nos Anexos da Ficha do Paciente com sucesso!"
            )
            self.carregar_anexos_disponiveis()
        else:
            QMessageBox.critical(self, "Erro", msg)

    def exportar_pdf(self):
        img = self.gerar_imagem_composta()
        if not img:
            return

        import tempfile
        temp_img = Path(tempfile.gettempdir()) / f"comp_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        img.save(str(temp_img), "PNG")

        dest, _ = QFileDialog.getSaveFileName(
            self, "Salvar Comparativo em PDF",
            f"Comparativo_Antes_Depois_{self.patient.get('nome', 'Paciente').replace(' ', '_')}.pdf",
            "Documentos PDF (*.pdf)"
        )
        if not dest:
            return

        uri_img = temp_img.as_uri()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 10px;
                    text-align: center;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <img src="{uri_img}" />
        </body>
        </html>
        """

        ok = exportar_html_para_pdf(html, dest)
        try:
            temp_img.unlink()
        except Exception:
            pass

        if ok:
            QMessageBox.information(self, "PDF Gerado", f"Comparativo exportado em PDF com sucesso:\n{dest}")
            import os
            try:
                os.startfile(dest)
            except Exception:
                pass
        else:
            QMessageBox.critical(self, "Erro", "Falha ao gerar o documento PDF do comparativo.")
