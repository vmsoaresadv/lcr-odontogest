"""
Módulo de Serviços Clínicos: Prescrições, Receituários e Atestados Odontológicos
Gerencia modelos reutilizáveis (CRUD) de medicamentos/posologias e atestados,
além do histórico de documentos emitidos e geração de HTML formatado para PDF timbrado.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from database.connection import get_db_connection
from services.audit_service import log_action
from services.report_service import gerar_cabecalho_html, gerar_rodape_html, exportar_html_para_pdf
from version import APP_NAME, CLINICA_NOME, RESPONSAVEL_NOME, RESPONSAVEL_CRO, CIDADE_ESTADO


# -------------------------------------------------------------
# 1. MODELOS DE MEDICAMENTOS E POSOLOGIAS (CRUD)
# -------------------------------------------------------------

def list_prescription_templates(categoria: Optional[str] = None, busca: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista modelos de medicamentos ativos com filtros opcionais de categoria e busca."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM prescription_templates WHERE ativo = 1"
        params = []
        if categoria and categoria != "Todas":
            sql += " AND categoria = ?"
            params.append(categoria)
        if busca and busca.strip():
            sql += " AND (nome_medicamento LIKE ? OR concentracao_forma LIKE ? OR posologia LIKE ?)"
            termo = f"%{busca.strip()}%"
            params.extend([termo, termo, termo])
        sql += " ORDER BY categoria ASC, nome_medicamento ASC"
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_prescription_template(template_id: int) -> Optional[Dict[str, Any]]:
    """Obtém os detalhes de um modelo de medicamento específico."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prescription_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_prescription_template(
    nome: str,
    concentracao_forma: str,
    posologia: str,
    orientacoes: Optional[str] = None,
    categoria: str = "Geral",
    user_id: Optional[int] = None,
    usuario_nome: str = "Sistema"
) -> Tuple[bool, str, Optional[int]]:
    """Cadastra um novo modelo de medicamento / posologia."""
    if not nome or not nome.strip():
        return False, "O nome do medicamento é obrigatório.", None
    if not posologia or not posologia.strip():
        return False, "A posologia é obrigatória.", None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prescription_templates (nome_medicamento, concentracao_forma, posologia, orientacoes, categoria, ativo)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (nome.strip(), concentracao_forma.strip() if concentracao_forma else None, posologia.strip(), orientacoes.strip() if orientacoes else None, categoria.strip()))
        conn.commit()
        novo_id = cursor.lastrowid

    log_action(user_id, usuario_nome, "CRIAR_PRESCRICAO_MODELO", f"Modelo de medicamento '{nome}' cadastrado")
    return True, "Modelo de medicamento cadastrado com sucesso!", novo_id


def update_prescription_template(
    template_id: int,
    nome: str,
    concentracao_forma: str,
    posologia: str,
    orientacoes: Optional[str] = None,
    categoria: str = "Geral",
    user_id: Optional[int] = None,
    usuario_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Atualiza um modelo de medicamento existente."""
    if not nome or not nome.strip():
        return False, "O nome do medicamento é obrigatório."
    if not posologia or not posologia.strip():
        return False, "A posologia é obrigatória."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE prescription_templates
            SET nome_medicamento = ?, concentracao_forma = ?, posologia = ?, orientacoes = ?, categoria = ?, atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (nome.strip(), concentracao_forma.strip() if concentracao_forma else None, posologia.strip(), orientacoes.strip() if orientacoes else None, categoria.strip(), template_id))
        conn.commit()

    log_action(user_id, usuario_nome, "EDITAR_PRESCRICAO_MODELO", f"Modelo #{template_id} '{nome}' atualizado")
    return True, "Modelo de medicamento atualizado com sucesso!"


def delete_prescription_template(template_id: int, user_id: Optional[int] = None, usuario_nome: str = "Sistema") -> Tuple[bool, str]:
    """Exclui (desativa de forma segura) um modelo de medicamento."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE prescription_templates SET ativo = 0 WHERE id = ?", (template_id,))
        conn.commit()

    log_action(user_id, usuario_nome, "EXCLUIR_PRESCRICAO_MODELO", f"Modelo de medicamento #{template_id} desativado")
    return True, "Modelo de medicamento excluído com sucesso!"


# -------------------------------------------------------------
# 2. MODELOS DE ATESTADOS E DECLARAÇÕES (CRUD)
# -------------------------------------------------------------

def list_certificate_templates(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista modelos de atestados e declarações ativos."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM certificate_templates WHERE ativo = 1"
        params = []
        if tipo and tipo != "Todos":
            sql += " AND tipo = ?"
            params.append(tipo)
        sql += " ORDER BY tipo ASC, titulo ASC"
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_certificate_template(template_id: int) -> Optional[Dict[str, Any]]:
    """Obtém um modelo de atestado específico."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM certificate_templates WHERE id = ?", (template_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_certificate_template(
    titulo: str,
    tipo: str,
    texto_padrao: str,
    dias_repouso: int = 1,
    observacoes: Optional[str] = None,
    user_id: Optional[int] = None,
    usuario_nome: str = "Sistema"
) -> Tuple[bool, str, Optional[int]]:
    """Cria um novo modelo de atestado ou declaração."""
    if not titulo or not titulo.strip():
        return False, "O título do modelo é obrigatório.", None
    if not texto_padrao or not texto_padrao.strip():
        return False, "O texto padrão do documento é obrigatório.", None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO certificate_templates (titulo, tipo, texto_padrao, dias_repouso, observacoes, ativo)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (titulo.strip(), tipo.strip(), texto_padrao.strip(), max(0, int(dias_repouso)), observacoes.strip() if observacoes else None))
        conn.commit()
        novo_id = cursor.lastrowid

    log_action(user_id, usuario_nome, "CRIAR_ATESTADO_MODELO", f"Modelo de atestado '{titulo}' cadastrado")
    return True, "Modelo de atestado cadastrado com sucesso!", novo_id


def update_certificate_template(
    template_id: int,
    titulo: str,
    tipo: str,
    texto_padrao: str,
    dias_repouso: int = 1,
    observacoes: Optional[str] = None,
    user_id: Optional[int] = None,
    usuario_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Atualiza um modelo de atestado ou declaração existente."""
    if not titulo or not titulo.strip():
        return False, "O título do modelo é obrigatório."
    if not texto_padrao or not texto_padrao.strip():
        return False, "O texto padrão é obrigatório."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE certificate_templates
            SET titulo = ?, tipo = ?, texto_padrao = ?, dias_repouso = ?, observacoes = ?, atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (titulo.strip(), tipo.strip(), texto_padrao.strip(), max(0, int(dias_repouso)), observacoes.strip() if observacoes else None, template_id))
        conn.commit()

    log_action(user_id, usuario_nome, "EDITAR_ATESTADO_MODELO", f"Modelo de atestado #{template_id} '{titulo}' atualizado")
    return True, "Modelo de atestado atualizado com sucesso!"


def delete_certificate_template(template_id: int, user_id: Optional[int] = None, usuario_nome: str = "Sistema") -> Tuple[bool, str]:
    """Exclui (desativa) um modelo de atestado."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE certificate_templates SET ativo = 0 WHERE id = ?", (template_id,))
        conn.commit()

    log_action(user_id, usuario_nome, "EXCLUIR_ATESTADO_MODELO", f"Modelo de atestado #{template_id} desativado")
    return True, "Modelo de atestado excluído com sucesso!"


# -------------------------------------------------------------
# 3. HISTÓRICO DE DOCUMENTOS EMITIDOS PARA PACIENTES
# -------------------------------------------------------------

def list_patient_issued_documents(patient_id: int) -> List[Dict[str, Any]]:
    """Lista todos os receituários e atestados já emitidos para um paciente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM issued_clinical_documents
            WHERE patient_id = ?
            ORDER BY data_emissao DESC, id DESC
        """, (patient_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_issued_document(doc_id: int) -> Optional[Dict[str, Any]]:
    """Obtém um documento clínico emitido por ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM issued_clinical_documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def issue_clinical_document(
    tipo_documento: str,
    patient_id: int,
    titulo: str,
    conteudo: Any,  # List[Dict] para receituário ou texto/dict para atestado
    dias_repouso: int = 0,
    cid: Optional[str] = None,
    observacoes: Optional[str] = None,
    user_id: Optional[int] = None,
    usuario_nome: str = "Sistema"
) -> Tuple[bool, str, Optional[int]]:
    """Salva a emissão oficial de um receituário ou atestado para um paciente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Busca dados do paciente
        cursor.execute("SELECT nome, cpf FROM patients WHERE id = ?", (patient_id,))
        pac = cursor.fetchone()
        if not pac:
            return False, "Paciente não encontrado.", None

        conteudo_str = json.dumps(conteudo, ensure_ascii=False) if not isinstance(conteudo, str) else conteudo
        data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M")

        valid_user_id = None
        if user_id:
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if cursor.fetchone():
                valid_user_id = user_id

        cursor.execute("""
            INSERT INTO issued_clinical_documents (
                tipo_documento, patient_id, paciente_nome, paciente_cpf,
                titulo, conteudo_json, cid, dias_repouso, observacoes,
                user_id, usuario_nome, data_emissao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo_documento, patient_id, pac["nome"], pac["cpf"] or "",
            titulo.strip(), conteudo_str, cid.strip() if cid else None,
            max(0, int(dias_repouso)), observacoes.strip() if observacoes else None,
            valid_user_id, usuario_nome, data_hoje
        ))
        conn.commit()
        novo_id = cursor.lastrowid

    log_action(user_id, usuario_nome, f"EMITIR_{tipo_documento.upper()}", f"{tipo_documento} #{novo_id} ('{titulo}') emitido para paciente #{patient_id} ({pac['nome']})")
    return True, f"{tipo_documento} emitido e registrado com sucesso!", novo_id


def delete_issued_document(doc_id: int, user_id: Optional[int] = None, usuario_nome: str = "Sistema") -> Tuple[bool, str]:
    """Exclui o registro de um documento clínico emitido."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM issued_clinical_documents WHERE id = ?", (doc_id,))
        conn.commit()

    log_action(user_id, usuario_nome, "EXCLUIR_DOCUMENTO_CLINICO", f"Documento emitido #{doc_id} excluído")
    return True, "Documento excluído do histórico com sucesso!"


# -------------------------------------------------------------
# 4. GERADORES DE HTML E PDF TIMBRADO (RECEITA E ATESTADO)
# -------------------------------------------------------------

def gerar_html_receituario(
    paciente_nome: str,
    paciente_cpf: str,
    medicamentos: List[Dict[str, str]],
    observacoes_adicionais: Optional[str] = None,
    data_emissao: Optional[str] = None
) -> str:
    """
    Gera o HTML formal de Receituário Odontológico para visualização e exportação em PDF.
    Cada medicamento contém: nome, concentracao, posologia, orientacoes.
    """
    dt_str = data_emissao if data_emissao else datetime.now().strftime("%d/%m/%Y")
    cabecalho = gerar_cabecalho_html("Receituário Odontológico")

    html_meds = ""
    for idx, med in enumerate(medicamentos, 1):
        nome_comp = med.get("nome", "")
        if med.get("concentracao"):
            nome_comp += f" — {med['concentracao']}"
        posologia = med.get("posologia", "")
        orientacoes = med.get("orientacoes", "")

        html_meds += f"""
        <div style="margin-bottom: 22px; padding-bottom: 14px; border-bottom: 1px dashed #e2e8f0; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="font-size: 13pt; font-weight: bold; color: #0f766e; margin-bottom: 5px;">
                {idx}. {nome_comp}
            </div>
            <div style="font-size: 11pt; color: #1e293b; line-height: 1.5; margin-left: 18px;">
                <strong>Uso:</strong> {posologia}
            </div>
        """
        if orientacoes:
            html_meds += f"""
            <div style="font-size: 10pt; color: #64748b; font-style: italic; margin-left: 18px; margin-top: 4px;">
                <strong>Recomendações:</strong> {orientacoes}
            </div>
            """
        html_meds += "</div>"

    html_obs = ""
    if observacoes_adicionais and observacoes_adicionais.strip():
        html_obs = f"""
        <div style="margin-top: 20px; padding: 12px; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; font-family: 'Segoe UI', Arial, sans-serif;">
            <div style="font-weight: bold; font-size: 10pt; color: #475569; margin-bottom: 4px;">Orientações Gerais Pós-Procedimento:</div>
            <div style="font-size: 10.5pt; color: #334155; line-height: 1.4;">{observacoes_adicionais.strip()}</div>
        </div>
        """

    rodape = gerar_rodape_html()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #0f172a;
                margin: 0;
                padding: 10px;
            }}
        </style>
    </head>
    <body>
        {cabecalho}

        <div style="background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px; font-family: 'Segoe UI', Arial, sans-serif;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="font-size: 12pt; color: #134e4a;">
                        <strong>Paciente:</strong> {paciente_nome}
                    </td>
                    <td style="text-align: right; font-size: 11pt; color: #134e4a;">
                        <strong>CPF:</strong> {paciente_cpf if paciente_cpf else "Não informado"}
                    </td>
                </tr>
            </table>
        </div>

        <div style="margin-top: 10px;">
            <div style="font-size: 11pt; font-weight: bold; color: #475569; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; border-bottom: 2px solid #0f766e; padding-bottom: 4px;">
                Prescrição Medicamentosa (Via Oral / Uso Tópico)
            </div>
            {html_meds}
        </div>

        {html_obs}

        {rodape}
    </body>
    </html>
    """


def gerar_html_atestado(
    paciente_nome: str,
    paciente_cpf: str,
    tipo: str,  # 'Atestado' ou 'Declaracao'
    texto_corpo: str,
    dias_repouso: int = 1,
    cid: Optional[str] = None,
    observacoes: Optional[str] = None,
    data_emissao: Optional[str] = None
) -> str:
    """
    Gera o HTML formal de Atestado Odontológico ou Declaração de Comparecimento.
    """
    titulo_doc = "Atestado Odontológico" if tipo == "Atestado" else "Declaração de Comparecimento"
    cabecalho = gerar_cabecalho_html(titulo_doc)
    dt_str = data_emissao if data_emissao else datetime.now().strftime("%d de %B de %Y")

    # Mapeia meses para português caso o sistema retorne em inglês
    meses_en_pt = {
        "January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril",
        "May": "maio", "June": "junho", "July": "julho", "August": "agosto",
        "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"
    }
    for en, pt in meses_en_pt.items():
        dt_str = dt_str.replace(en, pt)

    # Informação de CID (opcional e confidencial a pedido do paciente)
    html_cid = ""
    if cid and cid.strip():
        html_cid = f"""
        <div style="margin-top: 18px; font-size: 11pt; color: #475569; font-family: 'Segoe UI', Arial, sans-serif;">
            <strong>Diagnóstico / CID-10:</strong> {cid.strip()} <em>(Informado a pedido expresso do(a) paciente, em conformidade com o Código de Ética Odontológica)</em>.
        </div>
        """

    html_repouso = ""
    if tipo == "Atestado" and dias_repouso > 0:
        dias_txt = f"{dias_repouso} ({'um' if dias_repouso == 1 else 'dois' if dias_repouso == 2 else 'três' if dias_repouso == 3 else str(dias_repouso)}) dia(s)"
        html_repouso = f"""
        <div style="margin-top: 14px; font-size: 12pt; color: #0f766e; font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif;">
            Período de afastamento recomendado: {dias_txt}.
        </div>
        """

    html_obs = ""
    if observacoes and observacoes.strip():
        html_obs = f"""
        <div style="margin-top: 20px; padding: 10px; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 10pt; color: #475569;">
            <strong>Observações Complementares:</strong> {observacoes.strip()}
        </div>
        """

    rodape = gerar_rodape_html()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #0f172a;
                margin: 0;
                padding: 10px;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        {cabecalho}

        <div style="background-color: #f0fdfa; border: 1px solid #99f6e4; border-radius: 6px; padding: 12px 16px; margin-bottom: 30px; font-family: 'Segoe UI', Arial, sans-serif;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="font-size: 12pt; color: #134e4a;">
                        <strong>Paciente:</strong> {paciente_nome}
                    </td>
                    <td style="text-align: right; font-size: 11pt; color: #134e4a;">
                        <strong>CPF:</strong> {paciente_cpf if paciente_cpf else "Não informado"}
                    </td>
                </tr>
            </table>
        </div>

        <div style="margin-top: 30px; margin-bottom: 30px; padding: 10px 15px; font-size: 13pt; text-align: justify; text-justify: inter-word; color: #1e293b; line-height: 1.8;">
            {texto_corpo}
            {html_repouso}
            {html_cid}
        </div>

        {html_obs}

        <div style="margin-top: 35px; text-align: right; font-size: 12pt; color: #475569;">
            {CIDADE_ESTADO}, {dt_str}.
        </div>

        {rodape}
    </body>
    </html>
    """
