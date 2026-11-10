import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from database.connection import get_db_connection
from services.audit_service import log_action

FORMAS_PAGAMENTO = [
    "Pix",
    "Dinheiro",
    "Cartão de Débito",
    "Cartão de Crédito",
    "Boleto",
    "Outro"
]


# -------------------------------------------------------------
# CATEGORIAS FINANCEIRAS
# -------------------------------------------------------------

def list_financial_categories(tipo: Optional[str] = None) -> List[str]:
    """Retorna os nomes das categorias financeiras ativas, filtradas ou não por tipo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if tipo:
        cursor.execute("SELECT nome FROM financial_categories WHERE ativo = 1 AND tipo = ? ORDER BY nome ASC", (tipo,))
    else:
        cursor.execute("SELECT nome FROM financial_categories WHERE ativo = 1 ORDER BY nome ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r["nome"] for r in rows]


def list_financial_categories_detailed(tipo: Optional[str] = None) -> List[dict]:
    """Retorna dados detalhados das categorias com a contagem de transações vinculadas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT c.id, c.nome, c.tipo, c.ativo,
               (SELECT COUNT(*) FROM financial_transactions t WHERE t.categoria = c.nome) as total_lancamentos
        FROM financial_categories c
        WHERE c.ativo = 1
    """
    params = []
    if tipo:
        query += " AND c.tipo = ?"
        params.append(tipo)
    query += " ORDER BY c.tipo DESC, c.nome ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_financial_category(nome: str, tipo: str, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str, Optional[int]]:
    """Cadastra uma nova categoria financeira (Receita ou Despesa)."""
    nome = nome.strip()
    if not nome:
        return False, "O nome da categoria não pode estar vazio.", None
    if tipo not in ("Receita", "Despesa"):
        return False, "Tipo inválido. Deve ser 'Receita' ou 'Despesa'.", None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, ativo FROM financial_categories WHERE LOWER(nome) = LOWER(?) AND tipo = ?", (nome, tipo))
        existente = cursor.fetchone()
        if existente:
            if existente["ativo"] == 0:
                cursor.execute("UPDATE financial_categories SET ativo = 1 WHERE id = ?", (existente["id"],))
                conn.commit()
                conn.close()
                log_action(user_id, user_nome, "CATEGORIA_FINANCEIRA_RESTAURADA", f"Categoria '{nome}' ({tipo}) reativada.")
                return True, f"Categoria '{nome}' reativada com sucesso!", existente["id"]
            conn.close()
            return False, f"A categoria '{nome}' já existe para {tipo}.", None

        cursor.execute("INSERT INTO financial_categories (nome, tipo) VALUES (?, ?)", (nome, tipo))
        cat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        log_action(user_id, user_nome, "CATEGORIA_FINANCEIRA_CRIADA", f"Categoria '{nome}' ({tipo}) criada.")
        return True, f"Categoria '{nome}' cadastrada com sucesso!", cat_id
    except Exception as e:
        return False, f"Erro ao criar categoria: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_financial_category(cat_id: int, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str]:
    """Inativa uma categoria financeira."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome, tipo FROM financial_categories WHERE id = ?", (cat_id,))
        cat = cursor.fetchone()
        if not cat:
            conn.close()
            return False, "Categoria não encontrada."

        nome = cat["nome"]
        tipo = cat["tipo"]
        padrao = "Outras Receitas" if tipo == "Receita" else "Outras Despesas"

        if nome in ("Outras Receitas", "Outras Despesas", "Sublocação", "Sublocação de Consultório (Sala 2)"):
            conn.close()
            return False, f"A categoria do sistema '{nome}' não pode ser removida."

        cursor.execute("UPDATE financial_categories SET ativo = 0 WHERE id = ?", (cat_id,))
        cursor.execute("UPDATE financial_transactions SET categoria = ? WHERE categoria = ?", (padrao, nome))
        conn.commit()
        conn.close()
        log_action(user_id, user_nome, "CATEGORIA_FINANCEIRA_EXCLUIDA", f"Categoria '{nome}' ({tipo}) removida. Lançamentos movidos para '{padrao}'.")
        return True, f"Categoria '{nome}' removida com sucesso!"
    except Exception as e:
        return False, f"Erro ao remover categoria: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------------------------------------------
# LANÇAMENTOS FINANCEIROS / FLUXO DE CAIXA
# -------------------------------------------------------------

def create_transaction(
    tipo: str,
    categoria: str,
    descricao: str,
    valor: float,
    data_competencia: str,
    data_vencimento: Optional[str] = None,
    data_pagamento: Optional[str] = None,
    status: str = "Pago",
    forma_pagamento: str = "Pix",
    parcelas: int = 1,
    patient_id: Optional[int] = None,
    rental_id: Optional[int] = None,
    comprovante_path: Optional[str] = None,
    nota_fiscal_emitida: int = 0,
    numero_nota_fiscal: Optional[str] = None,
    recorrente: int = 0,
    dia_vencimento_recorrente: Optional[int] = None,
    observacoes: Optional[str] = None,
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str, Optional[int]]:
    """Cadastra um novo lançamento financeiro (Receita ou Despesa)."""
    descricao = descricao.strip()
    if not descricao:
        return False, "A descrição do lançamento é obrigatória.", None
    if valor <= 0:
        return False, "O valor do lançamento deve ser maior que zero.", None
    if tipo not in ("Receita", "Despesa"):
        return False, "Tipo inválido (deve ser 'Receita' ou 'Despesa').", None
    if status not in ("Pago", "Pendente", "Cancelado"):
        status = "Pago"
    if not forma_pagamento:
        forma_pagamento = "Pix"

    # Se status é pago e data de pagamento não informada, assume a data de competência
    if status == "Pago" and not data_pagamento:
        data_pagamento = data_competencia

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO financial_transactions (
                tipo, categoria, descricao, valor, data_competencia,
                data_vencimento, data_pagamento, status, forma_pagamento,
                parcelas, patient_id, rental_id, comprovante_path,
                nota_fiscal_emitida, numero_nota_fiscal, recorrente,
                observacoes, user_id, usuario_nome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo, categoria, descricao, float(valor), data_competencia,
            data_vencimento or data_competencia, data_pagamento, status,
            forma_pagamento, parcelas, patient_id, rental_id,
            comprovante_path, int(nota_fiscal_emitida or 0), numero_nota_fiscal,
            int(recorrente or 0),
            observacoes, user_id, user_nome
        ))
        trans_id = cursor.lastrowid

        # Se for recorrente mensal, registra o modelo para gerações futuras automáticas
        if recorrente:
            dia_venc = int(dia_vencimento_recorrente or (int(str(data_vencimento or data_competencia)[8:10]) if len(str(data_vencimento or data_competencia)) >= 10 else 10))
            dia_venc = max(1, min(31, dia_venc))
            cursor.execute("""
                INSERT INTO recurring_transactions (
                    tipo, categoria, descricao, valor, dia_vencimento,
                    forma_pagamento, patient_id, observacoes, ativo, ultima_geracao_mes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                tipo, categoria, descricao, float(valor), dia_venc,
                forma_pagamento, patient_id, observacoes, str(data_competencia)[:7]
            ))
            tmpl_id = cursor.lastrowid
            cursor.execute("UPDATE financial_transactions SET recorrente_template_id = ? WHERE id = ?", (tmpl_id, trans_id))

        conn.commit()
        conn.close()

        val_fmt = f"{valor:.2f}".replace('.', ',')
        nf_tag = " (NF Emitida)" if nota_fiscal_emitida else ""
        rec_tag = " [Recorrente Mensal]" if recorrente else ""
        log_action(user_id, user_nome, f"FINANCEIRO_{tipo.upper()}_CRIADA", f"{tipo} '{descricao}' de R$ {val_fmt} ({forma_pagamento}, {status}{nf_tag}{rec_tag}) lançada.")
        return True, f"{tipo} cadastrada com sucesso!", trans_id
    except Exception as e:
        return False, f"Erro ao registrar lançamento: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_transaction(
    trans_id: int,
    tipo: str,
    categoria: str,
    descricao: str,
    valor: float,
    data_competencia: str,
    data_vencimento: Optional[str] = None,
    data_pagamento: Optional[str] = None,
    status: str = "Pago",
    forma_pagamento: str = "Pix",
    parcelas: int = 1,
    patient_id: Optional[int] = None,
    comprovante_path: Optional[str] = None,
    nota_fiscal_emitida: int = 0,
    numero_nota_fiscal: Optional[str] = None,
    observacoes: Optional[str] = None,
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Atualiza os dados de um lançamento financeiro existente."""
    descricao = descricao.strip()
    if not descricao:
        return False, "A descrição do lançamento é obrigatória."
    if valor <= 0:
        return False, "O valor do lançamento deve ser maior que zero."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM financial_transactions WHERE id = ?", (trans_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Lançamento não encontrado."

        cursor.execute("""
            UPDATE financial_transactions
            SET tipo = ?, categoria = ?, descricao = ?, valor = ?,
                data_competencia = ?, data_vencimento = ?, data_pagamento = ?,
                status = ?, forma_pagamento = ?, parcelas = ?,
                patient_id = ?, comprovante_path = ?,
                nota_fiscal_emitida = ?, numero_nota_fiscal = ?,
                observacoes = ?,
                atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (
            tipo, categoria, descricao, float(valor), data_competencia,
            data_vencimento or data_competencia, data_pagamento, status,
            forma_pagamento, parcelas, patient_id, comprovante_path,
            int(nota_fiscal_emitida or 0), numero_nota_fiscal,
            observacoes, trans_id
        ))
        conn.commit()
        conn.close()

        val_fmt = f"{valor:.2f}".replace('.', ',')
        nf_tag = " [NF Emitida]" if nota_fiscal_emitida else ""
        log_action(user_id, user_nome, "FINANCEIRO_ATUALIZADO", f"Lançamento #{trans_id} atualizado: '{descricao}' (R$ {val_fmt}{nf_tag}).")
        return True, "Lançamento financeiro atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar lançamento: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_transaction(trans_id: int, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str]:
    """Exclui um lançamento financeiro."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT descricao, valor, tipo FROM financial_transactions WHERE id = ?", (trans_id,))
        t = cursor.fetchone()
        if not t:
            conn.close()
            return False, "Lançamento não encontrado."

        desc = t["descricao"]
        val = t["valor"]
        tipo = t["tipo"]

        cursor.execute("DELETE FROM financial_transactions WHERE id = ?", (trans_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "FINANCEIRO_EXCLUIDO", f"{tipo} #{trans_id} '{desc}' (R$ {val:.2f}) excluída.")
        return True, "Lançamento financeiro removido com sucesso!"
    except Exception as e:
        return False, f"Erro ao excluir lançamento: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def marcar_como_pago(
    trans_id: int,
    data_pagamento: str,
    forma_pagamento: str,
    nota_fiscal_emitida: Optional[int] = None,
    numero_nota_fiscal: Optional[str] = None,
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Baixa um lançamento pendente, registrando data e forma de pagamento efetivas."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, descricao, valor, tipo FROM financial_transactions WHERE id = ?", (trans_id,))
        t = cursor.fetchone()
        if not t:
            conn.close()
            return False, "Lançamento não encontrado."

        if nota_fiscal_emitida is not None:
            cursor.execute("""
                UPDATE financial_transactions
                SET status = 'Pago', data_pagamento = ?, forma_pagamento = ?,
                    nota_fiscal_emitida = ?, numero_nota_fiscal = ?,
                    atualizado_em = (datetime('now', 'localtime'))
                WHERE id = ?
            """, (data_pagamento, forma_pagamento, int(nota_fiscal_emitida), numero_nota_fiscal, trans_id))
        else:
            cursor.execute("""
                UPDATE financial_transactions
                SET status = 'Pago', data_pagamento = ?, forma_pagamento = ?,
                    atualizado_em = (datetime('now', 'localtime'))
                WHERE id = ?
            """, (data_pagamento, forma_pagamento, trans_id))
        conn.commit()
        conn.close()

        val_fmt = f"{t['valor']:.2f}".replace('.', ',')
        nf_tag = " (com NF-e)" if nota_fiscal_emitida else ""
        log_action(user_id, user_nome, "FINANCEIRO_BAIXA", f"Baixa efetuada em #{trans_id} '{t['descricao']}' (R$ {val_fmt}) via {forma_pagamento}{nf_tag}.")
        return True, "Lançamento marcado como Pago com sucesso!"
    except Exception as e:
        return False, f"Erro ao marcar como pago: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_transaction(trans_id: int) -> Optional[dict]:
    """Retorna os detalhes de um lançamento específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, p.nome as paciente_nome
        FROM financial_transactions t
        LEFT JOIN patients p ON t.patient_id = p.id
        WHERE t.id = ?
    """, (trans_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_transactions(
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    status: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    termo: Optional[str] = None
) -> List[dict]:
    """Consulta lançamentos com suporte flexível a filtros de período, categoria, status e busca textual."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.*, p.nome as paciente_nome
        FROM financial_transactions t
        LEFT JOIN patients p ON t.patient_id = p.id
        WHERE 1=1
    """
    params = []

    if tipo and tipo != "Todos":
        query += " AND t.tipo = ?"
        params.append(tipo)

    if categoria and categoria != "Todas as Categorias" and categoria != "Todas":
        query += " AND t.categoria = ?"
        params.append(categoria)

    if status and status != "Todos":
        query += " AND t.status = ?"
        params.append(status)

    if forma_pagamento and forma_pagamento != "Todas":
        query += " AND t.forma_pagamento = ?"
        params.append(forma_pagamento)

    if data_inicio:
        query += " AND t.data_competencia >= ?"
        params.append(data_inicio)

    if data_fim:
        query += " AND t.data_competencia <= ?"
        params.append(data_fim)

    if termo and termo.strip():
        t = f"%{termo.strip().lower()}%"
        query += " AND (LOWER(t.descricao) LIKE ? OR LOWER(t.categoria) LIKE ? OR LOWER(COALESCE(p.nome, '')) LIKE ?)"
        params.extend([t, t, t])

    query += " ORDER BY t.data_competencia DESC, t.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_financial_kpis(data_inicio: Optional[str] = None, data_fim: Optional[str] = None) -> dict:
    """Calcula os indicadores-chave financeiros do período informado."""
    conn = get_db_connection()
    cursor = conn.cursor()

    where_date = ""
    params_date = []
    if data_inicio and data_fim:
        where_date = "AND data_competencia BETWEEN ? AND ?"
        params_date = [data_inicio, data_fim]
    elif data_inicio:
        where_date = "AND data_competencia >= ?"
        params_date = [data_inicio]
    elif data_fim:
        where_date = "AND data_competencia <= ?"
        params_date = [data_fim]

    # Receitas Pagas
    cursor.execute(f"SELECT COALESCE(SUM(valor), 0.0) FROM financial_transactions WHERE tipo = 'Receita' AND status = 'Pago' {where_date}", params_date)
    total_receitas = float(cursor.fetchone()[0])

    # Despesas Pagas
    cursor.execute(f"SELECT COALESCE(SUM(valor), 0.0) FROM financial_transactions WHERE tipo = 'Despesa' AND status = 'Pago' {where_date}", params_date)
    total_despesas = float(cursor.fetchone()[0])

    # Pendente a Receber
    cursor.execute(f"SELECT COALESCE(SUM(valor), 0.0) FROM financial_transactions WHERE tipo = 'Receita' AND status = 'Pendente' {where_date}", params_date)
    pendente_receber = float(cursor.fetchone()[0])

    # Pendente a Pagar
    cursor.execute(f"SELECT COALESCE(SUM(valor), 0.0) FROM financial_transactions WHERE tipo = 'Despesa' AND status = 'Pendente' {where_date}", params_date)
    pendente_pagar = float(cursor.fetchone()[0])

    saldo_liquido = total_receitas - total_despesas

    # Total de lançamentos
    cursor.execute(f"SELECT COUNT(*) FROM financial_transactions WHERE 1=1 {where_date}", params_date)
    total_lancamentos = int(cursor.fetchone()[0])

    conn.close()
    return {
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_liquido": saldo_liquido,
        "pendente_receber": pendente_receber,
        "pendente_pagar": pendente_pagar,
        "total_lancamentos": total_lancamentos
    }


def sync_sublocacao_receita(
    rental_id: int,
    valor: float,
    data_locacao: str,
    forma_pagamento: str,
    partner_nome: str,
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Sincroniza automaticamente um pagamento recebido da Sublocação da Sala 2 no Financeiro."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verifica se já existe receita vinculada a essa locação
        cursor.execute("SELECT id FROM financial_transactions WHERE rental_id = ?", (rental_id,))
        existente = cursor.fetchone()

        desc = f"Sublocação • {partner_nome}"
        if existente:
            cursor.execute("""
                UPDATE financial_transactions
                SET valor = ?, data_competencia = ?, data_pagamento = ?,
                    forma_pagamento = ?, status = 'Pago', descricao = ?,
                    atualizado_em = (datetime('now', 'localtime'))
                WHERE id = ?
            """, (valor, data_locacao, data_locacao, forma_pagamento, desc, existente["id"]))
        else:
            cursor.execute("""
                INSERT INTO financial_transactions (
                    tipo, categoria, descricao, valor, data_competencia,
                    data_vencimento, data_pagamento, status, forma_pagamento,
                    rental_id, user_id, usuario_nome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'Receita', 'Sublocação', desc, float(valor),
                data_locacao, data_locacao, data_locacao, 'Pago', forma_pagamento,
                rental_id, user_id, user_nome
            ))

        conn.commit()
        conn.close()
        log_action(user_id, user_nome, "FINANCEIRO_SYNC_SUBLOCACAO", f"Receita de sublocação sincronizada: R$ {valor:.2f} ({forma_pagamento}).")
        return True, "Receita integrada ao financeiro com sucesso!"
    except Exception as e:
        return False, f"Erro ao integrar com financeiro: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_dre_resumido(data_inicio: Optional[str] = None, data_fim: Optional[str] = None) -> dict:
    """Gera um resumo gerencial DRE (Demonstrativo de Resultado do Exercício) agrupado por categoria."""
    conn = get_db_connection()
    cursor = conn.cursor()

    where_date = ""
    params_date = []
    if data_inicio and data_fim:
        where_date = "AND data_competencia BETWEEN ? AND ?"
        params_date = [data_inicio, data_fim]
    elif data_inicio:
        where_date = "AND data_competencia >= ?"
        params_date = [data_inicio]
    elif data_fim:
        where_date = "AND data_competencia <= ?"
        params_date = [data_fim]

    # Receitas por categoria
    cursor.execute(f"""
        SELECT categoria, SUM(valor) as total
        FROM financial_transactions
        WHERE tipo = 'Receita' AND status = 'Pago' {where_date}
        GROUP BY categoria
        ORDER BY total DESC
    """, params_date)
    receitas_cat = [dict(r) for r in cursor.fetchall()]

    # Despesas por categoria
    cursor.execute(f"""
        SELECT categoria, SUM(valor) as total
        FROM financial_transactions
        WHERE tipo = 'Despesa' AND status = 'Pago' {where_date}
        GROUP BY categoria
        ORDER BY total DESC
    """, params_date)
    despesas_cat = [dict(r) for r in cursor.fetchall()]

    # Totais por forma de pagamento
    cursor.execute(f"""
        SELECT forma_pagamento, SUM(valor) as total
        FROM financial_transactions
        WHERE status = 'Pago' {where_date}
        GROUP BY forma_pagamento
        ORDER BY total DESC
    """, params_date)
    formas_pagamento_tot = [dict(r) for r in cursor.fetchall()]

    conn.close()

    total_receitas = sum(r["total"] for r in receitas_cat)
    total_despesas = sum(d["total"] for d in despesas_cat)
    resultado_liquido = total_receitas - total_despesas

    return {
        "receitas_por_categoria": receitas_cat,
        "despesas_por_categoria": despesas_cat,
        "formas_pagamento": formas_pagamento_tot,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "resultado_liquido": resultado_liquido
    }


# =============================================================
# RECORRÊNCIA E ALERTAS AUTOMÁTICOS DE VENCIMENTO
# =============================================================

def list_recurring_templates(apenas_ativos: bool = True) -> List[dict]:
    """Lista os moldes de lançamentos recorrentes cadastrados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    filtro = "WHERE ativo = 1" if apenas_ativos else ""
    cursor.execute(f"SELECT * FROM recurring_transactions {filtro} ORDER BY dia_vencimento ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def cancel_recurring_template(template_id: int) -> bool:
    """Desativa um molde de recorrência para não gerar mais lançamentos futuros."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE recurring_transactions SET ativo = 0, atualizado_em = (datetime('now', 'localtime')) WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return True


def gerar_transacoes_recorrentes_pendentes(mes_ano_ref: Optional[str] = None) -> int:
    """
    Gera automaticamente os lançamentos pendentes das despesas/receitas recorrentes
    para o mês corrente (ou mes_ano_ref YYYY-MM), caso ainda não tenham sido gerados.
    Retorna o número de transações geradas.
    """
    if not mes_ano_ref:
        hoje = date.today()
        mes_ano_ref = hoje.strftime("%Y-%m")
    else:
        hoje = datetime.strptime(f"{mes_ano_ref}-01", "%Y-%m-%d").date()

    ano = hoje.year
    mes = hoje.month

    conn = get_db_connection()
    cursor = conn.cursor()
    gerados = 0
    try:
        cursor.execute("SELECT * FROM recurring_transactions WHERE ativo = 1")
        templates = [dict(r) for r in cursor.fetchall()]
        for tmpl in templates:
            # Verifica se já gerou para este mês
            cursor.execute("""
                SELECT id FROM financial_transactions
                WHERE recorrente_template_id = ?
                  AND strftime('%Y-%m', data_competencia) = ?
            """, (tmpl["id"], mes_ano_ref))
            if cursor.fetchone():
                continue  # Já existe transação gerada para este mês

            # Calcula o dia limite do mês
            dia_venc = min(tmpl["dia_vencimento"], 28 if mes == 2 else 30)
            try:
                dt_venc = date(ano, mes, dia_venc)
            except ValueError:
                dt_venc = date(ano, mes, 28)

            dt_comp = date(ano, mes, 1)

            cursor.execute("""
                INSERT INTO financial_transactions (
                    tipo, categoria, descricao, valor, data_competencia,
                    data_vencimento, data_pagamento, status, forma_pagamento,
                    parcelas, patient_id, recorrente, recorrente_template_id,
                    observacoes, usuario_nome
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, 'Pendente', ?, 1, ?, 1, ?, ?, 'Recorrência Automática')
            """, (
                tmpl["tipo"], tmpl["categoria"], tmpl["descricao"],
                float(tmpl["valor"]), dt_comp.isoformat(),
                dt_venc.isoformat(), tmpl["forma_pagamento"],
                tmpl.get("patient_id"), tmpl["id"],
                tmpl.get("observacoes") or "Lançamento recorrente mensal gerado automaticamente."
            ))
            cursor.execute("""
                UPDATE recurring_transactions
                SET ultima_geracao_mes = ?, atualizado_em = (datetime('now', 'localtime'))
                WHERE id = ?
            """, (mes_ano_ref, tmpl["id"]))
            gerados += 1

        conn.commit()
    except Exception as e:
        print(f"Erro ao gerar recorrentes: {e}")
    finally:
        conn.close()

    return gerados


def verificar_alertas_vencimento(dias_antecedencia: int = 1) -> List[dict]:
    """
    Retorna contas a pagar (e a receber) pendentes que:
    1. Já venceram (atrasadas)
    2. Vencem hoje
    3. Vencem nos próximos `dias_antecedencia` dias (ex: amanhã)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje = date.today()
    limite = hoje + timedelta(days=dias_antecedencia)
    limite_str = limite.isoformat()

    try:
        cursor.execute("""
            SELECT t.*, p.nome as paciente_nome, p.telefone as paciente_telefone
            FROM financial_transactions t
            LEFT JOIN patients p ON t.patient_id = p.id
            WHERE t.status = 'Pendente'
              AND t.data_vencimento IS NOT NULL
              AND t.data_vencimento <= ?
            ORDER BY t.tipo DESC, t.data_vencimento ASC
        """, (limite_str,))
        rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            venc_str = str(r["data_vencimento"])[:10]
            try:
                dt_v = datetime.strptime(venc_str, "%Y-%m-%d").date()
                diff = (dt_v - hoje).days
                if diff < 0:
                    r["urgencia"] = "vencida"
                    r["urgencia_label"] = f"⚠️ Vencida há {abs(diff)} dia(s)"
                    r["cor_badge"] = "#dc2626"
                elif diff == 0:
                    r["urgencia"] = "hoje"
                    r["urgencia_label"] = "🚨 Vence Hoje!"
                    r["cor_badge"] = "#ea580c"
                else:
                    r["urgencia"] = "amanha"
                    r["urgencia_label"] = f"⏳ Vence amanhã ({dt_v.strftime('%d/%m')})"
                    r["cor_badge"] = "#0284c7"
            except Exception:
                r["urgencia"] = "indefinida"
                r["urgencia_label"] = "Pendente"
                r["cor_badge"] = "#64748b"

        return rows
    except Exception as e:
        print(f"Erro ao verificar alertas de vencimento: {e}")
        return []
    finally:
        conn.close()
