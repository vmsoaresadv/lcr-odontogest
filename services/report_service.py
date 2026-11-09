import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

from PySide6.QtGui import QTextDocument, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QSizeF, QMarginsF

from database.connection import get_db_connection
from services.financial_service import get_dre_resumido, search_transactions
from services.inventory_service import search_items, get_inventory_kpis
from services.patient_service import (
    get_patient_anamnese, get_patient_odontograma,
    NOMES_DENTES, STATUS_DENTE_CORES
)
from services.audit_service import log_action
from version import APP_NAME, CLINICA_NOME, RESPONSAVEL_NOME, RESPONSAVEL_CRO, CIDADE_ESTADO

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo_clean.png"


def gerar_cabecalho_html(titulo_documento: str) -> str:
    """Gera o cabeçalho oficial padronizado com a marca da Dra. Lara Camila."""
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    return f"""
    <div style="border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 22px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="vertical-align: middle;">
                    <div style="font-size: 20pt; font-weight: bold; color: #0f766e; font-family: 'Segoe UI', Arial, sans-serif;">
                        {CLINICA_NOME}
                    </div>
                    <div style="font-size: 12pt; color: #475569; font-family: 'Segoe UI', Arial, sans-serif; margin-top: 3px;">
                        <strong>{RESPONSAVEL_NOME}</strong> • {RESPONSAVEL_CRO} • {CIDADE_ESTADO}
                    </div>
                </td>
                <td style="text-align: right; vertical-align: middle;">
                    <div style="font-size: 16pt; font-weight: bold; color: #1e293b; font-family: 'Segoe UI', Arial, sans-serif;">
                        {titulo_documento}
                    </div>
                    <div style="font-size: 11pt; color: #64748b; font-family: 'Segoe UI', Arial, sans-serif; margin-top: 4px;">
                        Emissão: {agora_str}
                    </div>
                </td>
            </tr>
        </table>
    </div>
    """


def gerar_rodape_html() -> str:
    """Gera o rodapé com assinatura profissional e proteção LGPD."""
    return f"""
    <div style="margin-top: 40px; border-top: 1px solid #cbd5e1; padding-top: 16px; text-align: center; font-family: 'Segoe UI', Arial, sans-serif;">
        <div style="margin-top: 25px; margin-bottom: 8px; font-size: 12pt; color: #64748b;">
            _____________________________________________________________
        </div>
        <div style="font-size: 13pt; font-weight: bold; color: #1e293b;">
            {RESPONSAVEL_NOME}
        </div>
        <div style="font-size: 12pt; color: #64748b;">
            Cirurgiã-Dentista • {RESPONSAVEL_CRO}
        </div>
        <div style="margin-top: 16px; font-size: 10pt; color: #94a3b8;">
            Documento emitido pelo sistema {APP_NAME}. Uso exclusivo e confidencial em conformidade com a LGPD (Lei 13.709/2018).
        </div>
    </div>
    """


def gerar_html_ficha_paciente(paciente_id: int) -> str:
    """Gera a Ficha Cadastral, Anamnese, Odontograma e Histórico Clínico do Paciente para Impressão/PDF."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE id = ?", (paciente_id,))
        p = cursor.fetchone()
        if not p:
            return "<h1>Paciente não encontrado.</h1>"

        p_dict = dict(p)

        cursor.execute("""
            SELECT *
            FROM patient_records
            WHERE patient_id = ?
            ORDER BY data_hora DESC
        """, (paciente_id,))
        prontuarios = [dict(row) for row in cursor.fetchall()]

    cabecalho = gerar_cabecalho_html(f"Prontuário Odontológico #{p_dict['id']}")

    nasc = p_dict.get("data_nascimento") or "Não informada"
    if nasc and len(nasc) == 10 and "-" in nasc:
        nasc = datetime.strptime(nasc, "%Y-%m-%d").strftime("%d/%m/%Y")

    # Carrega Anamnese e Odontograma
    anamnese = get_patient_anamnese(paciente_id)
    odonto = get_patient_odontograma(paciente_id)

    # Formatação de Doenças Sistêmicas
    doencas = []
    if anamnese.get("hipertensao"): doencas.append("<strong style='color:#e11d48;'>Hipertensão Arterial</strong>")
    if anamnese.get("diabetes"): doencas.append("<strong style='color:#a16207;'>Diabetes Mellitus</strong>")
    if anamnese.get("cardiopatia"): doencas.append("<strong style='color:#be185d;'>Cardiopatia</strong>")
    if anamnese.get("problema_coagulacao"): doencas.append("<strong style='color:#c2410c;'>Distúrbio de Coagulação</strong>")
    if anamnese.get("doenca_renal_hepatica"): doencas.append("Doença Renal/Hepática")
    if anamnese.get("gestante_lactante"): doencas.append("Gestante/Lactante")
    if anamnese.get("fumante"): doencas.append("Fumante")
    if anamnese.get("bruxismo"): doencas.append("Bruxismo/Apertamento")
    str_doencas = ", ".join(doencas) if doencas else "Nenhuma doença sistêmica relatada"

    alergias_txt = anamnese.get("alergias_medicamentos") or p_dict.get("alergias") or "Nenhuma alergia relatada"
    if anamnese.get("alergia_latex"):
        alergias_txt += " (Alérgico a Látex)"

    meds_txt = anamnese.get("medicamentos_uso") or "Nenhum medicamento contínuo relatado"
    queixa_txt = anamnese.get("queixa_principal") or "Consulta e avaliação geral"

    # Linhas do Odontograma (dentes com anotações)
    linhas_odonto = ""
    dentes_alterados = [d for d in odonto.values() if d.get("status") != "higido"]
    if not dentes_alterados:
        linhas_odonto = """
        <tr>
            <td colspan="4" style="text-align: center; color: #166260; padding: 10px; font-size: 11pt; background-color: #f0fdf4;">
                ✓ Todos os 32 dentes registrados como <strong>Hígidos / Sadios</strong> no momento do exame.
            </td>
        </tr>
        """
    else:
        for d in sorted(dentes_alterados, key=lambda x: x["numero_dente"]):
            num = d["numero_dente"]
            nome_d = NOMES_DENTES.get(num, f"Dente {num}")
            st_cfg = STATUS_DENTE_CORES.get(d["status"], STATUS_DENTE_CORES["higido"])
            faces_str = d.get("faces") or "-"
            obs_d = d.get("observacoes") or "-"

            linhas_odonto += f"""
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 6px 8px; font-size: 11pt; font-weight: bold;">Dente {num}</td>
                <td style="padding: 6px 8px; font-size: 11pt; color: #475569;">{nome_d}</td>
                <td style="padding: 6px 8px; font-size: 11pt; font-weight: bold; color: {st_cfg['cor']};">{st_cfg['nome']} (Faces: {faces_str})</td>
                <td style="padding: 6px 8px; font-size: 11pt; color: #334155;">{obs_d}</td>
            </tr>
            """

    linhas_atendimentos = ""
    if not prontuarios:
        linhas_atendimentos = """
        <tr>
            <td colspan="4" style="text-align: center; color: #64748b; padding: 14px; font-size: 12pt;">
                Nenhum atendimento ou procedimento registrado até o momento.
            </td>
        </tr>
        """
    else:
        for item in prontuarios:
            dh = item.get("data_hora", "")
            dh_fmt = dh
            try:
                dt_obj = datetime.strptime(dh[:19], "%Y-%m-%d %H:%M:%S")
                dh_fmt = dt_obj.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                pass

            procedimento = item.get("procedimento") or "Consulta Geral"
            descricao = item.get("descricao") or "-"
            dentista = item.get("profissional_nome") or RESPONSAVEL_NOME
            dente = item.get("dente_regiao") or "Geral"

            linhas_atendimentos += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 6px; font-size: 11pt; color: #334155;">{dh_fmt}</td>
                <td style="padding: 8px 6px; font-size: 11pt; font-weight: bold; color: #0f766e;">{procedimento} ({dente})</td>
                <td style="padding: 8px 6px; font-size: 11pt; color: #1e293b;">{descricao}</td>
                <td style="padding: 8px 6px; font-size: 11pt; color: #475569;">{dentista}</td>
            </tr>
            """

    corpo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12pt; color: #0f172a; margin: 10px; }}
            .secao-titulo {{ font-size: 13pt; font-weight: bold; color: #0f766e; background-color: #f0fdfa; padding: 7px 12px; border-left: 5px solid #0d9488; margin-top: 16px; margin-bottom: 10px; }}
            table.info-tabela {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
            table.info-tabela td {{ padding: 6px 8px; font-size: 12pt; }}
            table.grade-tabela {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
            table.grade-tabela th {{ background-color: #f8fafc; color: #334155; font-size: 11pt; font-weight: bold; text-align: left; padding: 8px 6px; border-bottom: 2px solid #cbd5e1; }}
        </style>
    </head>
    <body>
        {cabecalho}

        <div class="secao-titulo">1. DADOS CADASTRAIS DO PACIENTE</div>
        <table class="info-tabela">
            <tr>
                <td style="width: 50%;"><strong>Nome Completo:</strong> {p_dict.get('nome', '')}</td>
                <td style="width: 50%;"><strong>CPF:</strong> {p_dict.get('cpf') or 'Não informado'}</td>
            </tr>
            <tr>
                <td><strong>Data de Nascimento:</strong> {nasc}</td>
                <td><strong>Telefone / WhatsApp:</strong> {p_dict.get('telefone') or 'Não informado'}</td>
            </tr>
            <tr>
                <td><strong>Profissão:</strong> {p_dict.get('profissao') or 'Não informada'}</td>
                <td><strong>Endereço:</strong> {p_dict.get('endereco') or 'Não informado'}</td>
            </tr>
        </table>

        <div class="secao-titulo">2. ANAMNESE CLÍNICA E HISTÓRICO DE SAÚDE</div>
        <table class="info-tabela">
            <tr>
                <td colspan="2"><strong>Queixa Principal / Motivo:</strong> {queixa_txt}</td>
            </tr>
            <tr>
                <td style="width: 50%;">
                    <strong style="color: #dc2626;">Alergias / Restrições:</strong><br>
                    <span style="color: #7f1d1d; font-size: 11pt;">{alergias_txt}</span>
                </td>
                <td style="width: 50%;">
                    <strong>Condições / Doenças Sistêmicas:</strong><br>
                    <span style="font-size: 11pt;">{str_doencas}</span>
                </td>
            </tr>
            <tr>
                <td colspan="2">
                    <strong>Medicamentos em Uso Contínuo:</strong> {meds_txt}
                </td>
            </tr>
        </table>

        <div class="secao-titulo">3. ODONTOGRAMA (MAPA DE DENTES E INTERVENÇÕES)</div>
        <table class="grade-tabela">
            <thead>
                <tr>
                    <th style="width: 15%;">Dente</th>
                    <th style="width: 30%;">Nome Anatômico</th>
                    <th style="width: 30%;">Condição Clínica / Faces</th>
                    <th style="width: 25%;">Observações</th>
                </tr>
            </thead>
            <tbody>
                {linhas_odonto}
            </tbody>
        </table>

        <div class="secao-titulo">4. HISTÓRICO DE PROCEDIMENTOS E EVOLUÇÕES CLÍNICAS</div>
        <table class="grade-tabela">
            <thead>
                <tr>
                    <th style="width: 20%;">Data / Hora</th>
                    <th style="width: 30%;">Procedimento (Região)</th>
                    <th style="width: 32%;">Evolução Clínica</th>
                    <th style="width: 18%;">Profissional</th>
                </tr>
            </thead>
            <tbody>
                {linhas_atendimentos}
            </tbody>
        </table>

        {gerar_rodape_html()}
    </body>
    </html>
    """
    return corpo


def gerar_html_dre_financeiro(data_inicio: str, data_fim: str) -> str:
    """Gera o Demonstrativo de Resultados do Exercício (DRE) do Período."""
    resumo = get_dre_resumido(data_inicio, data_fim)
    transacoes = search_transactions(data_inicio=data_inicio, data_fim=data_fim)

    dt_ini_fmt = datetime.strptime(data_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
    dt_fim_fmt = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")

    cabecalho = gerar_cabecalho_html(f"Demonstrativo Financeiro ({dt_ini_fmt} a {dt_fim_fmt})")

    total_rec = resumo.get("total_receitas", 0.0)
    total_desp = resumo.get("total_despesas", 0.0)
    saldo_liq = resumo.get("resultado_liquido", 0.0)

    # Detalhamento por categorias
    rec_cats_html = ""
    for rc in resumo.get("receitas_por_categoria", []):
        rec_cats_html += f"""
        <tr>
            <td style="padding: 7px 10px; font-size: 12pt; color: #334155;">{rc['categoria']}</td>
            <td style="padding: 7px 10px; font-size: 12pt; text-align: right; color: #16a34a; font-weight: bold;">R$ {rc['total']:,.2f}</td>
        </tr>
        """
    if not rec_cats_html:
        rec_cats_html = "<tr><td colspan='2' style='padding:7px 10px; font-size:12pt; color:#64748b;'>Nenhuma receita no período</td></tr>"

    desp_cats_html = ""
    for dc in resumo.get("despesas_por_categoria", []):
        desp_cats_html += f"""
        <tr>
            <td style="padding: 7px 10px; font-size: 12pt; color: #334155;">{dc['categoria']}</td>
            <td style="padding: 7px 10px; font-size: 12pt; text-align: right; color: #dc2626; font-weight: bold;">- R$ {dc['total']:,.2f}</td>
        </tr>
        """
    if not desp_cats_html:
        desp_cats_html = "<tr><td colspan='2' style='padding:7px 10px; font-size:12pt; color:#64748b;'>Nenhuma despesa no período</td></tr>"

    # Linhas de transações detalhadas
    linhas_t = ""
    for t in transacoes:
        cor_tipo = "#16a34a" if t.get("tipo") == "Receita" else "#dc2626"
        sinal = "+" if t.get("tipo") == "Receita" else "-"
        tipo_str = t.get("tipo", "Transação")
        dt_t = t.get("data_competencia") or t.get("data_vencimento") or ""
        if dt_t and len(dt_t) == 10 and "-" in dt_t:
            dt_t = datetime.strptime(dt_t, "%Y-%m-%d").strftime("%d/%m/%Y")

        linhas_t += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 8px; font-size: 11pt;">{dt_t}</td>
            <td style="padding: 8px; font-size: 11pt; font-weight: bold; color: {cor_tipo};">{tipo_str}</td>
            <td style="padding: 8px; font-size: 11pt;">{t.get('categoria', '-')}</td>
            <td style="padding: 8px; font-size: 11pt;">{t.get('descricao', '-')}</td>
            <td style="padding: 8px; font-size: 11pt; text-align: right; font-weight: bold; color: {cor_tipo};">
                {sinal} R$ {t.get('valor', 0.0):,.2f}
            </td>
        </tr>
        """

    corpo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12pt; color: #0f172a; margin: 10px; }}
            .card-resumo {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-bottom: 20px; background-color: #f8fafc; }}
            table.tabela-resumo {{ width: 100%; border-collapse: collapse; }}
            table.tabela-resumo td {{ padding: 8px 10px; font-size: 12pt; }}
            table.tabela-extrato {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
            table.tabela-extrato th {{ background-color: #f1f5f9; color: #334155; font-size: 12pt; font-weight: bold; padding: 10px 8px; text-align: left; border-bottom: 2px solid #cbd5e1; }}
        </style>
    </head>
    <body>
        {cabecalho}

        <div class="card-resumo">
            <table class="tabela-resumo">
                <tr style="background-color: #f0fdfa;">
                    <td colspan="2" style="font-weight: bold; color: #0f766e; font-size: 13pt; padding: 8px 10px;">1. RECEITAS DO PERÍODO</td>
                </tr>
                {rec_cats_html}
                <tr style="border-top: 1px dashed #cbd5e1; border-bottom: 2px solid #cbd5e1;">
                    <td style="padding: 10px; font-size: 13pt;"><strong>TOTAL DE RECEITAS BRUTAS:</strong></td>
                    <td style="text-align: right; color: #16a34a; font-weight: bold; font-size: 14pt; padding: 10px;">R$ {total_rec:,.2f}</td>
                </tr>
                <tr style="background-color: #fef2f2;">
                    <td colspan="2" style="font-weight: bold; color: #991b1b; font-size: 13pt; padding: 10px 10px 8px 10px;">2. DESPESAS E CUSTOS OPERACIONAIS</td>
                </tr>
                {desp_cats_html}
                <tr style="border-top: 1px dashed #cbd5e1; border-bottom: 2px solid #cbd5e1;">
                    <td style="padding: 10px; font-size: 13pt;"><strong>TOTAL DE DESPESAS:</strong></td>
                    <td style="text-align: right; color: #dc2626; font-weight: bold; font-size: 14pt; padding: 10px;">- R$ {total_desp:,.2f}</td>
                </tr>
                <tr style="border-top: 3px solid #0d9488; background-color: #ffffff;">
                    <td style="padding: 14px 10px; font-size: 15pt;"><strong>RESULTADO LÍQUIDO DO PERÍODO:</strong></td>
                    <td style="text-align: right; color: {'#16a34a' if saldo_liq >= 0 else '#dc2626'}; font-weight: bold; font-size: 16pt; padding: 14px 10px;">
                        R$ {saldo_liq:,.2f}
                    </td>
                </tr>
            </table>
        </div>

        <div style="font-size: 13pt; font-weight: bold; color: #0f766e; margin-top: 24px; margin-bottom: 8px;">LANÇAMENTOS DISCRIMINADOS DO PERÍODO</div>
        <table class="tabela-extrato">
            <thead>
                <tr>
                    <th style="width: 14%;">Data</th>
                    <th style="width: 12%;">Tipo</th>
                    <th style="width: 25%;">Categoria</th>
                    <th style="width: 34%;">Descrição</th>
                    <th style="width: 15%; text-align: right;">Valor (R$)</th>
                </tr>
            </thead>
            <tbody>
                {linhas_t if linhas_t else '<tr><td colspan="5" style="text-align:center; padding:16px; color:#64748b; font-size:12pt;">Nenhuma movimentação financeira no período selecionado.</td></tr>'}
            </tbody>
        </table>

        {gerar_rodape_html()}
    </body>
    </html>
    """
    return corpo


def gerar_html_relatorio_estoque() -> str:
    """Gera o Relatório de Posição de Estoque e Validades de Materiais."""
    produtos = search_items()
    resumo = get_inventory_kpis()

    cabecalho = gerar_cabecalho_html("Posição Geral de Estoque e Validades")

    linhas_p = ""
    for p in produtos:
        cor_status = "#16a34a"
        rotulo_status = "✓ Normal"
        alerta = p.get("status_alerta", "ok")
        if alerta == "baixo":
            cor_status = "#dc2626"
            rotulo_status = "⚠ Repor Estoque"
        elif alerta == "vencido":
            cor_status = "#991b1b"
            rotulo_status = "❌ Vencido"
        elif alerta == "a_vencer":
            cor_status = "#d97706"
            rotulo_status = "⏰ A Vencer"

        val_fmt = p.get("data_validade", "")
        if val_fmt and len(val_fmt) == 10 and "-" in val_fmt:
            val_fmt = datetime.strptime(val_fmt, "%Y-%m-%d").strftime("%d/%m/%Y")

        linhas_p += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 8px 10px; font-size: 11pt; font-weight: bold;">{p['nome']}</td>
            <td style="padding: 8px 10px; font-size: 11pt; color: #475569;">{p.get('categoria', '-')}</td>
            <td style="padding: 8px 10px; font-size: 11pt; text-align: center;">{p.get('quantidade', 0)} {p.get('unidade', 'un')}</td>
            <td style="padding: 8px 10px; font-size: 11pt; text-align: center;">{val_fmt or '-'}</td>
            <td style="padding: 8px 10px; font-size: 11pt; text-align: right;">R$ {p.get('preco_custo', 0.0):,.2f}</td>
            <td style="padding: 8px 10px; font-size: 11pt; font-weight: bold; color: {cor_status};">{rotulo_status}</td>
        </tr>
        """

    corpo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12pt; color: #0f172a; margin: 10px; }}
            .card-metricas {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            .card-metricas td {{ padding: 12px; background-color: #f8fafc; border: 1px solid #e2e8f0; text-align: center; }}
            table.tabela-itens {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
            table.tabela-itens th {{ background-color: #f1f5f9; color: #334155; font-size: 12pt; font-weight: bold; padding: 10px 8px; text-align: left; border-bottom: 2px solid #cbd5e1; }}
        </style>
    </head>
    <body>
        {cabecalho}

        <table class="card-metricas">
            <tr>
                <td style="width: 25%;">
                    <div style="font-size: 11pt; color: #64748b;">Total de Itens</div>
                    <div style="font-size: 17pt; font-weight: bold; color: #0f766e; margin-top: 4px;">{resumo.get('total_itens', 0)} itens</div>
                </td>
                <td style="width: 25%;">
                    <div style="font-size: 11pt; color: #64748b;">Valor Total em Estoque</div>
                    <div style="font-size: 17pt; font-weight: bold; color: #0d9488; margin-top: 4px;">R$ {resumo.get('valor_total', 0.0):,.2f}</div>
                </td>
                <td style="width: 25%;">
                    <div style="font-size: 11pt; color: #64748b;">Estoque Crítico</div>
                    <div style="font-size: 17pt; font-weight: bold; color: #dc2626; margin-top: 4px;">{resumo.get('estoque_baixo', 0)} itens</div>
                </td>
                <td style="width: 25%;">
                    <div style="font-size: 11pt; color: #64748b;">A Vencer / Vencidos</div>
                    <div style="font-size: 17pt; font-weight: bold; color: #d97706; margin-top: 4px;">{resumo.get('vencidos_ou_avencer', 0)} itens</div>
                </td>
            </tr>
        </table>

        <div style="font-size: 13pt; font-weight: bold; color: #0f766e; margin-top: 20px; margin-bottom: 8px;">LISTA COMPLETA DE MATERIAIS ODONTOLÓGICOS</div>
        <table class="tabela-itens">
            <thead>
                <tr>
                    <th style="width: 30%;">Material / Produto</th>
                    <th style="width: 20%;">Categoria</th>
                    <th style="width: 15%; text-align: center;">Qtd Atual</th>
                    <th style="width: 12%; text-align: center;">Validade</th>
                    <th style="width: 11%; text-align: right;">Custo (R$)</th>
                    <th style="width: 12%;">Situação</th>
                </tr>
            </thead>
            <tbody>
                {linhas_p}
            </tbody>
        </table>

        {gerar_rodape_html()}
    </body>
    </html>
    """
    return corpo


def exportar_html_para_pdf(html_content: str, output_pdf_path: str) -> bool:
    """
    Renderiza o HTML formatado e exporta nativamente para arquivo PDF vetorial em tamanho A4 real.
    Garante legibilidade padrão (fonte 12pt) e margens proporcionais.
    """
    try:
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_pdf_path)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

        doc = QTextDocument()
        doc.setPageSize(printer.pageRect(QPrinter.Unit.DevicePixel).size())
        doc.setHtml(html_content)
        doc.print_(printer)
        return True
    except Exception as e:
        print(f"Erro na geração de PDF: {e}")
        return False
