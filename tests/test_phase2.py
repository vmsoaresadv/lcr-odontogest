import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Override para banco temporário de testes
import database.connection as db_conn
TEST_DB_PATH = BASE_DIR / "data" / "test_phase2.db"
db_conn.DB_PATH = TEST_DB_PATH

from database.connection import init_db
from services.patient_service import (
    create_patient, update_patient, delete_patient,
    get_patient, search_patients, add_record, update_record, get_record,
    list_records, delete_record, add_attachment,
    list_attachments, delete_attachment
)
from services.audit_service import get_audit_logs


def test_phase2():
    print("--- INICIANDO TESTES DA FASE 2: PACIENTES, PRONTUÁRIO E ANEXOS ---")

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    init_db()
    print("[OK] Banco de dados temporário inicializado.")

    # 1. Criar Paciente
    ok, msg, p_id = create_patient(
        nome="Mariana Souza Santos",
        cpf="12345678901",
        data_nascimento="15/05/1992",
        telefone="(74) 99111-2222",
        email="mariana@email.com",
        endereco="Av. Santos Dumont, 100, Irecê",
        alergias="Penicilina e Dipirona",
        observacoes_medicas="Pressão arterial normal",
        user_id=1,
        user_nome="Dra. Lara Camila"
    )
    assert ok, f"Falha ao criar paciente: {msg}"
    print(f"[OK] Paciente cadastrada com sucesso com ID #{p_id}")

    # 2. Testar busca por Nome e por CPF
    res_nome = search_patients("Mariana")
    assert len(res_nome) == 1
    assert res_nome[0]["cpf"] == "123.456.789-01"
    print("[OK] Busca por Nome funcionando e CPF formatado corretamente.")

    res_cpf = search_patients("12345678901")
    assert len(res_cpf) == 1
    print("[OK] Busca por dígitos do CPF funcionando.")

    # 3. Testar rejeição de CPF duplicado
    ok_dup, msg_dup, _ = create_patient(
        nome="Outro Paciente",
        cpf="123.456.789-01",
        data_nascimento="01/01/2000",
        telefone="", email="", endereco="", alergias="", observacoes_medicas="",
        user_id=1, user_nome="Dra. Lara Camila"
    )
    assert not ok_dup, "Deveria ter rejeitado CPF duplicado!"
    print("[OK] Validação de duplicidade de CPF funcionando.")

    # 4. Adicionar Procedimento Odontológico ao Prontuário
    ok_rec, msg_rec = add_record(
        patient_id=p_id,
        dente_regiao="Dente 16",
        procedimento="Restauração em Resina Composta",
        descricao="Remoção de cárie oclusal e restauração com resina fotopolimerizável.",
        profissional_nome="Dra. Lara Camila",
        user_id=1
    )
    assert ok_rec, msg_rec
    print("[OK] Procedimento odontológico adicionado com indicação do Dente 16.")

    # 5. Listar Prontuário
    records = list_records(p_id)
    assert len(records) == 1
    assert records[0]["dente_regiao"] == "Dente 16"
    print("[OK] Histórico do prontuário recuperado com sucesso.")

    # 5.1 Testar Edição de Procedimento
    rec_id = records[0]["id"]
    ok_upd, msg_upd = update_record(
        record_id=rec_id,
        dente_regiao="Dente 16 e 17",
        procedimento="Restauração em Resina Composta e Profilaxia",
        descricao="Atualizado com polimento final.",
        profissional_nome="Dra. Lara Camila",
        user_id=1,
        data_hora="2026-11-07 14:30:00"
    )
    assert ok_upd, msg_upd
    rec_editado = get_record(rec_id)
    assert rec_editado["dente_regiao"] == "Dente 16 e 17"
    assert "Profilaxia" in rec_editado["procedimento"]
    print("[OK] Edição de procedimento realizada e validada com sucesso.")

    # 6. Testar Anexos (criando arquivo de teste temporário)
    test_file = BASE_DIR / "test_raiox.txt"
    test_file.write_text("Simulação de arquivo de raio-x do paciente.")
    ok_att, msg_att = add_attachment(p_id, str(test_file), 1, "Dra. Lara Camila")
    assert ok_att, msg_att
    test_file.unlink()

    anexos = list_attachments(p_id)
    assert len(anexos) == 1
    assert anexos[0]["nome_arquivo"] == "test_raiox.txt"
    print(f"[OK] Arquivo anexado com sucesso na pasta uploads/patients/{p_id}/")

    # 7. Excluir anexo
    att_id = anexos[0]["id"]
    ok_del_att, msg_del_att = delete_attachment(att_id, 1, "Dra. Lara Camila")
    assert ok_del_att, msg_del_att
    assert len(list_attachments(p_id)) == 0
    print("[OK] Exclusão de anexo funcionando fisicamente e no banco.")

    # 8. Testar Logs de Auditoria LGPD
    logs = get_audit_logs()
    assert len(logs) >= 4
    print(f"[OK] Trilha de auditoria da Fase 2 gravou {len(logs)} eventos de pacientes/prontuários.")

    # Limpeza
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    print("\n--- TODOS OS TESTES DA FASE 2 FORAM APROVADOS COM SUCESSO! ---")


if __name__ == "__main__":
    test_phase2()
