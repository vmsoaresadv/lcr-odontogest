"""
Módulo de Gestão de Orçamentos e Planos de Tratamento Odontológico
LCR OdontoGest - Dra. Lara Camila (CRO-BA 15247)
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional
from database.connection import get_db_connection
from services.audit_service import log_action
from services.patient_service import add_record, get_patient


def create_budget(
    patient_id: int,
    titulo: str,
    itens: List[Dict],
    desconto: float,
    forma_pagamento: str,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str, int]:
    """Cria um novo orçamento/plano de tratamento com seus respectivos itens discriminados."""
    if not titulo or not titulo.strip():
        return False, "O título do orçamento é obrigatório.", 0

    if not itens:
        return False, "O orçamento deve conter pelo menos um procedimento/item.", 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Calcular totais
        valor_bruto = 0.0
        for item in itens:
            qtd = int(item.get("quantidade", 1))
            vu = float(item.get("valor_unitario", 0.0))
            valor_bruto += (qtd * vu)

        desconto_val = max(0.0, float(desconto or 0.0))
        valor_final = max(0.0, valor_bruto - desconto_val)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hoje = datetime.now().strftime("%d/%m/%Y")

        cursor.execute("""
            INSERT INTO patient_budgets (
                patient_id, titulo, valor_bruto, desconto, valor_final,
                forma_pagamento, status, observacoes, data_criacao,
                user_id, user_nome
            ) VALUES (?, ?, ?, ?, ?, ?, 'Pendente', ?, ?, ?, ?)
        """, (
            patient_id, titulo.strip(), valor_bruto, desconto_val, valor_final,
            forma_pagamento.strip() if forma_pagamento else "A combinar",
            observacoes.strip() if observacoes else "",
            hoje, user_id, user_nome
        ))
        budget_id = cursor.lastrowid

        # Inserir itens
        for item in itens:
            dente = str(item.get("dente_regiao", "")).strip()
            proc = str(item.get("procedimento", "")).strip()
            qtd = int(item.get("quantidade", 1))
            vu = float(item.get("valor_unitario", 0.0))
            vt = qtd * vu
            cursor.execute("""
                INSERT INTO patient_budget_items (
                    budget_id, dente_regiao, procedimento, quantidade, valor_unitario, valor_total
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (budget_id, dente, proc, qtd, vu, vt))

        conn.commit()

        log_action(user_id, user_nome, "ORCAMENTO_CRIADO",
                   f"Orçamento #{budget_id} ('{titulo}') criado para o paciente #{patient_id} no valor de R$ {valor_final:.2f}")

        return True, "Orçamento criado com sucesso!", budget_id

    except Exception as e:
        conn.rollback()
        return False, f"Erro ao criar orçamento: {e}", 0
    finally:
        conn.close()


def list_budgets(patient_id: int) -> List[Dict]:
    """Lista todos os orçamentos do paciente ordenados pelo mais recente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, COUNT(i.id) as total_itens
        FROM patient_budgets b
        LEFT JOIN patient_budget_items i ON b.id = i.budget_id
        WHERE b.patient_id = ?
        GROUP BY b.id
        ORDER BY b.id DESC
    """, (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_budget_details(budget_id: int) -> Optional[Dict]:
    """Retorna os dados completos do orçamento, incluindo todos os seus itens."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_budgets WHERE id = ?", (budget_id,))
    b_row = cursor.fetchone()
    if not b_row:
        conn.close()
        return None

    budget = dict(b_row)

    cursor.execute("""
        SELECT * FROM patient_budget_items
        WHERE budget_id = ?
        ORDER BY id ASC
    """, (budget_id,))
    items_rows = cursor.fetchall()
    conn.close()

    budget["itens"] = [dict(it) for it in items_rows]
    return budget


def update_budget_status(
    budget_id: int,
    novo_status: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Altera o status do orçamento ('Pendente', 'Aprovado', 'Recusado', 'Concluído')."""
    if novo_status not in ['Pendente', 'Aprovado', 'Recusado', 'Concluído']:
        return False, "Status inválido."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hoje = datetime.now().strftime("%d/%m/%Y")

        data_aprov = hoje if novo_status == 'Aprovado' else None
        aprov_por = user_nome if novo_status == 'Aprovado' else None

        cursor.execute("""
            UPDATE patient_budgets
            SET status = ?, data_aprovacao = ?, aprovado_por = ?, atualizado_em = ?
            WHERE id = ?
        """, (novo_status, data_aprov, aprov_por, agora, budget_id))
        conn.commit()

        log_action(user_id, user_nome, "ORCAMENTO_STATUS",
                   f"Orçamento #{budget_id} teve o status alterado para '{novo_status}'")
        return True, f"Status do orçamento atualizado para '{novo_status}'!"

    except Exception as e:
        return False, f"Erro ao atualizar status: {e}"
    finally:
        conn.close()


def aprovar_orcamento(
    budget_id: int,
    lancar_no_prontuario: bool,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """
    Aprova o orçamento e, se selecionado, adiciona automaticamente cada procedimento
    ao prontuário clínico do paciente com status 'Planejado / Aprovado'.
    """
    details = get_budget_details(budget_id)
    if not details:
        return False, "Orçamento não encontrado."

    ok, msg = update_budget_status(budget_id, "Aprovado", user_id, user_nome)
    if not ok:
        return False, msg

    if lancar_no_prontuario:
        patient_id = details["patient_id"]
        for item in details.get("itens", []):
            dente = item.get("dente_regiao", "")
            proc = item.get("procedimento", "")
            obs = f"Procedimento gerado a partir do Orçamento #{budget_id} aprovado."
            add_record(
                patient_id=patient_id,
                dente_regiao=dente,
                procedimento=proc,
                descricao=obs,
                profissional_nome=user_nome,
                user_id=user_id
            )

    return True, "Orçamento aprovado com sucesso e lançado na ficha do paciente!"


def delete_budget(budget_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclui um orçamento e seus itens correspondentes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT patient_id, titulo FROM patient_budgets WHERE id = ?", (budget_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Orçamento não encontrado."

        p_id = row["patient_id"]
        titulo = row["titulo"]

        cursor.execute("DELETE FROM patient_budgets WHERE id = ?", (budget_id,))
        conn.commit()

        log_action(user_id, user_nome, "ORCAMENTO_EXCLUIDO",
                   f"Orçamento #{budget_id} ('{titulo}') do paciente #{p_id} foi excluído.")
        return True, "Orçamento excluído com sucesso."

    except Exception as e:
        return False, f"Erro ao excluir orçamento: {e}"
    finally:
        conn.close()


def gerar_html_orcamento(budget_id: int) -> str:
    """Gera o HTML formal de impressão do Orçamento / Plano de Tratamento em padrão A4."""
    budget = get_budget_details(budget_id)
    if not budget:
        return "<p>Orçamento não encontrado.</p>"

    patient = get_patient(budget["patient_id"])
    if not patient:
        return "<p>Paciente não encontrado.</p>"

    from services.report_service import get_clinic_header_html

    cabecalho = get_clinic_header_html("PLANO DE TRATAMENTO E ORÇAMENTO ODONTOLÓGICO")

    status_cor = {
        "Pendente": "#d97706",
        "Aprovado": "#059669",
        "Recusado": "#dc2626",
        "Concluído": "#2563eb"
    }.get(budget["status"], "#334155")

    # Linhas de itens
    linhas_itens = ""
    for idx, item in enumerate(budget.get("itens", []), 1):
        dente = item.get("dente_regiao") or "Geral"
        proc = item.get("procedimento") or ""
        qtd = item.get("quantidade", 1)
        vu = item.get("valor_unitario", 0.0)
        vt = item.get("valor_total", 0.0)

        linhas_itens += f"""
        <tr>
            <td style="text-align: center;">{idx}</td>
            <td style="text-align: center; font-weight: bold;">{dente}</td>
            <td>{proc}</td>
            <td style="text-align: center;">{qtd}</td>
            <td style="text-align: right;">R$ {vu:,.2f}</td>
            <td style="text-align: right; font-weight: bold;">R$ {vt:,.2f}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                color: #1e293b;
                line-height: 1.4;
                margin: 0;
                padding: 10px;
            }}
            .secao-titulo {{
                font-size: 12pt;
                font-weight: bold;
                color: #0f766e;
                border-bottom: 2px solid #0f766e;
                padding-bottom: 4px;
                margin-top: 14px;
                margin-bottom: 8px;
            }}
            table.tabela-info {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }}
            table.tabela-info td {{
                padding: 5px 8px;
                font-size: 11pt;
            }}
            table.tabela-itens {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 8px;
                margin-bottom: 12px;
            }}
            table.tabela-itens th {{
                background-color: #f1f5f9;
                color: #334155;
                font-size: 10pt;
                font-weight: bold;
                padding: 7px 8px;
                border: 1px solid #cbd5e1;
            }}
            table.tabela-itens td {{
                padding: 6px 8px;
                font-size: 10pt;
                border: 1px solid #cbd5e1;
            }}
            .bloco-totais {{
                float: right;
                width: 280px;
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px;
                margin-top: 6px;
                margin-bottom: 14px;
            }}
            .assinaturas {{
                clear: both;
                margin-top: 50px;
                width: 100%;
            }}
            .assinatura-box {{
                display: inline-block;
                width: 45%;
                text-align: center;
                vertical-align: top;
            }}
            .linha-assinatura {{
                border-top: 1px solid #334155;
                margin-bottom: 4px;
            }}
        </style>
    </head>
    <body>
        {cabecalho}

        <div class="secao-titulo">1. DADOS DO PACIENTE E DO ORÇAMENTO</div>
        <table class="tabela-info">
            <tr>
                <td style="width: 50%;"><strong>Paciente:</strong> {patient.get('nome', '')}</td>
                <td style="width: 50%;"><strong>CPF:</strong> {patient.get('cpf') or 'Não informado'}</td>
            </tr>
            <tr>
                <td><strong>Telefone:</strong> {patient.get('telefone') or 'Não informado'}</td>
                <td><strong>Data de Emissão:</strong> {budget.get('data_criacao', '')}</td>
            </tr>
            <tr>
                <td><strong>Plano / Título:</strong> {budget.get('titulo', '')}</td>
                <td><strong>Situação:</strong> <span style="font-weight: bold; color: {status_cor};">{budget.get('status', 'Pendente')}</span></td>
            </tr>
        </table>

        <div class="secao-titulo">2. PROCEDIMENTOS PROPOSTOS</div>
        <table class="tabela-itens">
            <thead>
                <tr>
                    <th style="width: 6%;">Item</th>
                    <th style="width: 16%;">Dente / Região</th>
                    <th style="width: 44%;">Procedimento</th>
                    <th style="width: 8%;">Qtd</th>
                    <th style="width: 13%;">Valor Unit.</th>
                    <th style="width: 13%;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {linhas_itens}
            </tbody>
        </table>

        <div class="bloco-totais">
            <table style="width: 100%; font-size: 11pt;">
                <tr>
                    <td>Valor Bruto:</td>
                    <td style="text-align: right;">R$ {budget.get('valor_bruto', 0.0):,.2f}</td>
                </tr>
                <tr>
                    <td>Desconto Concedido:</td>
                    <td style="text-align: right; color: #dc2626;">- R$ {budget.get('desconto', 0.0):,.2f}</td>
                </tr>
                <tr style="font-weight: bold; font-size: 12pt; border-top: 1px solid #cbd5e1;">
                    <td style="color: #0f766e; padding-top: 6px;">VALOR TOTAL:</td>
                    <td style="text-align: right; color: #0f766e; padding-top: 6px;">R$ {budget.get('valor_final', 0.0):,.2f}</td>
                </tr>
            </table>
        </div>

        <div style="clear: both;"></div>

        <div class="secao-titulo">3. CONDIÇÕES DE PAGAMENTO E OBSERVAÇÕES</div>
        <p style="margin: 4px 0;"><strong>Forma de Pagamento Acordada:</strong> {budget.get('forma_pagamento') or 'A combinar'}</p>
        <p style="margin: 4px 0;"><strong>Observações Clínicas:</strong> {budget.get('observacoes') or 'Nenhuma observação informada.'}</p>
        <p style="font-size: 9pt; color: #64748b; margin-top: 8px;">
            * Este orçamento possui validade de 30 (trinta) dias a contar da data de sua emissão.
            Os procedimentos propostos poderão sofrer ajustes conforme a resposta biológica individual e necessidade clínica.
        </p>

        <div class="assinaturas">
            <div class="assinatura-box" style="float: left;">
                <div class="linha-assinatura"></div>
                <strong>Dra. Lara Camila • Cirurgiã-Dentista</strong><br>
                CRO-BA 15247 • LCR Clínica Odontológica
            </div>
            <div class="assinatura-box" style="float: right;">
                <div class="linha-assinatura"></div>
                <strong>{patient.get('nome', 'Paciente')}</strong><br>
                Assinatura de Concordância do Paciente / Responsável
            </div>
            <div style="clear: both;"></div>
        </div>
    </body>
    </html>
    """
    return html
