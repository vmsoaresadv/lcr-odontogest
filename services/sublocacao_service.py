from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict
from database.connection import get_db_connection
from services.audit_service import log_action
from services.schedule_service import get_setting, set_setting, clean_phone_for_whatsapp, open_whatsapp
from services.patient_service import clean_cpf, format_cpf, format_telefone

# Configurações padrão
DEFAULT_TARIFA_HORA = "50.00"
DEFAULT_TARIFA_TURNO = "180.00"
DEFAULT_TARIFA_DIARIA = "300.00"
DEFAULT_PIX_CHAVE = "749991266602"
DEFAULT_PIX_TITULAR = "LARA CAMILA ROCHA"
DEFAULT_PIX_CIDADE = "IRECE"

DEFAULT_MSG_CONTATO_PARCEIRO = (
    "Olá, {parceiro}! Tudo bem?\n\n"
    "Aqui é da *LCR Clínica Odontológica* (Dra. Lara Camila).\n\n"
    "Passando para falar com você sobre a sublocação e agendamentos da Sala 2."
)


# -------------------------------------------------------------
# CONFIGURAÇÕES GERAIS DA SUBLOCAÇÃO
# -------------------------------------------------------------

def get_sublocacao_settings() -> dict:
    """Retorna as tarifas padrão, dados Pix e modelo de mensagem da clínica."""
    return {
        "tarifa_hora": float(get_setting("sublocacao_tarifa_padrao_hora", DEFAULT_TARIFA_HORA)),
        "tarifa_turno": float(get_setting("sublocacao_tarifa_padrao_turno", DEFAULT_TARIFA_TURNO)),
        "tarifa_diaria": float(get_setting("sublocacao_tarifa_padrao_diaria", DEFAULT_TARIFA_DIARIA)),
        "pix_chave": get_setting("pix_chave", DEFAULT_PIX_CHAVE),
        "pix_titular": get_setting("pix_titular", DEFAULT_PIX_TITULAR),
        "pix_cidade": get_setting("pix_cidade", DEFAULT_PIX_CIDADE),
        "msg_parceiro": get_setting("sublocacao_msg_parceiro", DEFAULT_MSG_CONTATO_PARCEIRO),
    }


def save_sublocacao_settings(
    tarifa_hora: float,
    tarifa_turno: float,
    tarifa_diaria: float,
    pix_chave: str,
    pix_titular: str,
    pix_cidade: str,
    user_id: int,
    user_nome: str,
    msg_parceiro: str = ""
) -> Tuple[bool, str]:
    """Salva as configurações de tarifas, dados do Pix e mensagem da sublocação."""
    try:
        set_setting("sublocacao_tarifa_padrao_hora", f"{tarifa_hora:.2f}")
        set_setting("sublocacao_tarifa_padrao_turno", f"{tarifa_turno:.2f}")
        set_setting("sublocacao_tarifa_padrao_diaria", f"{tarifa_diaria:.2f}")
        set_setting("pix_chave", pix_chave.strip())
        set_setting("pix_titular", pix_titular.strip())
        set_setting("pix_cidade", pix_cidade.strip())
        if msg_parceiro:
            set_setting("sublocacao_msg_parceiro", msg_parceiro.strip())

        log_action(user_id, user_nome, "SUBLOCACAO_CONFIG_ATUALIZADA",
                   f"Tarifas da Sala 2 e dados Pix atualizados: R${tarifa_hora:.2f}/h, Chave: {pix_chave}")
        return True, "Configurações da Sublocação salvas com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar configurações: {e}"


def build_partner_whatsapp_message(partner_name: str) -> str:
    """Gera a mensagem padrão de contato com o parceiro via WhatsApp."""
    template = get_setting("sublocacao_msg_parceiro", DEFAULT_MSG_CONTATO_PARCEIRO)
    primeiro_nome = partner_name.strip().split()[0]
    try:
        return template.format(
            parceiro=primeiro_nome,
            parceiro_completo=partner_name.strip(),
            clinica="LCR Clínica Odontológica",
            dentista="Dra. Lara Camila"
        )
    except Exception:
        return f"Olá, {primeiro_nome}! Aqui é da LCR Clínica Odontológica."


# -------------------------------------------------------------
# GESTÃO DE PROFISSIONAIS PARCEIROS
# -------------------------------------------------------------

def list_partners(status_filtro: str = "ativos") -> List[dict]:
    """Retorna a lista de profissionais parceiros."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if status_filtro == "ativos":
        cursor.execute("SELECT * FROM room_partners WHERE ativo = 1 ORDER BY nome ASC")
    elif status_filtro == "inativos":
        cursor.execute("SELECT * FROM room_partners WHERE ativo = 0 ORDER BY nome ASC")
    else:
        cursor.execute("SELECT * FROM room_partners ORDER BY nome ASC")

    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_partner(partner_id: int) -> Optional[dict]:
    """Busca dados de um profissional parceiro pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM room_partners WHERE id = ?", (partner_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_partner(
    nome: str,
    especialidade: str,
    telefone: str,
    cpf: str,
    email: str,
    tipo_cobranca: str,
    valor_acordado: float,
    usar_valor_padrao: bool,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str, Optional[int]]:
    """Cadastra um novo profissional parceiro."""
    nome = nome.strip()
    if not nome:
        return False, "O nome do profissional é obrigatório.", None

    tel_fmt = format_telefone(telefone.strip())
    cpf_fmt = format_cpf(cpf.strip()) if clean_cpf(cpf) else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO room_partners (
                nome, especialidade, telefone, cpf, email,
                tipo_cobranca, valor_acordado, usar_valor_padrao,
                observacoes, ativo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            nome, especialidade.strip(), tel_fmt, cpf_fmt, email.strip(),
            tipo_cobranca, valor_acordado, 1 if usar_valor_padrao else 0,
            observacoes.strip()
        ))
        partner_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PARCEIRO_CADASTRADO",
                   f"Profissional parceiro #{partner_id} '{nome}' ({especialidade}) cadastrado.")
        return True, f"Profissional '{nome}' cadastrado com sucesso!", partner_id
    except Exception as e:
        return False, f"Erro ao cadastrar profissional: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_partner(
    partner_id: int,
    nome: str,
    especialidade: str,
    telefone: str,
    cpf: str,
    email: str,
    tipo_cobranca: str,
    valor_acordado: float,
    usar_valor_padrao: bool,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Atualiza dados do profissional parceiro."""
    nome = nome.strip()
    if not nome:
        return False, "O nome do profissional é obrigatório."

    tel_fmt = format_telefone(telefone.strip())
    cpf_fmt = format_cpf(cpf.strip()) if clean_cpf(cpf) else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_partners SET
                nome = ?,
                especialidade = ?,
                telefone = ?,
                cpf = ?,
                email = ?,
                tipo_cobranca = ?,
                valor_acordado = ?,
                usar_valor_padrao = ?,
                observacoes = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            nome, especialidade.strip(), tel_fmt, cpf_fmt, email.strip(),
            tipo_cobranca, valor_acordado, 1 if usar_valor_padrao else 0,
            observacoes.strip(), partner_id
        ))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PARCEIRO_ATUALIZADO",
                   f"Dados do parceiro #{partner_id} '{nome}' foram atualizados.")
        return True, "Cadastro atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_partner(partner_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Arquiva/Inativa um profissional parceiro (Soft Delete)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM room_partners WHERE id = ?", (partner_id,))
        p = cursor.fetchone()
        if not p:
            conn.close()
            return False, "Profissional não encontrado."

        nome = p["nome"]
        cursor.execute("UPDATE room_partners SET ativo = 0 WHERE id = ?", (partner_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PARCEIRO_INATIVADO",
                   f"Profissional parceiro #{partner_id} '{nome}' foi inativado.")
        return True, f"Profissional '{nome}' inativado com sucesso!"
    except Exception as e:
        return False, f"Erro ao inativar: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def restore_partner(partner_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Reativa um profissional parceiro."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM room_partners WHERE id = ?", (partner_id,))
        p = cursor.fetchone()
        if not p:
            conn.close()
            return False, "Profissional não encontrado."

        nome = p["nome"]
        cursor.execute("UPDATE room_partners SET ativo = 1 WHERE id = ?", (partner_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PARCEIRO_REATIVADO",
                   f"Profissional parceiro #{partner_id} '{nome}' foi reativado.")
        return True, f"Profissional '{nome}' reativado com sucesso!"
    except Exception as e:
        return False, f"Erro ao reativar: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------------------------------------------
# CÁLCULO INTELIGENTE DE VALORES DE SUBLOCAÇÃO
# -------------------------------------------------------------

def calcular_valor_sessao(tipo_cobranca: str, tarifa_base: float, duracao_minutos: int) -> float:
    """
    Calcula o valor da locação com base no tempo de uso e modalidade:
    - hora: proporcional aos minutos (R$ = minutos / 60 * tarifa_hora)
    - turno: valor fechado do turno
    - diaria: valor fechado da diária
    - fixo: valor acordado fechado
    """
    if tipo_cobranca == "hora":
        if duracao_minutos <= 0:
            return 0.0
        horas = duracao_minutos / 60.0
        return round(horas * tarifa_base, 2)
    else:
        return round(tarifa_base, 2)


# -------------------------------------------------------------
# GESTÃO DE SESSÕES / RESERVAS DA SALA 2
# -------------------------------------------------------------

def create_rental(
    partner_id: int,
    data_locacao: str,
    horario_inicio: str,
    horario_fim: str,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str, Optional[int]]:
    """Cria uma nova reserva para a Sala 2."""
    data_locacao = data_locacao.strip()
    horario_inicio = horario_inicio.strip()
    horario_fim = horario_fim.strip()

    if not data_locacao or not horario_inicio or not horario_fim:
        return False, "Data, horário inicial e final são obrigatórios.", None

    partner = get_partner(partner_id)
    if not partner:
        return False, "Profissional parceiro não encontrado.", None

    settings = get_sublocacao_settings()

    # Define tarifa e tipo aplicados
    tipo_cobranca = partner["tipo_cobranca"]
    if partner["usar_valor_padrao"]:
        if tipo_cobranca == "hora":
            valor_base = settings["tarifa_hora"]
        elif tipo_cobranca == "turno":
            valor_base = settings["tarifa_turno"]
        elif tipo_cobranca == "diaria":
            valor_base = settings["tarifa_diaria"]
        else:
            valor_base = settings["tarifa_hora"]
    else:
        valor_base = partner["valor_acordado"]

    # Calcula estimativa inicial baseada nos horários previstos
    try:
        t_ini = datetime.strptime(horario_inicio, "%H:%M")
        t_fim = datetime.strptime(horario_fim, "%H:%M")
        dur_prevista_minutos = max(0, int((t_fim - t_ini).total_seconds() / 60))
    except Exception:
        dur_prevista_minutos = 60

    estimativa = calcular_valor_sessao(tipo_cobranca, valor_base, dur_prevista_minutos)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO room_rentals (
                partner_id, data_locacao, horario_previsto_inicio, horario_previsto_fim,
                duracao_minutos, tipo_cobranca_aplicada, valor_base_hora, valor_calculado,
                valor_final, status_sessao, status_pagamento, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Agendado', 'Pendente', ?)
        """, (
            partner_id, data_locacao, horario_inicio, horario_fim,
            dur_prevista_minutos, tipo_cobranca, valor_base, estimativa,
            estimativa, observacoes.strip()
        ))
        rental_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "SUBLOCACAO_AGENDADA",
                   f"Reserva de sublocação #{rental_id} para '{partner['nome']}' em {data_locacao} das {horario_inicio} às {horario_fim}.")
        return True, "Reserva de sublocação criada com sucesso!", rental_id
    except Exception as e:
        return False, f"Erro ao criar reserva: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_rentals_by_date(data_str: str) -> List[dict]:
    """Retorna todas as sessões da Sala 2 para um dia específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.nome as partner_nome, p.especialidade as partner_especialidade,
               p.telefone as partner_telefone
        FROM room_rentals r
        JOIN room_partners p ON r.partner_id = p.id
        WHERE r.data_locacao = ?
        ORDER BY r.horario_previsto_inicio ASC
    """, (data_str,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_all_rentals(limit: int = 200) -> List[dict]:
    """Retorna as sessões recentes da Sala 2."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.nome as partner_nome, p.especialidade as partner_especialidade,
               p.telefone as partner_telefone
        FROM room_rentals r
        JOIN room_partners p ON r.partner_id = p.id
        ORDER BY r.data_locacao DESC, r.horario_previsto_inicio DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_rental(rental_id: int) -> Optional[dict]:
    """Retorna os dados completos de uma locação."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.nome as partner_nome, p.especialidade as partner_especialidade,
               p.telefone as partner_telefone, p.cpf as partner_cpf
        FROM room_rentals r
        JOIN room_partners p ON r.partner_id = p.id
        WHERE r.id = ?
    """, (rental_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def checkin_rental(rental_id: int, horario_checkin: str, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Registra o início real do atendimento na Sala 2."""
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_rentals SET
                horario_checkin = ?,
                status_sessao = 'Em Uso'
            WHERE id = ?
        """, (horario_checkin, rental_id))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "SUBLOCACAO_CHECKIN",
                   f"Check-in de sublocação registrado para '{rental['partner_nome']}' às {horario_checkin}.")
        return True, f"Check-in registrado às {horario_checkin}! Consultório em uso."
    except Exception as e:
        return False, f"Erro no check-in: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def checkout_rental(rental_id: int, horario_checkout: str, user_id: int, user_nome: str) -> Tuple[bool, str, float]:
    """
    Registra o término real do atendimento na Sala 2,
    calcula a duração exata e o valor total devido.
    """
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada.", 0.0

    checkin_str = rental["horario_checkin"] or rental["horario_previsto_inicio"]

    # Calcula duração em minutos
    duracao_min = 60
    try:
        t_in = datetime.strptime(checkin_str[:5], "%H:%M")
        t_out = datetime.strptime(horario_checkout[:5], "%H:%M")
        duracao_min = max(1, int((t_out - t_in).total_seconds() / 60))
    except Exception:
        duracao_min = 60

    # Calcula valor
    valor_calc = calcular_valor_sessao(
        rental["tipo_cobranca_aplicada"],
        rental["valor_base_hora"],
        duracao_min
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_rentals SET
                horario_checkout = ?,
                duracao_minutos = ?,
                valor_calculado = ?,
                valor_final = ?,
                status_sessao = 'Finalizado'
            WHERE id = ?
        """, (horario_checkout, duracao_min, valor_calc, valor_calc, rental_id))
        conn.commit()
        conn.close()

        horas = duracao_min // 60
        mins = duracao_min % 60
        dur_txt = f"{horas}h{mins:02d}min" if horas > 0 else f"{mins}min"

        log_action(user_id, user_nome, "SUBLOCACAO_CHECKOUT",
                   f"Check-out de sublocação registrado para '{rental['partner_nome']}' às {horario_checkout} ({dur_txt} - R${valor_calc:.2f}).")
        return True, f"Check-out concluído! Tempo de uso: {dur_txt}. Valor sugerido: R$ {valor_calc:.2f}", valor_calc
    except Exception as e:
        return False, f"Erro no check-out: {e}", 0.0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_rental_final_value(
    rental_id: int,
    valor_final: float,
    observacoes: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Permite ao usuário ajustar ou personalizar livremente o valor final a ser pago."""
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_rentals SET
                valor_final = ?,
                observacoes = ?
            WHERE id = ?
        """, (valor_final, observacoes.strip(), rental_id))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "SUBLOCACAO_VALOR_AJUSTADO",
                   f"Valor da sublocação #{rental_id} '{rental['partner_nome']}' ajustado manualmente para R$ {valor_final:.2f}.")
        return True, f"Valor final atualizado para R$ {valor_final:.2f} com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar valor: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def mark_rental_as_paid(
    rental_id: int,
    forma_pagamento: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Marca a sublocação como Paga."""
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada."

    hoje_str = date.today().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_rentals SET
                status_pagamento = 'Pago',
                forma_pagamento = ?,
                data_pagamento = ?
            WHERE id = ?
        """, (forma_pagamento, hoje_str, rental_id))
        conn.commit()
        conn.close()

        # Sincroniza automaticamente a receita no Módulo Financeiro
        try:
            from services.financial_service import sync_sublocacao_receita
            sync_sublocacao_receita(
                rental_id=rental_id,
                valor=float(rental["valor_final"]),
                data_locacao=rental["data_locacao"],
                forma_pagamento=forma_pagamento,
                partner_nome=rental["partner_nome"],
                user_id=user_id,
                user_nome=user_nome
            )
        except Exception:
            pass

        log_action(user_id, user_nome, "SUBLOCACAO_PAGA",
                   f"Pagamento de R$ {rental['valor_final']:.2f} de sublocação confirmado para '{rental['partner_nome']}' ({forma_pagamento}).")
        return True, "Pagamento registrado com sucesso!"
    except Exception as e:
        return False, f"Erro ao registrar pagamento: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def cancel_rental(rental_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Cancela uma reserva de sublocação."""
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE room_rentals SET
                status_sessao = 'Cancelado'
            WHERE id = ?
        """, (rental_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "SUBLOCACAO_CANCELADA",
                   f"Reserva #{rental_id} de '{rental['partner_nome']}' foi cancelada.")
        return True, "Reserva cancelada com sucesso."
    except Exception as e:
        return False, f"Erro ao cancelar: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_rental(rental_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclui um registro de sublocação."""
    rental = get_rental(rental_id)
    if not rental:
        return False, "Reserva não encontrada."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM room_rentals WHERE id = ?", (rental_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "SUBLOCACAO_EXCLUIDA",
                   f"Registro de locação #{rental_id} foi excluído.")
        return True, "Registro excluído com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------------------------------------------
# MENSAGEM WHATSAPP PARA COBRANÇA DO PIX
# -------------------------------------------------------------

def build_sublocacao_whatsapp_message(rental: dict, pix_copia_cola: str) -> str:
    """Gera o texto de cobrança com os detalhes do uso e o código Pix Copia e Cola."""
    primeiro_nome = rental["partner_nome"].split()[0]
    duracao_min = rental.get("duracao_minutos", 0)
    horas = duracao_min // 60
    mins = duracao_min % 60
    dur_txt = f"{horas}h{mins:02d}min" if horas > 0 else f"{mins}min"

    d_obj = datetime.strptime(rental["data_locacao"], "%Y-%m-%d").date()
    data_br = d_obj.strftime("%d/%m/%Y")

    h_in = rental.get("horario_checkin") or rental.get("horario_previsto_inicio") or "--:--"
    h_out = rental.get("horario_checkout") or rental.get("horario_previsto_fim") or "--:--"

    msg = (
        f"Olá, {primeiro_nome}! Tudo bem?\n\n"
        f"Aqui é da *LCR Clínica Odontológica*.\n"
        f"Segue o resumo do uso do consultório em *{data_br}*:\n\n"
        f"⏰ Horário: {h_in} às {h_out} ({dur_txt})\n"
        f"💰 *Valor a pagar: R$ {rental['valor_final']:.2f}*\n\n"
        f"Para pagar via Pix com rapidez, utilize o código abaixo:\n\n"
        f"`{pix_copia_cola}`\n\n"
        f"(Basta copiar o código acima e colar na opção *Pix Copia e Cola* do seu banco)\n\n"
        f"Agradecemos a parceria!"
    )
    return msg
