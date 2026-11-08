import sqlite3
from datetime import datetime
from typing import List, Optional
from database.connection import get_db_connection


def log_action(user_id: Optional[int], usuario_nome: str, acao: str, detalhe: Optional[str] = None):
    """
    Grava um registro imutável na tabela de auditoria (LGPD) com horário local da clínica (Irecê - BA).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Valida se o user_id existe no banco para evitar erro de Foreign Key
        valid_user_id = None
        if user_id:
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if cursor.fetchone():
                valid_user_id = user_id

        agora_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO audit_logs (user_id, usuario_nome, acao, detalhe, data_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (valid_user_id, usuario_nome, acao, detalhe, agora_local))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao registrar log de auditoria: {e}")


def get_audit_logs(
    limit: int = 500,
    search: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
) -> List[dict]:
    """
    Recupera registros de auditoria convertidos para o horário local (Irecê - BA).
    Permite busca textual e filtros de data (início e fim no formato YYYY-MM-DD).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if data_inicio:
        conditions.append("DATE(data_hora) >= ?")
        params.append(data_inicio.strip())

    if data_fim:
        conditions.append("DATE(data_hora) <= ?")
        params.append(data_fim.strip())

    if search and search.strip():
        search_param = f"%{search.strip()}%"
        conditions.append("(usuario_nome LIKE ? OR acao LIKE ? OR detalhe LIKE ?)")
        params.extend([search_param, search_param, search_param])

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT id, user_id, usuario_nome, acao, detalhe,
               data_hora,
               DATE(data_hora) as data_dia,
               time(data_hora) as hora_min
        FROM audit_logs
        {where_clause}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(limit)
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
