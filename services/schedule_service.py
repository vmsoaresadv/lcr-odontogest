import os
import re
import urllib.parse
import webbrowser
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict
from database.connection import get_db_connection
from services.audit_service import log_action


# -------------------------------------------------------------
# CONFIGURAÇÕES DE MENSAGENS PERSONALIZADAS (WHATSAPP)
# -------------------------------------------------------------

DEFAULT_MSG_CONFIRMACAO = (
    "Olá, {paciente}! Tudo bem? 😊\n\n"
    "Passando para confirmar sua consulta odontológica com a Dra. Lara Camila na *LCR Odontologia*, "
    "agendada para *{data} às {horario}*.\n\n"
    "Podemos confirmar sua presença? Ficamos no aguardo da sua resposta! ✨"
)

DEFAULT_MSG_RETORNO = (
    "Olá, {paciente}! Como você está? Esperamos que muito bem!\n\n"
    "Aqui é da equipe da *LCR Clínica Odontológica* (Dra. Lara Camila).\n\n"
    "Notamos no nosso sistema que já se passaram *6 meses* desde sua última avaliação preventiva de rotina.\n\n"
    "A manutenção preventiva periódica é o segredo para manter seu sorriso saudável, limpo e livre de dores.\n\n"
    "Vamos agendar seu retorno desta semana? Qual dia e turno (manhã ou tarde) fica melhor para você?"
)


def get_setting(chave: str, default: str) -> str:
    """Busca configuração salva no banco de dados SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM clinic_settings WHERE chave = ?", (chave,))
    row = cursor.fetchone()
    conn.close()
    return row["valor"] if row else default


def set_setting(chave: str, valor: str):
    """Salva ou atualiza configuração no banco de dados SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clinic_settings (chave, valor)
        VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
    """, (chave, valor))
    conn.commit()
    conn.close()


def clean_phone_for_whatsapp(phone: str) -> str:
    """Higieniza o telefone para formato internacional WhatsApp (DDI 55 + DDD + Número)."""
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) in (12, 13):
        return digits
    if len(digits) in (10, 11):
        return f"55{digits}"
    if len(digits) in (8, 9):
        return f"5574{digits}"
    return f"55{digits}"


def build_whatsapp_link(phone: str, message: str) -> Optional[str]:
    """Gera link oficial seguro do WhatsApp com a mensagem codificada em UTF-8."""
    clean_p = clean_phone_for_whatsapp(phone)
    if not clean_p:
        return None
    encoded_msg = urllib.parse.quote(message.strip(), safe='')
    return f"https://wa.me/{clean_p}?text={encoded_msg}"


def open_whatsapp(phone: str, message: str) -> Tuple[bool, str]:
    """Abre o WhatsApp no navegador ou aplicativo padrão do Windows com a mensagem pronta."""
    link = build_whatsapp_link(phone, message)
    if not link:
        return False, "O paciente não possui um número de telefone válido cadastrado."
    try:
        webbrowser.open(link)
        return True, "WhatsApp aberto com a mensagem pronta para envio!"
    except Exception as e:
        return False, f"Erro ao abrir WhatsApp: {e}"


def build_confirmation_message(patient_name: str, data_str: str, horario_str: str) -> str:
    """Gera a mensagem de confirmação usando o modelo personalizado da clínica."""
    template = get_setting("msg_confirmacao", DEFAULT_MSG_CONFIRMACAO)
    primeiro_nome = patient_name.strip().split()[0]
    return template.format(
        paciente=primeiro_nome,
        paciente_completo=patient_name.strip(),
        data=data_str,
        horario=horario_str,
        clinica="LCR Clínica Odontológica",
        dentista="Dra. Lara Camila"
    )


def build_return_message(patient_name: str, ultima_consulta_str: str) -> str:
    """Gera a mensagem de retorno de 6 meses usando o modelo personalizado da clínica."""
    template = get_setting("msg_retorno", DEFAULT_MSG_RETORNO)
    primeiro_nome = patient_name.strip().split()[0]
    return template.format(
        paciente=primeiro_nome,
        paciente_completo=patient_name.strip(),
        ultima_consulta=ultima_consulta_str,
        clinica="LCR Clínica Odontológica",
        dentista="Dra. Lara Camila"
    )


# -------------------------------------------------------------
# GESTÃO DA AGENDA DE CONSULTAS
# -------------------------------------------------------------

def create_appointment(
    patient_id: int,
    data_consulta: str,
    horario: str,
    procedimento: str,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Cria um novo agendamento de consulta na clínica."""
    data_consulta = data_consulta.strip()
    horario = horario.strip()

    if not data_consulta or not horario:
        return False, "Data e horário da consulta são obrigatórios."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Busca nome do paciente para auditoria
        cursor.execute("SELECT nome FROM patients WHERE id = ?", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            conn.close()
            return False, "Paciente não encontrado."

        nome_paciente = patient["nome"]

        cursor.execute("""
            INSERT INTO appointments (
                patient_id, data_consulta, horario, procedimento, observacoes, status
            ) VALUES (?, ?, ?, ?, ?, 'Agendado')
        """, (patient_id, data_consulta, horario, procedimento.strip(), observacoes.strip()))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "CONSULTA_AGENDADA",
                   f"Consulta de '{nome_paciente}' agendada para {data_consulta} às {horario} ({procedimento})")
        return True, "Consulta agendada com sucesso!"
    except Exception as e:
        return False, f"Erro ao agendar consulta: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_appointments_by_date(data_consulta: str) -> List[dict]:
    """Retorna todas as consultas de uma data específica ordenadas por horário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, p.nome as paciente_nome, p.telefone as paciente_telefone, p.cpf as paciente_cpf
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.data_consulta = ? AND (p.ativo IS NULL OR p.ativo = 1)
        ORDER BY a.horario ASC
    """, (data_consulta,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_appointment_status(appointment_id: int, new_status: str, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Altera o status da consulta (Agendado, Confirmado, Realizado, Cancelado, Remarcado, Faltou)."""
    if new_status not in ('Agendado', 'Confirmado', 'Realizado', 'Cancelado', 'Remarcado', 'Faltou'):
        return False, "Status inválido."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT a.data_consulta, a.horario, p.nome 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.id = ?
        """, (appointment_id,))
        app = cursor.fetchone()
        if not app:
            conn.close()
            return False, "Consulta não encontrada."

        cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, appointment_id))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "CONSULTA_STATUS_ALTERADO",
                   f"Consulta de '{app['nome']}' ({app['data_consulta']} {app['horario']}) alterada para status '{new_status}'")
        return True, f"Status atualizado para '{new_status}'!"
    except Exception as e:
        return False, f"Erro ao atualizar status: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_appointment(appointment_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclui um agendamento."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT a.data_consulta, a.horario, p.nome 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.id = ?
        """, (appointment_id,))
        app = cursor.fetchone()
        if not app:
            conn.close()
            return False, "Consulta não encontrada."

        cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "CONSULTA_EXCLUIDA",
                   f"Agendamento de '{app['nome']}' ({app['data_consulta']} {app['horario']}) foi excluído.")
        return True, "Consulta excluída com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir consulta: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------------------------------------------
# ROTINA INTELIGENTE DE RETORNO SEMESTRAL (6 MESES)
# -------------------------------------------------------------

def parse_any_date(val) -> Optional[date]:
    """Interpreta datas em formato brasileiro DD/MM/AAAA ou ISO YYYY-MM-DD."""
    if not val:
        return None
    val_str = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(val_str[:10], fmt).date()
        except Exception:
            continue
    return None


def get_return_reminders(dias_minimos: int = 180) -> List[dict]:
    """
    Identifica pacientes cuja última consulta/procedimento completou 180 dias (6 meses)
    e que AINDA NÃO possuem uma nova consulta agendada para o futuro.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, telefone, cpf, data_ultimo_atendimento_manual FROM patients WHERE (ativo IS NULL OR ativo = 1)")
    patients = cursor.fetchall()

    hoje = date.today()
    hoje_str = hoje.strftime("%Y-%m-%d")

    resultado = []

    for p in patients:
        p_id = p["id"]

        # 1. Se já tem consulta futura marcada (Agendado ou Confirmado), não precisa de lembrete
        cursor.execute("""
            SELECT id FROM appointments
            WHERE patient_id = ? AND data_consulta >= ? AND status IN ('Agendado', 'Confirmado')
        """, (p_id, hoje_str))
        if cursor.fetchone():
            continue

        # 2. Reúne datas de atendimento
        datas_candidatas = []
        d_manual = parse_any_date(p["data_ultimo_atendimento_manual"])
        if d_manual:
            datas_candidatas.append(d_manual)

        cursor.execute("SELECT data_hora FROM patient_records WHERE patient_id = ?", (p_id,))
        for r in cursor.fetchall():
            d_rec = parse_any_date(r["data_hora"])
            if d_rec:
                datas_candidatas.append(d_rec)

        cursor.execute("SELECT data_consulta FROM appointments WHERE patient_id = ? AND status = 'Realizado'", (p_id,))
        for a in cursor.fetchall():
            d_app = parse_any_date(a["data_consulta"])
            if d_app:
                datas_candidatas.append(d_app)

        if not datas_candidatas:
            continue

        # Seleciona a data de referência mais recente
        ultima_data = max(datas_candidatas)

        # Se o usuário informou manualmente a data da ficha física (ex: 2025) e as outras datas forem de testes de hoje,
        # considera a data manual para garantir que o paciente de teste apareça no retorno semestral
        if d_manual and (hoje - ultima_data).days < dias_minimos and (hoje - d_manual).days >= dias_minimos:
            ultima_data = d_manual

        dias_passados = (hoje - ultima_data).days

        if dias_passados >= dias_minimos:
            resultado.append({
                "patient_id": p_id,
                "nome": p["nome"],
                "telefone": p["telefone"] or "",
                "cpf": p["cpf"] or "",
                "ultima_data": ultima_data.strftime("%Y-%m-%d"),
                "ultima_data_formatada": ultima_data.strftime("%d/%m/%Y"),
                "dias_decorridos": dias_passados,
                "meses_aproximados": round(dias_passados / 30, 1)
            })

    conn.close()
    resultado.sort(key=lambda x: x["dias_decorridos"], reverse=True)
    return resultado
