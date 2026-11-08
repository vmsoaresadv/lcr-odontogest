import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any
from database.connection import get_db_connection
from services.audit_service import log_action

# Categorias odontológicas pré-configuradas para a LCR Clínica Odontológica
CATEGORIAS_ODONTO = [
    "Dentística e Resinas",
    "Anestésicos e Farmacologia",
    "Biossegurança e Descartáveis",
    "Endodontia",
    "Ortodontia",
    "Cirurgia e Periodontia",
    "Moldagem e Prótese",
    "Instrumentais e Brocas",
    "Prevenção e Profilaxia",
    "Geral / Outros"
]

# Unidades de medida padrão
UNIDADES_MEDIDA = [
    "Unidade",
    "Caixa",
    "Frasco",
    "Tubete / Carpule",
    "Seringa",
    "Pacote",
    "Kit",
    "Envelope",
    "Rolo",
    "Pote"
]


def list_categories() -> List[str]:
    """Retorna os nomes de todas as categorias ativas cadastradas no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM inventory_categories WHERE ativo = 1 ORDER BY nome ASC")
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return [r["nome"] for r in rows]
    return CATEGORIAS_ODONTO


def list_categories_detailed() -> List[dict]:
    """Retorna detalhes de cada categoria e a contagem de materiais vinculados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.nome, c.ativo,
               (SELECT COUNT(*) FROM inventory_items i WHERE i.categoria = c.nome AND i.ativo = 1) as total_itens
        FROM inventory_categories c
        WHERE c.ativo = 1
        ORDER BY c.nome ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_category(nome: str, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str, Optional[int]]:
    """Cadastra uma nova categoria de materiais."""
    nome = nome.strip()
    if not nome:
        return False, "O nome da categoria não pode estar vazio.", None

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, ativo FROM inventory_categories WHERE LOWER(nome) = LOWER(?)", (nome,))
        existente = cursor.fetchone()
        if existente:
            if existente["ativo"] == 0:
                cursor.execute("UPDATE inventory_categories SET ativo = 1 WHERE id = ?", (existente["id"],))
                conn.commit()
                conn.close()
                log_action(user_id, user_nome, "CATEGORIA_RESTAURADA", f"Categoria '{nome}' reativada.")
                return True, f"Categoria '{nome}' foi reativada com sucesso!", existente["id"]
            conn.close()
            return False, f"A categoria '{nome}' já existe.", None

        cursor.execute("INSERT INTO inventory_categories (nome) VALUES (?)", (nome,))
        cat_id = cursor.lastrowid
        conn.commit()
        conn.close()
        log_action(user_id, user_nome, "CATEGORIA_CRIADA", f"Nova categoria de materiais '{nome}' criada.")
        return True, f"Categoria '{nome}' criada com sucesso!", cat_id
    except Exception as e:
        return False, f"Erro ao criar categoria: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_category(cat_id: int, novo_nome: str, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str]:
    """Modifica o nome de uma categoria e atualiza em cascata nos materiais vinculados."""
    novo_nome = novo_nome.strip()
    if not novo_nome:
        return False, "O novo nome da categoria não pode estar vazio."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome FROM inventory_categories WHERE id = ?", (cat_id,))
        cat = cursor.fetchone()
        if not cat:
            conn.close()
            return False, "Categoria não encontrada."

        nome_antigo = cat["nome"]
        cursor.execute("UPDATE inventory_categories SET nome = ? WHERE id = ?", (novo_nome, cat_id))
        cursor.execute("UPDATE inventory_items SET categoria = ? WHERE categoria = ?", (novo_nome, nome_antigo))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "CATEGORIA_ATUALIZADA", f"Categoria renomeada de '{nome_antigo}' para '{novo_nome}'.")
        return True, f"Categoria alterada para '{novo_nome}' com sucesso!"
    except Exception as e:
        return False, f"Erro ao renomear categoria: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_category(cat_id: int, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str]:
    """Inativa uma categoria e remaneja seus materiais vinculados para 'Geral / Outros'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome FROM inventory_categories WHERE id = ?", (cat_id,))
        cat = cursor.fetchone()
        if not cat:
            conn.close()
            return False, "Categoria não encontrada."

        nome_cat = cat["nome"]
        if nome_cat == "Geral / Outros":
            conn.close()
            return False, "A categoria padrão 'Geral / Outros' não pode ser excluída."

        cursor.execute("UPDATE inventory_categories SET ativo = 0 WHERE id = ?", (cat_id,))
        cursor.execute("UPDATE inventory_items SET categoria = 'Geral / Outros' WHERE categoria = ?", (nome_cat,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "CATEGORIA_EXCLUIDA", f"Categoria '{nome_cat}' removida. Materiais vinculados foram movidos para 'Geral / Outros'.")
        return True, f"Categoria '{nome_cat}' removida com sucesso!"
    except Exception as e:
        return False, f"Erro ao remover categoria: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_item(
    nome: str,
    categoria: str,
    unidade: str = "Unidade",
    quantidade: float = 0.0,
    estoque_minimo: float = 1.0,
    lote: str = "",
    data_validade: str = "",
    preco_custo: float = 0.0,
    localizacao: str = "",
    fornecedor: str = "",
    observacoes: str = "",
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str, Optional[int]]:
    """Cadastra um novo material/insumo no estoque da clínica."""
    nome = nome.strip()
    categoria = categoria.strip() or "Geral / Outros"
    unidade = unidade.strip() or "Unidade"
    lote = lote.strip()
    data_validade = data_validade.strip()
    localizacao = localizacao.strip()
    fornecedor = fornecedor.strip()
    observacoes = observacoes.strip()

    if not nome:
        return False, "O nome do material é obrigatório.", None

    if quantidade < 0:
        return False, "A quantidade inicial não pode ser negativa.", None

    if estoque_minimo < 0:
        return False, "O estoque mínimo não pode ser negativo.", None

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO inventory_items (
                nome, categoria, unidade, quantidade, estoque_minimo,
                lote, data_validade, preco_custo, localizacao,
                fornecedor, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, categoria, unidade, quantidade, estoque_minimo,
            lote, data_validade, preco_custo, localizacao,
            fornecedor, observacoes
        ))
        item_id = cursor.lastrowid

        # Se foi cadastrado com quantidade > 0, cria o registro inicial no histórico
        if quantidade > 0:
            cursor.execute("""
                INSERT INTO inventory_movements (
                    item_id, tipo, quantidade, quantidade_anterior,
                    quantidade_nova, motivo, user_id, usuario_nome
                ) VALUES (?, 'Entrada', ?, 0, ?, 'Estoque Inicial no Cadastro', ?, ?)
            """, (item_id, quantidade, quantidade, user_id, user_nome))

        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "ESTOQUE_ITEM_CRIADO",
                   f"Material '{nome}' (#{item_id}) cadastrado com estoque inicial de {quantidade} {unidade}.")
        return True, f"Material '{nome}' cadastrado com sucesso!", item_id
    except Exception as e:
        return False, f"Erro ao cadastrar material: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_item(
    item_id: int,
    nome: str,
    categoria: str,
    unidade: str,
    estoque_minimo: float,
    lote: str,
    data_validade: str,
    preco_custo: float,
    localizacao: str,
    fornecedor: str,
    observacoes: str,
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """Atualiza as informações cadastrais de um material."""
    nome = nome.strip()
    categoria = categoria.strip() or "Geral / Outros"
    unidade = unidade.strip() or "Unidade"
    lote = lote.strip()
    data_validade = data_validade.strip()
    localizacao = localizacao.strip()
    fornecedor = fornecedor.strip()
    observacoes = observacoes.strip()

    if not nome:
        return False, "O nome do material é obrigatório."

    if estoque_minimo < 0:
        return False, "O estoque mínimo não pode ser negativo."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM inventory_items WHERE id = ? AND ativo = 1", (item_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Material não encontrado."

        cursor.execute("""
            UPDATE inventory_items SET
                nome = ?,
                categoria = ?,
                unidade = ?,
                estoque_minimo = ?,
                lote = ?,
                data_validade = ?,
                preco_custo = ?,
                localizacao = ?,
                fornecedor = ?,
                observacoes = ?,
                atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (
            nome, categoria, unidade, estoque_minimo,
            lote, data_validade, preco_custo, localizacao,
            fornecedor, observacoes, item_id
        ))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "ESTOQUE_ITEM_ATUALIZADO",
                   f"Dados do material '{nome}' (#{item_id}) foram atualizados.")
        return True, f"Material '{nome}' atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar material: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_item(item_id: int, user_id: Optional[int] = None, user_nome: str = "Sistema") -> Tuple[bool, str]:
    """Inativa o material do estoque (Soft Delete), preservando histórico."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM inventory_items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return False, "Material não encontrado."

        nome = item["nome"]
        cursor.execute("""
            UPDATE inventory_items 
            SET ativo = 0, atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (item_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "ESTOQUE_ITEM_EXCLUIDO",
                   f"Material '{nome}' (#{item_id}) foi removido do catálogo de estoque.")
        return True, f"Material '{nome}' removido com sucesso."
    except Exception as e:
        return False, f"Erro ao remover material: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_item(item_id: int) -> Optional[dict]:
    """Retorna um material específico pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_stock_movement(
    item_id: int,
    tipo: str,  # 'Entrada' ou 'Saida' ou 'Ajuste'
    quantidade: float,
    motivo: str = "",
    user_id: Optional[int] = None,
    user_nome: str = "Sistema"
) -> Tuple[bool, str]:
    """
    Registra uma movimentação no estoque (Entrada de compra, Saída para atendimento ou Ajuste de balanço).
    Atualiza o saldo atual e grava no histórico auditado.
    """
    tipo = tipo.capitalize()
    if tipo not in ("Entrada", "Saida", "Ajuste"):
        return False, "Tipo de movimentação inválido. Use Entrada, Saida ou Ajuste."

    if quantidade <= 0 and tipo != "Ajuste":
        return False, "A quantidade deve ser maior que zero."

    motivo = motivo.strip() or ("Compra / Reposição" if tipo == "Entrada" else "Consumo Clínico")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome, quantidade, unidade FROM inventory_items WHERE id = ? AND ativo = 1", (item_id,))
        item = cursor.fetchone()
        if not item:
            conn.close()
            return False, "Material não encontrado ou inativo."

        nome = item["nome"]
        saldo_ant = float(item["quantidade"])
        unidade = item["unidade"]

        if tipo == "Entrada":
            saldo_novo = saldo_ant + quantidade
        elif tipo == "Saida":
            if saldo_ant < quantidade:
                conn.close()
                return False, f"Saldo insuficiente! Estoque atual é de apenas {saldo_ant} {unidade}."
            saldo_novo = saldo_ant - quantidade
        else:  # Ajuste
            saldo_novo = quantidade
            quantidade_mov = abs(saldo_novo - saldo_ant)

        # 1. Atualiza quantidade no item
        cursor.execute("""
            UPDATE inventory_items
            SET quantidade = ?, atualizado_em = (datetime('now', 'localtime'))
            WHERE id = ?
        """, (saldo_novo, item_id))

        # 2. Registra na tabela de movimentações
        qtd_registrada = quantidade if tipo != "Ajuste" else (saldo_novo - saldo_ant)
        cursor.execute("""
            INSERT INTO inventory_movements (
                item_id, tipo, quantidade, quantidade_anterior,
                quantidade_nova, motivo, user_id, usuario_nome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, tipo, qtd_registrada, saldo_ant,
            saldo_novo, motivo, user_id, user_nome
        ))

        conn.commit()
        conn.close()

        acao_audit = "ESTOQUE_ENTRADA" if tipo == "Entrada" else ("ESTOQUE_SAIDA" if tipo == "Saida" else "ESTOQUE_AJUSTE")
        log_action(user_id, user_nome, acao_audit,
                   f"{tipo} de {quantidade} {unidade} no item '{nome}' (#{item_id}). Saldo anterior: {saldo_ant}, Novo saldo: {saldo_novo}. Motivo: {motivo}")

        return True, f"Movimentação registrada com sucesso! Novo saldo de '{nome}': {saldo_novo} {unidade}."
    except Exception as e:
        return False, f"Erro ao registrar movimentação: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_movements(item_id: int) -> List[dict]:
    """Retorna o histórico de movimentações de um material específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, i.nome as item_nome, i.unidade
        FROM inventory_movements m
        JOIN inventory_items i ON i.id = m.item_id
        WHERE m.item_id = ?
        ORDER BY m.id DESC
        LIMIT 200
    """, (item_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_items(
    termo: str = "",
    categoria: str = "Todas",
    filtro_alerta: str = "todos"
) -> List[dict]:
    """
    Busca materiais no estoque com suporte a filtros combinados:
    - termo: busca em tempo real por nome, lote ou fornecedor
    - categoria: filtra por categoria odontológica
    - filtro_alerta:
        'todos': todos os ativos
        'baixo': quantidade <= estoque_minimo
        'avencer': vencimento nos próximos 30 dias
        'vencido': data_validade < hoje
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = ["ativo = 1"]
    params: List[Any] = []

    # 1. Filtro por termo
    if termo and termo.strip():
        t = f"%{termo.strip()}%"
        conditions.append("(nome LIKE ? OR lote LIKE ? OR fornecedor LIKE ? OR localizacao LIKE ?)")
        params.extend([t, t, t, t])

    # 2. Filtro por Categoria
    if categoria and categoria != "Todas":
        conditions.append("categoria = ?")
        params.append(categoria)

    # 3. Filtro por Alerta
    hoje_str = date.today().strftime("%Y-%m-%d")
    em_30d_str = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

    if filtro_alerta == "baixo":
        conditions.append("quantidade <= estoque_minimo")
    elif filtro_alerta == "vencido":
        conditions.append("data_validade != '' AND data_validade < ?")
        params.append(hoje_str)
    elif filtro_alerta == "avencer":
        conditions.append("data_validade != '' AND data_validade >= ? AND data_validade <= ?")
        params.extend([hoje_str, em_30d_str])

    where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT *,
               CASE
                   WHEN data_validade != '' AND data_validade < '{hoje_str}' THEN 'vencido'
                   WHEN data_validade != '' AND data_validade <= '{em_30d_str}' THEN 'avencer'
                   WHEN quantidade <= 0 THEN 'zerado'
                   WHEN quantidade <= estoque_minimo THEN 'baixo'
                   ELSE 'ok'
               END as status_alerta
        FROM inventory_items
        {where_clause}
        ORDER BY nome ASC
    """
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_inventory_kpis() -> Dict[str, Any]:
    """Retorna os indicadores-chave de performance (KPIs) para os cards superiores."""
    conn = get_db_connection()
    cursor = conn.cursor()

    hoje_str = date.today().strftime("%Y-%m-%d")
    em_30d_str = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

    cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE ativo = 1")
    total_itens = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventory_items WHERE ativo = 1 AND quantidade <= estoque_minimo")
    estoque_baixo = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM inventory_items 
        WHERE ativo = 1 AND data_validade != '' AND data_validade <= ?
    """, (em_30d_str,))
    vencidos_ou_avencer = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantidade * preco_custo) FROM inventory_items WHERE ativo = 1")
    val = cursor.fetchone()[0]
    valor_total = float(val) if val else 0.0

    conn.close()

    return {
        "total_itens": total_itens,
        "estoque_baixo": estoque_baixo,
        "vencidos_ou_avencer": vencidos_ou_avencer,
        "valor_total": valor_total
    }
