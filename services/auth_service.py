import hashlib
import os
import sqlite3
from typing import Optional, Tuple, List
from database.connection import get_db_connection
from services.audit_service import log_action

try:
    import bcrypt

    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


def hash_password(password: str) -> str:
    """Gera hash seguro da senha usando bcrypt ou pbkdf2 com salt."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback de segurança com PBKDF2-HMAC-SHA256
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
        return f"pbkdf2:{salt}:{key.hex()}"


def check_password(password: str, hashed: str) -> bool:
    """Verifica se a senha fornecida confere com o hash armazenado."""
    if HAS_BCRYPT and not hashed.startswith("pbkdf2:"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
    elif hashed.startswith("pbkdf2:"):
        try:
            _, salt, key = hashed.split(":")
            check_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100000)
            return check_key.hex() == key
        except Exception:
            return False
    return False


def has_any_user() -> bool:
    """Verifica se existe ao menos um usuário cadastrado no sistema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM users")
    row = cursor.fetchone()
    conn.close()
    return bool(row and row["total"] > 0)


def create_user(
    nome: str,
    login: str,
    senha: str,
    perfil: str,
    current_admin_id: Optional[int] = None,
    current_admin_nome: Optional[str] = None
) -> Tuple[bool, str]:
    """Cadastra um novo usuário no sistema."""
    nome = nome.strip()
    login = login.strip().lower()
    perfil = perfil.strip().lower()

    if not nome or not login or not senha:
        return False, "Todos os campos são obrigatórios."

    if len(senha) < 6:
        return False, "A senha deve conter no mínimo 6 caracteres."

    if perfil not in ("admin", "secretaria"):
        return False, "Perfil inválido. Deve ser 'admin' ou 'secretaria'."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        senha_hash = hash_password(senha)
        cursor.execute("""
            INSERT INTO users (nome, login, senha_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, 1)
        """, (nome, login, senha_hash, perfil))
        user_id = cursor.lastrowid
        conn.commit()

        # Auditoria
        actor_id = current_admin_id if current_admin_id else user_id
        actor_name = current_admin_nome if current_admin_nome else nome
        acao = "PRIMEIRO_ACESSO_CRIADO" if not current_admin_id else "USUARIO_CRIADO"
        detalhe = f"Usuário '{login}' cadastrado como '{perfil}'"
        log_action(actor_id, actor_name, acao, detalhe)

        return True, "Usuário criado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"O login '{login}' já está em uso."
    except Exception as e:
        return False, f"Erro ao criar usuário: {e}"
    finally:
        conn.close()


def authenticate(login: str, senha: str) -> Tuple[Optional[dict], str]:
    """Autentica o usuário e retorna o dicionário com seus dados ou mensagem de erro."""
    login = login.strip().lower()
    if not login or not senha:
        log_action(None, login or "DESCONHECIDO", "LOGIN_FALHA", "Campos vazios")
        return None, "Informe o login e a senha."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, login, senha_hash, perfil, ativo
        FROM users
        WHERE login = ?
    """, (login,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        log_action(None, login, "LOGIN_FALHA", "Usuário não encontrado")
        return None, "Login ou senha incorretos."

    if not user["ativo"]:
        log_action(user["id"], user["nome"], "LOGIN_BLOQUEADO", "Usuário inativo")
        return None, "Este usuário foi desativado. Contate a Administradora."

    if not check_password(senha, user["senha_hash"]):
        log_action(user["id"], user["nome"], "LOGIN_FALHA", "Senha incorreta")
        return None, "Login ou senha incorretos."

    # Login bem-sucedido
    user_dict = {
        "id": user["id"],
        "nome": user["nome"],
        "login": user["login"],
        "perfil": user["perfil"],
        "ativo": user["ativo"]
    }
    log_action(user["id"], user["nome"], "LOGIN_SUCESSO", f"Sessão iniciada como {user['perfil']}")
    return user_dict, "Login efetuado com sucesso."


def list_users() -> List[dict]:
    """Lista todos os usuários cadastrados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, login, perfil, ativo, criado_em
        FROM users
        ORDER BY nome ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_user_active(user_id: int, admin_id: int, admin_nome: str) -> Tuple[bool, str]:
    """Alterna o status de ativo/inativo de um usuário (não permite desativar a si mesmo)."""
    if user_id == admin_id:
        return False, "Você não pode desativar seu próprio usuário."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, login, ativo FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, "Usuário não encontrado."

    novo_status = 0 if user["ativo"] else 1
    cursor.execute("UPDATE users SET ativo = ? WHERE id = ?", (novo_status, user_id))
    conn.commit()
    conn.close()

    status_txt = "reativado" if novo_status == 1 else "desativado"
    log_action(admin_id, admin_nome, "USUARIO_STATUS_ALTERADO", f"Usuário '{user['login']}' foi {status_txt}.")
    return True, f"Usuário {status_txt} com sucesso."


def reset_user_password(user_id: int, nova_senha: str, admin_id: int, admin_nome: str) -> Tuple[bool, str]:
    """Redefine a senha de um usuário."""
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter no mínimo 6 caracteres."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, login FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, "Usuário não encontrado."

    senha_hash = hash_password(nova_senha)
    cursor.execute("UPDATE users SET senha_hash = ? WHERE id = ?", (senha_hash, user_id))
    conn.commit()
    conn.close()

    log_action(admin_id, admin_nome, "SENHA_REDEFINIDA", f"Senha do usuário '{user['login']}' foi redefinida.")
    return True, "Senha alterada com sucesso."


def get_user_by_login(login: str) -> Optional[dict]:
    """Busca usuário pelo login (case-insensitive)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, login, perfil, ativo FROM users WHERE LOWER(login) = LOWER(?)", (login.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def recover_admin_password(login: str, chave_seguranca: str, nova_senha: str) -> Tuple[bool, str]:
    """Redefine a senha de um Administrador usando a Chave de Segurança da Clínica."""
    user = get_user_by_login(login)
    if not user:
        return False, "Usuário não encontrado."

    if user["perfil"] != "admin":
        return False, "Este usuário não é Administrador. Solicite a redefinição à Dra. Lara no menu Usuários."

    if not user["ativo"]:
        return False, "Este usuário está inativo no sistema."

    if len(nova_senha) < 6:
        return False, "A nova senha deve ter no mínimo 6 caracteres."

    # Verifica a Chave de Segurança configurada no banco (padrão LCR2026)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM clinic_settings WHERE chave = 'admin_recovery_key'")
    row = cursor.fetchone()
    chave_esperada = row["valor"] if row else "LCR2026"

    if chave_seguranca.strip() != chave_esperada.strip():
        conn.close()
        return False, "Chave de Segurança incorreta. Verifique a chave da clínica."

    senha_hash = hash_password(nova_senha)
    cursor.execute("UPDATE users SET senha_hash = ? WHERE id = ?", (senha_hash, user["id"]))
    conn.commit()
    conn.close()

    log_action(user["id"], user["nome"], "RECUPERACAO_SENHA_ADMIN", f"Senha do Administrador '{user['login']}' redefinida via Chave de Segurança.")
    return True, "Senha redefinida com sucesso! Você já pode fazer login com a nova senha."
