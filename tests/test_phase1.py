import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# database test override
import database.connection as db_conn
TEST_DB_PATH = BASE_DIR / "data" / "test_clinica.db"
db_conn.DB_PATH = TEST_DB_PATH

from database.connection import init_db, get_db_connection
from services.auth_service import (
    has_any_user, create_user, authenticate,
    list_users, toggle_user_active, reset_user_password
)
from services.audit_service import get_audit_logs, log_action


def test_phase1():
    print("--- INICIANDO TESTES AUTOMATIZADOS DA FASE 1 ---")

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    # 1. Testar inicialização do banco
    init_db()
    assert TEST_DB_PATH.exists(), f"Erro: {TEST_DB_PATH} não foi criado."
    print("[OK] Banco de dados SQLite criado com sucesso em data/test_clinica.db")

    # 2. Testar primeiro acesso
    print(f"Existe algum usuario no banco? {has_any_user()}")

    # 3. Criar primeiro Administrador
    ok, msg = create_user("Dra. Larissa", "larissa.admin", "senha123", "admin")
    assert ok, f"Falha ao criar admin: {msg}"
    print("[OK] Administradora inicial criada com sucesso.")

    # 4. Criar Secretaria
    admin_user = list_users()[0]
    ok, msg = create_user("Ana Recepcao", "ana.secretaria", "senha123", "secretaria",
                          current_admin_id=admin_user["id"], current_admin_nome=admin_user["nome"])
    assert ok, f"Falha ao criar secretaria: {msg}"
    print("[OK] Usuario Secretaria criada com sucesso pelo Admin.")

    # 5. Testar Autenticacao valida e invalida
    user_admin, msg = authenticate("larissa.admin", "senha123")
    assert user_admin is not None, f"Falha no login do admin: {msg}"
    assert user_admin["perfil"] == "admin"
    print("[OK] Autenticacao de Administrador bem-sucedida.")

    user_sec, msg = authenticate("ana.secretaria", "senha123")
    assert user_sec is not None, f"Falha no login da secretaria: {msg}"
    assert user_sec["perfil"] == "secretaria"
    print("[OK] Autenticacao de Secretaria bem-sucedida.")

    user_fail, msg = authenticate("larissa.admin", "senha_errada")
    assert user_fail is None, "Deveria ter falhado com senha errada!"
    print("[OK] Rejeicao de senha invalida funcionando perfeitamente.")

    # 6. Testar Desativacao de Usuario
    sec_id = user_sec["id"]
    ok, msg = toggle_user_active(sec_id, admin_user["id"], admin_user["nome"])
    assert ok, msg
    # Tentativa de login de usuario inativo
    user_blocked, msg = authenticate("ana.secretaria", "senha123")
    assert user_blocked is None, "Usuario desativado nao pode conseguir logar!"
    print("[OK] Bloqueio de usuario desativado funcionando.")

    # Reativar
    toggle_user_active(sec_id, admin_user["id"], admin_user["nome"])
    user_reok, msg = authenticate("ana.secretaria", "senha123")
    assert user_reok is not None
    print("[OK] Reativacao de usuario funcionando.")

    # 7. Testar Redefinicao de Senha
    ok, msg = reset_user_password(sec_id, "nova_senha456", admin_user["id"], admin_user["nome"])
    assert ok, msg
    user_newpass, msg = authenticate("ana.secretaria", "nova_senha456")
    assert user_newpass is not None
    print("[OK] Redefinicao de senha funcionando.")

    # 8. Testar Trilha de Auditoria (LGPD)
    logs = get_audit_logs()
    assert len(logs) > 0, "Deveria haver logs registrados."
    print(f"[OK] Trilha de auditoria LGPD gravou {len(logs)} eventos.")
    for l in logs[:5]:
        print(f"   [{l['data_hora']}] {l['usuario_nome']} -> {l['acao']}: {l['detalhe']}")

    print("\n--- TODOS OS TESTES DE BACKEND E SEGURANÇA FORAM APROVADOS! ---")


if __name__ == "__main__":
    test_phase1()
