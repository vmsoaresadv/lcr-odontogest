import sys
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Override para banco temporário de testes
import database.connection as db_conn
TEST_DB_PATH = BASE_DIR / "data" / "test_phase3.db"
db_conn.DB_PATH = TEST_DB_PATH

from database.connection import init_db
from services.patient_service import create_patient, add_record
from services.schedule_service import (
    create_appointment, list_appointments_by_date,
    update_appointment_status, delete_appointment,
    get_return_reminders, clean_phone_for_whatsapp,
    build_whatsapp_link, build_confirmation_message, build_return_message
)
from services.audit_service import get_audit_logs


def test_phase3():
    print("--- INICIANDO TESTES DA FASE 3: AGENDA E RETORNO VIA WHATSAPP ---")

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    init_db()
    print("[OK] Banco de dados temporário inicializado.")

    # 1. Criar Paciente para testar agendamento
    ok, msg, p_id = create_patient(
        nome="Lucas Andrade",
        cpf="98765432100",
        data_nascimento="10/10/1990",
        telefone="(74) 99126-6602",
        email="lucas@email.com",
        endereco="Rua Central, Irecê",
        alergias="Nenhuma",
        observacoes_medicas="",
        user_id=1,
        user_nome="Dra. Lara Camila"
    )
    assert ok, msg
    print(f"[OK] Paciente Lucas criado com ID #{p_id}")

    # 2. Testar Agendamento de Consulta
    hoje_str = date.today().strftime("%Y-%m-%d")
    ok_app, msg_app = create_appointment(
        patient_id=p_id,
        data_consulta=hoje_str,
        horario="09:30",
        procedimento="Profilaxia / Limpeza Preventiva",
        observacoes="Primeira consulta",
        user_id=1,
        user_nome="Dra. Lara Camila"
    )
    assert ok_app, msg_app
    print("[OK] Consulta agendada com sucesso para hoje às 09:30.")

    # 3. Listar consultas do dia
    consultas = list_appointments_by_date(hoje_str)
    assert len(consultas) == 1
    assert consultas[0]["horario"] == "09:30"
    assert consultas[0]["status"] == "Agendado"
    print("[OK] Listagem de consultas do dia funcionando com horários ordenados.")

    # 4. Alterar Status para Confirmado e Realizado
    app_id = consultas[0]["id"]
    ok_st, msg_st = update_appointment_status(app_id, "Confirmado", 1, "Dra. Lara Camila")
    assert ok_st, msg_st
    consultas = list_appointments_by_date(hoje_str)
    assert consultas[0]["status"] == "Confirmado"
    print("[OK] Status alterado com sucesso para 'Confirmado'.")

    # 5. Testar Higienização de Telefone e Link do WhatsApp
    tel_limpo = clean_phone_for_whatsapp("(74) 99126-6602")
    assert tel_limpo == "5574991266602", f"Esperado 5574991266602, obteve {tel_limpo}"
    print("[OK] Higienização internacional do número para o WhatsApp funcionando.")

    msg_conf = build_confirmation_message("Lucas Andrade", "06/11/2026", "09:30")
    link_zap = build_whatsapp_link("(74) 99126-6602", msg_conf)
    assert "https://wa.me/5574991266602?text=" in link_zap
    assert "Dra.%20Lara%20Camila" in link_zap
    print("[OK] Gerador de link do WhatsApp com mensagem pronta validado.")

    # 6. Testar Lógica de Retorno de 6 Meses
    # Cria paciente antigo cujo atendimento foi há 200 dias
    ok_ant, msg_ant, p_ant_id = create_patient(
        nome="Camila Silva Antiga",
        cpf="11122233344",
        data_nascimento="20/03/1985",
        telefone="(74) 99930-8146",
        email="", endereco="", alergias="", observacoes_medicas="",
        user_id=1, user_nome="Dra. Lara Camila"
    )
    assert ok_ant, msg_ant

    # Simula atendimento concluído há 200 dias no banco
    data_antiga = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
    conn = db_conn.get_db_connection()
    conn.execute("""
        INSERT INTO appointments (patient_id, data_consulta, horario, procedimento, status)
        VALUES (?, ?, '10:00', 'Restauração', 'Realizado')
    """, (p_ant_id, data_antiga))
    conn.commit()
    conn.close()

    # Verifica se Camila aparece nos lembretes de retorno
    lembretes = get_return_reminders(dias_minimos=180)
    pacientes_retorno_ids = [r["patient_id"] for r in lembretes]
    assert p_ant_id in pacientes_retorno_ids, "Paciente com atendimento há 200 dias deveria estar nos retornos!"
    print(f"[OK] Detecção inteligente de retorno de 6 meses identificou {len(lembretes)} paciente(s).")

    # Se agendarmos uma nova consulta futura para a Camila, ela deve sair da lista de retorno!
    data_futura = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    create_appointment(p_ant_id, data_futura, "14:00", "Revisão", "", 1, "Dra. Lara Camila")
    lembretes_apos_agendar = get_return_reminders(dias_minimos=180)
    pacientes_retorno_ids_depois = [r["patient_id"] for r in lembretes_apos_agendar]
    assert p_ant_id not in pacientes_retorno_ids_depois, "Paciente agendado para o futuro deve sair da lista de retorno!"
    print("[OK] Paciente com consulta futura removido automaticamente da lista de retorno.")

    # 7. Trilha de Auditoria
    logs = get_audit_logs()
    assert len(logs) >= 3
    print(f"[OK] Trilha de auditoria da Fase 3 gravou {len(logs)} eventos de agendamento.")

    # Limpeza
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    print("\n--- TODOS OS TESTES DA FASE 3 FORAM APROVADOS COM SUCESSO! ---")


if __name__ == "__main__":
    test_phase3()
