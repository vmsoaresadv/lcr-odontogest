"""
Módulo de Interface Gráfica da Fase 8: Receituários e Atestados Odontológicos Inteligentes
Clínica Odontológica Dra. Lara Camila (CRO-BA 15247)
"""

import os
import json
import tempfile
import webbrowser
from datetime import datetime
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QMessageBox, QFrame, QSplitter, QFileDialog, QScrollArea,
    QGroupBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QMarginsF, QUrl
from PySide6.QtGui import QFont, QColor, QTextDocument, QPageSize, QPageLayout, QDesktopServices
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from services.clinical_docs_service import (
    list_prescription_templates, get_prescription_template,
    create_prescription_template, update_prescription_template, delete_prescription_template,
    list_certificate_templates, get_certificate_template,
    create_certificate_template, update_certificate_template, delete_certificate_template,
    issue_clinical_document, list_patient_issued_documents, get_issued_document, delete_issued_document,
    gerar_html_receituario, gerar_html_atestado
)

DOCS_STYLE = """
QDialog {
    background-color: #f8fafc;
    font-family: 'Segoe UI', sans-serif;
}
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #1e293b;
}
QLabel {
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
}
QGroupBox {
    font-size: 13px;
    font-weight: 700;
    color: #0f766e;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #ffffff;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 28px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #0f766e;
    background-color: #ffffff;
}
QSpinBox {
    min-width: 100px;
    min-height: 32px;
    padding-right: 24px;
    font-weight: bold;
    color: #0f766e;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #e2e8f0;
}
QComboBox {
    min-height: 32px;
    padding-right: 20px;
}
QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    gridline-color: #f1f5f9;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #cbd5e1;
}
QPushButton#primaryBtn {
    background-color: #0f766e;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 18px;
    border-radius: 6px;
    border: none;
    min-height: 22px;
}
QPushButton#primaryBtn:hover {
    background-color: #115e59;
}
QPushButton#secondaryBtn {
    background-color: #ffffff;
    color: #334155;
    font-weight: 600;
    padding: 7px 15px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    min-height: 22px;
}
QPushButton#secondaryBtn:hover {
    background-color: #f1f5f9;
}
QPushButton#dangerBtn {
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #fca5a5;
    min-height: 20px;
}
QPushButton#dangerBtn:hover {
    background-color: #fecaca;
}
"""


class ClinicalDocPreviewDialog(QDialog):
    """Diálogo de visualização do documento timbrado com opções de Impressão e PDF."""
    def __init__(self, doc_data: dict, html_content: str, parent=None):
        super().__init__(parent)
        self.doc_data = doc_data
        self.html_content = html_content
        self.setWindowTitle(f"Visualizar Documento Clínico - {doc_data.get('titulo', 'Documento')}")
        self.resize(850, 780)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Barra superior com ações
        top_bar = QHBoxLayout()
        lbl_tipo = QLabel(f"📄 {self.doc_data.get('tipo_documento', 'Documento')} • {self.doc_data.get('titulo', '')}")
        lbl_tipo.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        top_bar.addWidget(lbl_tipo)
        top_bar.addStretch()

        btn_pdf = QPushButton("📥 Exportar PDF")
        btn_pdf.setObjectName("primaryBtn")
        btn_pdf.clicked.connect(self.exportar_pdf)
        top_bar.addWidget(btn_pdf)

        btn_imprimir = QPushButton("🖨️ Imprimir...")
        btn_imprimir.setObjectName("secondaryBtn")
        btn_imprimir.clicked.connect(self.imprimir_documento)
        top_bar.addWidget(btn_imprimir)

        btn_browser = QPushButton("🌐 Abrir no Navegador")
        btn_browser.setObjectName("secondaryBtn")
        btn_browser.clicked.connect(self.abrir_no_navegador)
        top_bar.addWidget(btn_browser)

        layout.addLayout(top_bar)

        # Visualizador de texto rico (renderiza o HTML timbrado da clínica)
        self.viewer = QTextEdit(self)
        self.viewer.setReadOnly(True)
        self.viewer.setHtml(self.html_content)
        self.viewer.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        layout.addWidget(self.viewer)

        # Barra inferior
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("secondaryBtn")
        btn_fechar.clicked.connect(self.accept)
        btn_box.addWidget(btn_fechar)
        layout.addLayout(btn_box)

    def exportar_pdf(self):
        """Exporta o documento timbrado diretamente para PDF em formato A4."""
        nome_sugerido = f"{self.doc_data.get('tipo_documento', 'Documento')}_{self.doc_data.get('paciente_nome', 'Paciente').replace(' ', '_')}_{datetime.now().strftime('%d%m%Y')}.pdf"
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar Documento em PDF", nome_sugerido, "Arquivos PDF (*.pdf)"
        )
        if not caminho:
            return

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(caminho)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

            doc = QTextDocument()
            doc.setHtml(self.html_content)
            doc.print_(printer)

            QMessageBox.information(
                self, "PDF Gerado",
                f"Documento timbrado exportado com sucesso para:\n{caminho}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Gerar PDF", f"Falha ao gerar arquivo PDF:\n{str(e)}")

    def imprimir_documento(self):
        """Abre o diálogo de impressão do Windows."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(self.html_content)
            doc.print_(printer)

    def abrir_no_navegador(self):
        """Cria um arquivo HTML temporário timbrado e abre no navegador padrão."""
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as f:
                f.write(self.html_content)
                temp_path = f.name
            webbrowser.open(f"file:///{temp_path.replace(os.sep, '/')}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir no navegador:\n{e}")


# ==============================================================================
# DIÁLOGO DE PRESCRIÇÃO (RECEITUÁRIO INTELIGENTE)
# ==============================================================================
class PrescriptionFormDialog(QDialog):
    """Diálogo completo de elaboração e emissão de receita com suporte a múltiplos medicamentos."""
    def __init__(self, patient_id: int, patient_nome: str, patient_cpf: str, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient_nome = patient_nome
        self.patient_cpf = patient_cpf
        self.current_user = current_user
        self.medicamentos_prescritos: List[Dict[str, str]] = []

        self.setWindowTitle(f"Emitir Receituário - {patient_nome}")
        self.resize(900, 720)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Cabeçalho
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header_frame)
        lbl_info = QLabel(f"💊 <b>Receituário Odontológico</b> &nbsp;|&nbsp; Paciente: <b>{self.patient_nome}</b> (CPF: {self.patient_cpf or 'Não informado'})")
        lbl_info.setStyleSheet("color: #0f766e; font-size: 14px;")
        h_layout.addWidget(lbl_info)
        h_layout.addStretch()
        layout.addWidget(header_frame)

        # Título da Receita
        tit_box = QHBoxLayout()
        lbl_tit = QLabel("Título / Finalidade:")
        self.txt_titulo = QLineEdit("Receituário Odontológico Pós-Procedimento")
        tit_box.addWidget(lbl_tit)
        tit_box.addWidget(self.txt_titulo, 1)
        layout.addLayout(tit_box)

        # Seletor de medicamentos do catálogo
        catalogo_box = QGroupBox("Inserir Medicamento do Catálogo Rápido")
        catalogo_layout = QHBoxLayout(catalogo_box)
        self.combo_catalogo = QComboBox()
        self.carregar_catalogo()
        catalogo_layout.addWidget(self.combo_catalogo, 1)

        btn_add_cat = QPushButton("+ Adicionar à Receita")
        btn_add_cat.setObjectName("primaryBtn")
        btn_add_cat.clicked.connect(self.adicionar_do_catalogo)
        catalogo_layout.addWidget(btn_add_cat)

        btn_add_manual = QPushButton("+ Medicamento Avulso")
        btn_add_manual.setObjectName("secondaryBtn")
        btn_add_manual.clicked.connect(self.adicionar_avulso)
        catalogo_layout.addWidget(btn_add_manual)

        btn_gerenciar_cat = QPushButton("⚙️ Modelos")
        btn_gerenciar_cat.setObjectName("secondaryBtn")
        btn_gerenciar_cat.clicked.connect(self.abrir_gerenciador_catalogo)
        catalogo_layout.addWidget(btn_gerenciar_cat)
        layout.addWidget(catalogo_box)

        # Tabela de medicamentos prescritos
        layout.addWidget(QLabel("Medicamentos da Receita:"))
        self.table_meds = QTableWidget()
        self.table_meds.setColumnCount(4)
        self.table_meds.setHorizontalHeaderLabels(["Medicamento", "Concentração / Forma", "Posologia Detalhada", "Ações"])
        self.table_meds.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_meds.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_meds.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_meds.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_meds.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_meds.setAlternatingRowColors(True)
        layout.addWidget(self.table_meds)

        # Orientações gerais
        layout.addWidget(QLabel("Orientações Gerais / Recomendações Pós-Operatórias:"))
        self.txt_orientacoes = QTextEdit()
        self.txt_orientacoes.setMaximumHeight(80)
        self.txt_orientacoes.setPlaceholderText("Ex: Repouso relativo, evitar esforço físico, dieta pastosa e fria nas primeiras 24 horas...")
        layout.addWidget(self.txt_orientacoes)

        # Botões inferiores
        btn_bar = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancelar)

        btn_bar.addStretch()

        btn_emitir = QPushButton("💾 Salvar e Gerar Receituário Timbrado")
        btn_emitir.setObjectName("primaryBtn")
        btn_emitir.clicked.connect(self.salvar_e_emitir)
        btn_bar.addWidget(btn_emitir)

        layout.addLayout(btn_bar)

    def carregar_catalogo(self):
        """Carrega lista de medicamentos padrão no ComboBox."""
        self.combo_catalogo.clear()
        templates = list_prescription_templates()
        for t in templates:
            label = f"[{t['categoria']}] {t['nome_medicamento']} - {t['concentracao_forma'] or ''}"
            self.combo_catalogo.addItem(label, t)

    def adicionar_do_catalogo(self):
        """Adiciona o medicamento selecionado à lista da receita."""
        data = self.combo_catalogo.currentData()
        if not data:
            return
        item = {
            "nome": data["nome_medicamento"],
            "concentracao": data["concentracao_forma"] or "",
            "posologia": data["posologia"] or "",
            "orientacoes": data["orientacoes"] or ""
        }
        self.medicamentos_prescritos.append(item)
        self.atualizar_tabela_meds()

    def adicionar_avulso(self):
        """Abre diálogo para adicionar medicamento não cadastrado."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Adicionar Medicamento Avulso")
        dlg.resize(460, 320)
        dlg.setStyleSheet(DOCS_STYLE)
        l = QVBoxLayout(dlg)

        l.addWidget(QLabel("Nome do Medicamento (*):"))
        txt_nome = QLineEdit()
        l.addWidget(txt_nome)

        l.addWidget(QLabel("Concentração / Apresentação:"))
        txt_conc = QLineEdit()
        txt_conc.setPlaceholderText("Ex: 500mg (Comprimidos)")
        l.addWidget(txt_conc)

        l.addWidget(QLabel("Posologia Detalhada (*):"))
        txt_poso = QTextEdit()
        txt_poso.setPlaceholderText("Ex: Tomar 1 comprimido de 8 em 8 horas por 5 dias.")
        l.addWidget(txt_poso)

        btn_box = QHBoxLayout()
        b_canc = QPushButton("Cancelar")
        b_canc.setObjectName("secondaryBtn")
        b_canc.clicked.connect(dlg.reject)
        b_salv = QPushButton("Adicionar")
        b_salv.setObjectName("primaryBtn")

        def confirmar():
            if not txt_nome.text().strip() or not txt_poso.toPlainText().strip():
                QMessageBox.warning(dlg, "Aviso", "Preencha o nome e a posologia do medicamento.")
                return
            self.medicamentos_prescritos.append({
                "nome": txt_nome.text().strip(),
                "concentracao": txt_conc.text().strip(),
                "posologia": txt_poso.toPlainText().strip(),
                "orientacoes": ""
            })
            self.atualizar_tabela_meds()
            dlg.accept()

        b_salv.clicked.connect(confirmar)
        btn_box.addWidget(b_canc)
        btn_box.addStretch()
        btn_box.addWidget(b_salv)
        l.addLayout(btn_box)
        dlg.exec()

    def atualizar_tabela_meds(self):
        """Atualiza a tabela com os itens prescritos."""
        self.table_meds.setRowCount(len(self.medicamentos_prescritos))
        for r_idx, m in enumerate(self.medicamentos_prescritos):
            self.table_meds.setItem(r_idx, 0, QTableWidgetItem(m["nome"]))
            self.table_meds.setItem(r_idx, 1, QTableWidgetItem(m["concentracao"]))
            self.table_meds.setItem(r_idx, 2, QTableWidgetItem(m["posologia"]))

            btn_rem = QPushButton("Remover")
            btn_rem.setObjectName("dangerBtn")
            btn_rem.clicked.connect(lambda _, idx=r_idx: self.remover_med(idx))
            self.table_meds.setCellWidget(r_idx, 3, btn_rem)

    def remover_med(self, idx: int):
        if 0 <= idx < len(self.medicamentos_prescritos):
            self.medicamentos_prescritos.pop(idx)
            self.atualizar_tabela_meds()

    def abrir_gerenciador_catalogo(self):
        dlg = ManagePrescriptionTemplatesDialog(self.current_user, self)
        dlg.exec()
        self.carregar_catalogo()

    def salvar_e_emitir(self):
        if not self.medicamentos_prescritos:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um medicamento à receita.")
            return

        titulo = self.txt_titulo.text().strip() or "Receituário Odontológico"
        orientacoes = self.txt_orientacoes.toPlainText().strip()

        conteudo = {
            "medicamentos": self.medicamentos_prescritos,
            "orientacoes_gerais": orientacoes
        }

        ok, msg, doc_id = issue_clinical_document(
            tipo_documento="Receituario",
            patient_id=self.patient_id,
            titulo=titulo,
            conteudo=conteudo,
            observacoes=orientacoes,
            user_id=self.current_user.get("id"),
            usuario_nome=self.current_user.get("nome", "Dra. Lara Camila")
        )

        if not ok:
            QMessageBox.critical(self, "Erro", msg)
            return

        # Busca documento salvo e abre visualizador com opção de PDF/Imprimir
        doc = get_issued_document(doc_id)
        html = gerar_html_receituario(doc)
        prev = ClinicalDocPreviewDialog(doc, html, self)
        prev.exec()

        self.accept()


# ==============================================================================
# DIÁLOGO DE ATESTADOS E DECLARAÇÕES INTELIGENTES
# ==============================================================================
class CertificateFormDialog(QDialog):
    """Diálogo completo de emissão de atestados e declarações com modelos e substituição dinâmica de tags."""
    def __init__(self, patient_id: int, patient_nome: str, patient_cpf: str, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.patient_nome = patient_nome
        self.patient_cpf = patient_cpf
        self.current_user = current_user

        self.setWindowTitle(f"Emitir Atestado / Declaração - {patient_nome}")
        self.resize(850, 680)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Cabeçalho
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header_frame)
        lbl_info = QLabel(f"📋 <b>Atestado / Declaração Odontológica</b> &nbsp;|&nbsp; Paciente: <b>{self.patient_nome}</b> (CPF: {self.patient_cpf or 'Não informado'})")
        lbl_info.setStyleSheet("color: #0f766e; font-size: 14px;")
        h_layout.addWidget(lbl_info)
        h_layout.addStretch()
        layout.addWidget(header_frame)

        # Seleção de Modelo
        sel_box = QGroupBox("Modelo Pré-Configurado")
        sel_layout = QHBoxLayout(sel_box)
        self.combo_modelos = QComboBox()
        self.carregar_modelos()
        self.combo_modelos.currentIndexChanged.connect(self.ao_mudar_modelo)
        sel_layout.addWidget(self.combo_modelos, 1)

        btn_gerenciar_modelos = QPushButton("⚙️ Gerenciar Modelos")
        btn_gerenciar_modelos.setObjectName("secondaryBtn")
        btn_gerenciar_modelos.clicked.connect(self.abrir_gerenciador_modelos)
        sel_layout.addWidget(btn_gerenciar_modelos)
        layout.addWidget(sel_box)

        # Campos de controle
        grid_params = QHBoxLayout()

        lbl_tipo = QLabel("Tipo:")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Atestado", "Declaracao", "Outro"])
        grid_params.addWidget(lbl_tipo)
        grid_params.addWidget(self.combo_tipo)

        lbl_dias = QLabel("Dias de Repouso:")
        self.spin_dias = QSpinBox()
        self.spin_dias.setRange(0, 90)
        self.spin_dias.setValue(1)
        self.spin_dias.valueChanged.connect(self.atualizar_texto_com_dias)
        grid_params.addWidget(lbl_dias)
        grid_params.addWidget(self.spin_dias)

        lbl_cid = QLabel("CID-10 (Opcional):")
        self.txt_cid = QLineEdit()
        self.txt_cid.setPlaceholderText("Ex: K08.1, K04.0 (a pedido do paciente)")
        grid_params.addWidget(lbl_cid)
        grid_params.addWidget(self.txt_cid)

        layout.addLayout(grid_params)

        # Título do documento
        tit_box = QHBoxLayout()
        tit_box.addWidget(QLabel("Título do Documento:"))
        self.txt_titulo = QLineEdit("Atestado Odontológico de Repouso")
        tit_box.addWidget(self.txt_titulo, 1)
        layout.addLayout(tit_box)

        # Texto do Atestado
        layout.addWidget(QLabel("Texto do Atestado / Declaração (Editável livremente):"))
        self.txt_conteudo = QTextEdit()
        self.txt_conteudo.setStyleSheet("font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.txt_conteudo, 1)

        # Observações internas / adicionais
        layout.addWidget(QLabel("Observações Adicionais (Opcional):"))
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Observações adicionais para constar no documento ou prontuário...")
        layout.addWidget(self.txt_obs)

        # Dispara primeiro preenchimento
        self.ao_mudar_modelo()

        # Botões inferiores
        btn_bar = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secondaryBtn")
        btn_cancelar.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancelar)

        btn_bar.addStretch()

        btn_emitir = QPushButton("💾 Salvar e Gerar Atestado Timbrado")
        btn_emitir.setObjectName("primaryBtn")
        btn_emitir.clicked.connect(self.salvar_e_emitir)
        btn_bar.addWidget(btn_emitir)

        layout.addLayout(btn_bar)

    def carregar_modelos(self):
        self.combo_modelos.clear()
        templates = list_certificate_templates()
        for t in templates:
            self.combo_modelos.addItem(f"[{t['tipo']}] {t['titulo']}", t)

    def ao_mudar_modelo(self):
        template = self.combo_modelos.currentData()
        if not template:
            return

        self.txt_titulo.setText(template["titulo"])
        self.combo_tipo.setCurrentText(template["tipo"])
        self.spin_dias.setValue(template.get("dias_repouso", 1))

        # Renderiza texto substituindo variáveis
        texto = template["texto_padrao"]
        hoje = datetime.now().strftime("%d/%m/%Y")
        hora = datetime.now().strftime("%H:%M")
        texto = texto.replace("{paciente}", self.patient_nome)
        texto = texto.replace("{cpf}", self.patient_cpf or "não informado")
        texto = texto.replace("{data}", hoje)
        texto = texto.replace("{dias}", str(self.spin_dias.value()))
        texto = texto.replace("{horario_inicio}", hora)
        texto = texto.replace("{horario_fim}", datetime.now().strftime("%H:%M"))
        self.txt_conteudo.setPlainText(texto)

    def atualizar_texto_com_dias(self, dias: int):
        template = self.combo_modelos.currentData()
        if template and "{dias}" in template["texto_padrao"]:
            # Atualiza apenas se for baseado no modelo padrão
            self.ao_mudar_modelo()

    def abrir_gerenciador_modelos(self):
        dlg = ManageCertificateTemplatesDialog(self.current_user, self)
        dlg.exec()
        self.carregar_modelos()

    def salvar_e_emitir(self):
        texto = self.txt_conteudo.toPlainText().strip()
        if not texto:
            QMessageBox.warning(self, "Aviso", "O texto do atestado não pode estar vazio.")
            return

        tipo_doc = self.combo_tipo.currentText()
        titulo = self.txt_titulo.text().strip() or "Atestado Odontológico"
        dias = self.spin_dias.value()
        cid = self.txt_cid.text().strip()
        obs = self.txt_obs.text().strip()

        ok, msg, doc_id = issue_clinical_document(
            tipo_documento=tipo_doc,
            patient_id=self.patient_id,
            titulo=titulo,
            conteudo=texto,
            cid=cid,
            dias_repouso=dias,
            observacoes=obs,
            user_id=self.current_user.get("id"),
            usuario_nome=self.current_user.get("nome", "Dra. Lara Camila")
        )

        if not ok:
            QMessageBox.critical(self, "Erro", msg)
            return

        doc = get_issued_document(doc_id)
        html = gerar_html_atestado(doc)
        prev = ClinicalDocPreviewDialog(doc, html, self)
        prev.exec()

        self.accept()


# ==============================================================================
# GERENCIAMENTO DE MODELOS DE MEDICAMENTOS (CRUD)
# ==============================================================================
class PrescriptionTemplateFormDialog(QDialog):
    """Cadastro/Edição de modelo de medicamento/posologia."""
    def __init__(self, template: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Editar Medicamento" if template else "Novo Medicamento no Catálogo")
        self.resize(520, 420)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Nome do Medicamento / Princípio Ativo (*):"))
        self.txt_nome = QLineEdit()
        layout.addWidget(self.txt_nome)

        layout.addWidget(QLabel("Concentração e Forma Farmacêutica:"))
        self.txt_conc = QLineEdit()
        self.txt_conc.setPlaceholderText("Ex: 500mg (Cápsulas), 0,12% (Solução)")
        layout.addWidget(self.txt_conc)

        layout.addWidget(QLabel("Categoria Farmacológica:"))
        self.combo_cat = QComboBox()
        self.combo_cat.setEditable(True)
        self.combo_cat.addItems(["Antibióticos", "Anti-inflamatórios", "Analgésicos", "Corticoides", "Antissépticos", "Geral"])
        layout.addWidget(self.combo_cat)

        layout.addWidget(QLabel("Posologia Padrão Recomendada (*):"))
        self.txt_poso = QTextEdit()
        self.txt_poso.setPlaceholderText("Ex: Tomar 1 comprimido via oral a cada 8 horas por 7 dias.")
        layout.addWidget(self.txt_poso)

        layout.addWidget(QLabel("Orientações e Precauções ao Paciente:"))
        self.txt_ori = QLineEdit()
        self.txt_ori.setPlaceholderText("Ex: Ingerir após as refeições. Não ingerir bebidas alcoólicas.")
        layout.addWidget(self.txt_ori)

        if self.template:
            self.txt_nome.setText(self.template.get("nome_medicamento", ""))
            self.txt_conc.setText(self.template.get("concentracao_forma", "") or "")
            self.combo_cat.setCurrentText(self.template.get("categoria", "Geral"))
            self.txt_poso.setPlainText(self.template.get("posologia", ""))
            self.txt_ori.setText(self.template.get("orientacoes", "") or "")

        btn_box = QHBoxLayout()
        btn_canc = QPushButton("Cancelar")
        btn_canc.setObjectName("secondaryBtn")
        btn_canc.clicked.connect(self.reject)
        btn_salv = QPushButton("Salvar Medicamento")
        btn_salv.setObjectName("primaryBtn")
        btn_salv.clicked.connect(self.salvar)

        btn_box.addWidget(btn_canc)
        btn_box.addStretch()
        btn_box.addWidget(btn_salv)
        layout.addLayout(btn_box)

    def salvar(self):
        nome = self.txt_nome.text().strip()
        poso = self.txt_poso.toPlainText().strip()
        if not nome or not poso:
            QMessageBox.warning(self, "Aviso", "Nome e Posologia são obrigatórios.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "nome": self.txt_nome.text().strip(),
            "concentracao_forma": self.txt_conc.text().strip(),
            "categoria": self.combo_cat.currentText().strip() or "Geral",
            "posologia": self.txt_poso.toPlainText().strip(),
            "orientacoes": self.txt_ori.text().strip()
        }


class ManagePrescriptionTemplatesDialog(QDialog):
    """Gerenciador completo de catálogo de remédios e posologias da clínica."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Catálogo de Medicamentos e Posologias Padrão")
        self.resize(850, 550)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        lbl = QLabel("💊 Catálogo de Medicamentos da Clínica")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        top.addWidget(lbl)
        top.addStretch()

        btn_novo = QPushButton("+ Novo Medicamento")
        btn_novo.setObjectName("primaryBtn")
        btn_novo.clicked.connect(self.novo_medicamento)
        top.addWidget(btn_novo)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Categoria", "Medicamento", "Concentração", "Posologia Padrão", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.carregar_tabela()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("secondaryBtn")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignRight)

    def carregar_tabela(self):
        templates = list_prescription_templates()
        self.table.setRowCount(len(templates))
        for r_idx, t in enumerate(templates):
            self.table.setItem(r_idx, 0, QTableWidgetItem(t["categoria"] or "Geral"))
            self.table.setItem(r_idx, 1, QTableWidgetItem(t["nome_medicamento"]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(t["concentracao_forma"] or ""))
            self.table.setItem(r_idx, 3, QTableWidgetItem(t["posologia"]))

            actions_w = QWidget()
            a_lay = QHBoxLayout(actions_w)
            a_lay.setContentsMargins(4, 2, 4, 2)
            a_lay.setSpacing(6)

            btn_edit = QPushButton("Editar")
            btn_edit.setObjectName("secondaryBtn")
            btn_edit.clicked.connect(lambda _, item=t: self.editar_medicamento(item))
            a_lay.addWidget(btn_edit)

            btn_del = QPushButton("Excluir")
            btn_del.setObjectName("dangerBtn")
            btn_del.clicked.connect(lambda _, tid=t["id"], nome=t["nome_medicamento"]: self.excluir_medicamento(tid, nome))
            a_lay.addWidget(btn_del)

            self.table.setCellWidget(r_idx, 4, actions_w)

    def novo_medicamento(self):
        dlg = PrescriptionTemplateFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok, msg, _ = create_prescription_template(
                nome=data["nome"],
                concentracao_forma=data["concentracao_forma"],
                posologia=data["posologia"],
                orientacoes=data["orientacoes"],
                categoria=data["categoria"],
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            if ok:
                self.carregar_tabela()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def editar_medicamento(self, item: dict):
        dlg = PrescriptionTemplateFormDialog(template=item, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok, msg = update_prescription_template(
                template_id=item["id"],
                nome=data["nome"],
                concentracao_forma=data["concentracao_forma"],
                posologia=data["posologia"],
                orientacoes=data["orientacoes"],
                categoria=data["categoria"],
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            if ok:
                self.carregar_tabela()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def excluir_medicamento(self, tid: int, nome: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente desativar o medicamento '{nome}' do catálogo?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_prescription_template(
                tid,
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            self.carregar_tabela()


# ==============================================================================
# GERENCIAMENTO DE MODELOS DE ATESTADOS (CRUD)
# ==============================================================================
class CertificateTemplateFormDialog(QDialog):
    """Cadastro/Edição de modelo de atestado ou declaração."""
    def __init__(self, template: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("Editar Modelo de Atestado" if template else "Novo Modelo de Atestado")
        self.resize(600, 480)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Título do Modelo (*):"))
        self.txt_titulo = QLineEdit()
        self.txt_titulo.setPlaceholderText("Ex: Atestado de Repouso 2 Dias")
        layout.addWidget(self.txt_titulo)

        h_row = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Atestado", "Declaracao", "Outro"])
        v1.addWidget(self.combo_tipo)
        h_row.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Dias Padrão de Repouso:"))
        self.spin_dias = QSpinBox()
        self.spin_dias.setRange(0, 90)
        self.spin_dias.setValue(1)
        v2.addWidget(self.spin_dias)
        h_row.addLayout(v2)
        layout.addLayout(h_row)

        layout.addWidget(QLabel("Texto Padrão (*):"))
        lbl_tags = QLabel("Tags dinâmicas disponíveis: <code>{paciente}</code>, <code>{cpf}</code>, <code>{dias}</code>, <code>{data}</code>, <code>{horario_inicio}</code>, <code>{horario_fim}</code>")
        lbl_tags.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_tags)

        self.txt_corpo = QTextEdit()
        self.txt_corpo.setPlaceholderText("Atesto para os devidos fins que o(a) paciente {paciente}, portador(a) do CPF nº {cpf}...")
        layout.addWidget(self.txt_corpo)

        if self.template:
            self.txt_titulo.setText(self.template.get("titulo", ""))
            self.combo_tipo.setCurrentText(self.template.get("tipo", "Atestado"))
            self.spin_dias.setValue(self.template.get("dias_repouso", 1))
            self.txt_corpo.setPlainText(self.template.get("texto_padrao", ""))

        btn_box = QHBoxLayout()
        btn_canc = QPushButton("Cancelar")
        btn_canc.setObjectName("secondaryBtn")
        btn_canc.clicked.connect(self.reject)
        btn_salv = QPushButton("Salvar Modelo")
        btn_salv.setObjectName("primaryBtn")
        btn_salv.clicked.connect(self.salvar)

        btn_box.addWidget(btn_canc)
        btn_box.addStretch()
        btn_box.addWidget(btn_salv)
        layout.addLayout(btn_box)

    def salvar(self):
        if not self.txt_titulo.text().strip() or not self.txt_corpo.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "Título e Texto Padrão são obrigatórios.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "titulo": self.txt_titulo.text().strip(),
            "tipo": self.combo_tipo.currentText(),
            "dias_repouso": self.spin_dias.value(),
            "texto_padrao": self.txt_corpo.toPlainText().strip()
        }


class ManageCertificateTemplatesDialog(QDialog):
    """Gerenciador completo de modelos de atestados e declarações."""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Modelos de Atestados e Declarações Odontológicas")
        self.resize(850, 550)
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        lbl = QLabel("📋 Modelos Oficiais de Atestados e Declarações")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f766e;")
        top.addWidget(lbl)
        top.addStretch()

        btn_novo = QPushButton("+ Novo Modelo")
        btn_novo.setObjectName("primaryBtn")
        btn_novo.clicked.connect(self.novo_modelo)
        top.addWidget(btn_novo)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tipo", "Título do Modelo", "Dias Padrão", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.carregar_tabela()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setObjectName("secondaryBtn")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar, alignment=Qt.AlignRight)

    def carregar_tabela(self):
        templates = list_certificate_templates()
        self.table.setRowCount(len(templates))
        for r_idx, t in enumerate(templates):
            self.table.setItem(r_idx, 0, QTableWidgetItem(t["tipo"]))
            self.table.setItem(r_idx, 1, QTableWidgetItem(t["titulo"]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(str(t.get("dias_repouso", 0))))

            actions_w = QWidget()
            a_lay = QHBoxLayout(actions_w)
            a_lay.setContentsMargins(4, 2, 4, 2)
            a_lay.setSpacing(6)

            btn_edit = QPushButton("Editar")
            btn_edit.setObjectName("secondaryBtn")
            btn_edit.clicked.connect(lambda _, item=t: self.editar_modelo(item))
            a_lay.addWidget(btn_edit)

            btn_del = QPushButton("Excluir")
            btn_del.setObjectName("dangerBtn")
            btn_del.clicked.connect(lambda _, tid=t["id"], tit=t["titulo"]: self.excluir_modelo(tid, tit))
            a_lay.addWidget(btn_del)

            self.table.setCellWidget(r_idx, 3, actions_w)

    def novo_modelo(self):
        dlg = CertificateTemplateFormDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok, msg, _ = create_certificate_template(
                titulo=data["titulo"],
                tipo=data["tipo"],
                dias_repouso=data["dias_repouso"],
                texto_padrao=data["texto_padrao"],
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            if ok:
                self.carregar_tabela()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def editar_modelo(self, item: dict):
        dlg = CertificateTemplateFormDialog(template=item, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            ok, msg = update_certificate_template(
                template_id=item["id"],
                titulo=data["titulo"],
                tipo=data["tipo"],
                dias_repouso=data["dias_repouso"],
                texto_padrao=data["texto_padrao"],
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            if ok:
                self.carregar_tabela()
            else:
                QMessageBox.critical(self, "Erro", msg)

    def excluir_modelo(self, tid: int, tit: str):
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente desativar o modelo '{tit}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_certificate_template(
                tid,
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            self.carregar_tabela()


# ==============================================================================
# WIDGET PRINCIPAL: ABA "RECEITUÁRIOS E ATESTADOS" NA FICHA DO PACIENTE
# ==============================================================================
class ClinicalDocsWidget(QWidget):
    """Aba completa de gerenciamento e emissão de receituários e atestados para o paciente."""
    def __init__(self, patient_id: int, current_user: dict, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.current_user = current_user
        self.setStyleSheet(DOCS_STYLE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Barra Superior de Ações
        top_bar = QHBoxLayout()

        lbl_tit = QLabel("Histórico de Receituários e Atestados Emitidos")
        lbl_tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f766e;")
        top_bar.addWidget(lbl_tit)
        top_bar.addStretch()

        btn_nova_receita = QPushButton("💊 + Nova Receita")
        btn_nova_receita.setObjectName("primaryBtn")
        btn_nova_receita.clicked.connect(self.abrir_nova_receita)
        top_bar.addWidget(btn_nova_receita)

        btn_novo_atestado = QPushButton("📋 + Novo Atestado / Declaração")
        btn_novo_atestado.setObjectName("primaryBtn")
        btn_novo_atestado.clicked.connect(self.abrir_novo_atestado)
        top_bar.addWidget(btn_novo_atestado)

        btn_modelos_meds = QPushButton("⚙️ Medicamentos")
        btn_modelos_meds.setObjectName("secondaryBtn")
        btn_modelos_meds.clicked.connect(self.abrir_gerenciador_meds)
        top_bar.addWidget(btn_modelos_meds)

        btn_modelos_atest = QPushButton("⚙️ Modelos de Atestados")
        btn_modelos_atest.setObjectName("secondaryBtn")
        btn_modelos_atest.clicked.connect(self.abrir_gerenciador_atest)
        top_bar.addWidget(btn_modelos_atest)

        layout.addLayout(top_bar)

        # Tabela de Documentos Emitidos
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Data de Emissão", "Tipo", "Título / Descrição", "Profissional", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.visualizar_documento_duplo_clique)
        layout.addWidget(self.table)

        # Barra de rodapé com atalhos
        footer = QHBoxLayout()
        lbl_hint = QLabel("💡 Dica: Dê duplo clique no documento para pré-visualizar, exportar PDF ou imprimir timbrado.")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 12px;")
        footer.addWidget(lbl_hint)
        footer.addStretch()

        btn_visualizar = QPushButton("👁️ Visualizar / Imprimir PDF")
        btn_visualizar.setObjectName("secondaryBtn")
        btn_visualizar.clicked.connect(self.visualizar_documento_selecionado)
        footer.addWidget(btn_visualizar)

        btn_excluir = QPushButton("🗑️ Excluir Registro")
        btn_excluir.setObjectName("dangerBtn")
        btn_excluir.clicked.connect(self.excluir_documento_selecionado)
        footer.addWidget(btn_excluir)

        layout.addLayout(footer)

        self.carregar_documentos()

    def get_paciente_info(self) -> tuple:
        from services.patient_service import get_patient
        p = get_patient(self.patient_id)
        if p:
            return p["nome"], p["cpf"] or ""
        return "Paciente", ""

    def carregar_documentos(self):
        """Carrega a lista de documentos emitidos para o paciente."""
        docs = list_patient_issued_documents(self.patient_id)
        self.table.setRowCount(len(docs))
        for r_idx, d in enumerate(docs):
            item_data = QTableWidgetItem(d["data_emissao"])
            item_data.setTextAlignment(Qt.AlignCenter)
            item_data.setData(Qt.UserRole, d["id"])
            self.table.setItem(r_idx, 0, item_data)

            # Badge / Ícone do tipo
            tipo = d["tipo_documento"]
            tipo_icon = "💊 Receita" if tipo == "Receituario" else ("📋 Atestado" if tipo == "Atestado" else "📄 Declaração")
            item_tipo = QTableWidgetItem(tipo_icon)
            item_tipo.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 1, item_tipo)

            item_tit = QTableWidgetItem(d["titulo"])
            item_tit.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(r_idx, 2, item_tit)

            item_user = QTableWidgetItem(d["usuario_nome"] or "Dra. Lara Camila")
            item_user.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 3, item_user)

            # Botão de ação rápida na linha
            btn_ver = QPushButton("👁️ Visualizar")
            btn_ver.setObjectName("secondaryBtn")
            btn_ver.clicked.connect(lambda _, doc_id=d["id"]: self.abrir_preview_doc(doc_id))
            self.table.setCellWidget(r_idx, 4, btn_ver)

    def abrir_nova_receita(self):
        p_nome, p_cpf = self.get_paciente_info()
        dlg = PrescriptionFormDialog(self.patient_id, p_nome, p_cpf, self.current_user, self)
        if dlg.exec() == QDialog.Accepted:
            self.carregar_documentos()

    def abrir_novo_atestado(self):
        p_nome, p_cpf = self.get_paciente_info()
        dlg = CertificateFormDialog(self.patient_id, p_nome, p_cpf, self.current_user, self)
        if dlg.exec() == QDialog.Accepted:
            self.carregar_documentos()

    def abrir_gerenciador_meds(self):
        dlg = ManagePrescriptionTemplatesDialog(self.current_user, self)
        dlg.exec()

    def abrir_gerenciador_atest(self):
        dlg = ManageCertificateTemplatesDialog(self.current_user, self)
        dlg.exec()

    def abrir_preview_doc(self, doc_id: int):
        doc = get_issued_document(doc_id)
        if not doc:
            QMessageBox.warning(self, "Aviso", "Documento não encontrado.")
            return

        if doc["tipo_documento"] == "Receituario":
            html = gerar_html_receituario(doc)
        else:
            html = gerar_html_atestado(doc)

        dlg = ClinicalDocPreviewDialog(doc, html, self)
        dlg.exec()

    def visualizar_documento_selecionado(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Aviso", "Selecione um documento na tabela para visualizar.")
            return
        doc_id = self.table.item(row, 0).data(Qt.UserRole)
        self.abrir_preview_doc(doc_id)

    def visualizar_documento_duplo_clique(self, index):
        row = index.row()
        if row >= 0:
            doc_id = self.table.item(row, 0).data(Qt.UserRole)
            self.abrir_preview_doc(doc_id)

    def excluir_documento_selecionado(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Aviso", "Selecione um documento na tabela para excluir.")
            return

        doc_id = self.table.item(row, 0).data(Qt.UserRole)
        titulo = self.table.item(row, 2).text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir o registro do documento '{titulo}'?\nEsta ação não poderá ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            ok, msg = delete_issued_document(
                doc_id,
                user_id=self.current_user.get("id"),
                usuario_nome=self.current_user.get("nome", "Admin")
            )
            if ok:
                self.carregar_documentos()
            else:
                QMessageBox.critical(self, "Erro ao Excluir", msg)
