import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from database.connection import get_db_connection
from services.audit_service import log_action

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads" / "patients"


def clean_cpf(cpf: str) -> str:
    """Remove caracteres não numéricos do CPF."""
    return "".join(c for c in cpf if c.isdigit())


def format_cpf(cpf: str) -> str:
    """Formata CPF no padrão 000.000.000-00."""
    d = clean_cpf(cpf)
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return cpf


def format_telefone(tel: str) -> str:
    """Formata telefone no padrão brasileiro (00) 00000-0000 ou (00) 0000-0000."""
    d = "".join(c for c in tel if c.isdigit())
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    elif len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    elif len(d) == 9:
        return f"(74) {d[:5]}-{d[5:]}"
    elif len(d) == 8:
        return f"(74) {d[:4]}-{d[4:]}"
    return tel


def format_data_br(dt_str: str) -> str:
    """Formata data no padrão brasileiro DD/MM/AAAA."""
    if not dt_str:
        return ""
    d = "".join(c for c in dt_str if c.isdigit())
    if len(d) == 8:
        # Se for no formato YYYYMMDD
        if dt_str.startswith("19") or dt_str.startswith("20") and len(dt_str) >= 8 and not "/" in dt_str:
            return f"{d[6:8]}/{d[4:6]}/{d[:4]}"
        return f"{d[:2]}/{d[2:4]}/{d[4:]}"
    return dt_str


# -------------------------------------------------------------
# GESTÃO DE PACIENTES
# -------------------------------------------------------------

def create_patient(
    nome: str,
    cpf: str,
    data_nascimento: str,
    telefone: str,
    email: str,
    endereco: str,
    alergias: str,
    observacoes_medicas: str,
    user_id: int,
    user_nome: str,
    data_ultimo_atendimento_manual: str = ""
) -> Tuple[bool, str, Optional[int]]:
    """Cadastra um novo paciente na clínica."""
    nome = nome.strip()
    cpf_limpo = clean_cpf(cpf)

    if not nome:
        return False, "O nome do paciente é obrigatório.", None

    telefone_formatado = format_telefone(telefone.strip())
    nasc_formatado = format_data_br(data_nascimento.strip())

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Se informou CPF, valida duplicidade
        if cpf_limpo:
            cursor.execute("SELECT id, nome FROM patients WHERE REPLACE(REPLACE(cpf, '.', ''), '-', '') = ?", (cpf_limpo,))
            existente = cursor.fetchone()
            if existente:
                conn.close()
                return False, f"CPF já cadastrado para o paciente '{existente['nome']}'.", None

        cursor.execute("""
            INSERT INTO patients (
                nome, cpf, data_nascimento, telefone, email,
                endereco, alergias, observacoes_medicas, data_ultimo_atendimento_manual
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, format_cpf(cpf_limpo) if cpf_limpo else "",
            nasc_formatado, telefone_formatado, email.strip(),
            endereco.strip(), alergias.strip(), observacoes_medicas.strip(),
            data_ultimo_atendimento_manual.strip()
        ))
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PACIENTE_CRIADO", f"Paciente #{patient_id} '{nome}' cadastrado.")
        return True, "Paciente cadastrado com sucesso!", patient_id
    except Exception as e:
        return False, f"Erro ao cadastrar paciente: {e}", None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_patient(
    patient_id: int,
    nome: str,
    cpf: str,
    data_nascimento: str,
    telefone: str,
    email: str,
    endereco: str,
    alergias: str,
    observacoes_medicas: str,
    user_id: int,
    user_nome: str,
    data_ultimo_atendimento_manual: str = ""
) -> Tuple[bool, str]:
    """Atualiza dados cadastrais do paciente."""
    nome = nome.strip()
    cpf_limpo = clean_cpf(cpf)

    if not nome:
        return False, "O nome do paciente é obrigatório."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Valida CPF duplicado com outro paciente
        if cpf_limpo:
            cursor.execute("""
                SELECT id, nome FROM patients 
                WHERE REPLACE(REPLACE(cpf, '.', ''), '-', '') = ? AND id != ?
            """, (cpf_limpo, patient_id))
            existente = cursor.fetchone()
            if existente:
                conn.close()
                return False, f"Este CPF já pertence ao paciente '{existente['nome']}'."

        telefone_formatado = format_telefone(telefone.strip())
        nasc_formatado = format_data_br(data_nascimento.strip())

        cursor.execute("""
            UPDATE patients SET
                nome = ?,
                cpf = ?,
                data_nascimento = ?,
                telefone = ?,
                email = ?,
                endereco = ?,
                alergias = ?,
                observacoes_medicas = ?,
                data_ultimo_atendimento_manual = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            nome, format_cpf(cpf_limpo) if cpf_limpo else "",
            nasc_formatado, telefone_formatado, email.strip(),
            endereco.strip(), alergias.strip(), observacoes_medicas.strip(),
            data_ultimo_atendimento_manual.strip(),
            patient_id
        ))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PACIENTE_ATUALIZADO", f"Ficha do paciente #{patient_id} '{nome}' foi atualizada.")
        return True, "Ficha atualizada com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_patient(patient_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """
    Arquiva/Inativa um paciente (Soft Delete / Lixeira).
    Preserva todo o histórico odontológico, consultas e Raio-X conforme exigência do CFO e LGPD.
    Pode ser restaurado a qualquer momento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM patients WHERE id = ?", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            conn.close()
            return False, "Paciente não encontrado."

        nome = patient["nome"]
        cursor.execute("UPDATE patients SET ativo = 0, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PACIENTE_ARQUIVADO",
                   f"Paciente #{patient_id} '{nome}' foi arquivado (enviado para a lixeira/inativos).")
        return True, f"Paciente '{nome}' foi enviado para a Lixeira / Inativos.\nVocê pode restaurá-lo a qualquer momento!"
    except Exception as e:
        return False, f"Erro ao arquivar paciente: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def restore_patient(patient_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Restaura um paciente inativo da lixeira de volta para a lista de ativos."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM patients WHERE id = ?", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            conn.close()
            return False, "Paciente não encontrado."

        nome = patient["nome"]
        cursor.execute("UPDATE patients SET ativo = 1, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?", (patient_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PACIENTE_RESTAURADO",
                   f"Paciente #{patient_id} '{nome}' foi restaurado da lixeira para a lista de ativos.")
        return True, f"Paciente '{nome}' restaurado com sucesso!\nSua ficha e histórico já estão visíveis novamente."
    except Exception as e:
        return False, f"Erro ao restaurar paciente: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_patient_permanently(patient_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclusão definitiva permanente do banco e do disco (exclusivo para perfil Administrador)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT nome FROM patients WHERE id = ?", (patient_id,))
        patient = cursor.fetchone()
        if not patient:
            conn.close()
            return False, "Paciente não encontrado."

        nome = patient["nome"]
        # Deleta registros dependentes explicitamente
        cursor.execute("DELETE FROM appointments WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patient_records WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patient_attachments WHERE patient_id = ?", (patient_id,))
        cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()

        # Remove pasta física de uploads
        patient_folder = UPLOADS_DIR / str(patient_id)
        if patient_folder.exists():
            shutil.rmtree(patient_folder, ignore_errors=True)

        log_action(user_id, user_nome, "PACIENTE_EXCLUIDO_DEFINITIVAMENTE",
                   f"Paciente #{patient_id} '{nome}' e todos os seus registros foram excluídos permanentemente.")
        return True, f"Paciente '{nome}' foi excluído permanentemente com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir paciente definitivamente: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_patient(patient_id: int) -> Optional[dict]:
    """Retorna os dados completos de um paciente pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_patients(termo: str = "", status_filtro: str = "ativos") -> List[dict]:
    """
    Busca pacientes por Nome ou CPF (em tempo real), respeitando o filtro de status:
    - 'ativos': apenas pacientes ativos (padrão do dia a dia)
    - 'inativos': pacientes arquivados / na lixeira
    - 'todos': todos os pacientes
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    termo_limpo = termo.strip()
    cpf_busca = clean_cpf(termo_limpo)

    cond_status = ""
    if status_filtro == "ativos":
        cond_status = "AND (p.ativo IS NULL OR p.ativo = 1)"
    elif status_filtro == "inativos":
        cond_status = "AND p.ativo = 0"

    if termo_limpo:
        query = f"""
            SELECT p.*,
                   COALESCE(
                       (SELECT MAX(pr.data_hora) FROM patient_records pr WHERE pr.patient_id = p.id),
                       p.data_ultimo_atendimento_manual
                   ) as ultimo_atendimento
            FROM patients p
            WHERE (p.nome LIKE ? 
               OR (length(?) > 0 AND REPLACE(REPLACE(p.cpf, '.', ''), '-', '') LIKE ?))
               {cond_status}
            ORDER BY p.nome ASC
        """
        param_nome = f"%{termo_limpo}%"
        param_cpf = f"%{cpf_busca}%"
        cursor.execute(query, (param_nome, cpf_busca, param_cpf))
    else:
        where_clause = ""
        if status_filtro == "ativos":
            where_clause = "WHERE (p.ativo IS NULL OR p.ativo = 1)"
        elif status_filtro == "inativos":
            where_clause = "WHERE p.ativo = 0"

        query = f"""
            SELECT p.*,
                   COALESCE(
                       (SELECT MAX(pr.data_hora) FROM patient_records pr WHERE pr.patient_id = p.id),
                       p.data_ultimo_atendimento_manual
                   ) as ultimo_atendimento
            FROM patients p
            {where_clause}
            ORDER BY p.nome ASC
            LIMIT 300
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# -------------------------------------------------------------
# PRONTUÁRIO / EVOLUÇÃO CLÍNICA
# -------------------------------------------------------------

def add_record(
    patient_id: int,
    dente_regiao: str,
    procedimento: str,
    descricao: str,
    profissional_nome: str,
    user_id: int,
    data_hora: Optional[str] = None
) -> Tuple[bool, str]:
    """Adiciona uma evolução / procedimento clínico ao prontuário (permite data retroativa)."""
    procedimento = procedimento.strip()
    if not procedimento:
        return False, "Informe o procedimento realizado."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        data_registro = data_hora.strip() if data_hora else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO patient_records (
                patient_id, dente_regiao, procedimento, descricao, profissional_nome, data_hora
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_id, dente_regiao.strip(), procedimento,
            descricao.strip(), profissional_nome.strip(), data_registro
        ))
        conn.commit()
        conn.close()

        log_action(user_id, profissional_nome, "PRONTUARIO_ADICIONADO",
                   f"Procedimento '{procedimento}' (Dente: {dente_regiao or 'Geral'}) no paciente #{patient_id} em {data_registro}")
        return True, "Evolução adicionada ao prontuário com sucesso!"
    except Exception as e:
        return False, f"Erro ao adicionar evolução: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_records(patient_id: int) -> List[dict]:
    """Lista todos os procedimentos do prontuário em ordem cronológica (mais recentes primeiro)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM patient_records
        WHERE patient_id = ?
        ORDER BY data_hora DESC, id DESC
    """, (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_record(
    record_id: int,
    dente_regiao: str,
    procedimento: str,
    descricao: str,
    profissional_nome: str,
    user_id: int,
    data_hora: Optional[str] = None
) -> Tuple[bool, str]:
    """Atualiza um procedimento / evolução clínica existente no prontuário."""
    procedimento = procedimento.strip()
    if not procedimento:
        return False, "Informe o procedimento realizado."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT patient_id, procedimento FROM patient_records WHERE id = ?", (record_id,))
        rec = cursor.fetchone()
        if not rec:
            conn.close()
            return False, "Procedimento não encontrado."

        data_registro = data_hora.strip() if data_hora else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE patient_records SET
                dente_regiao = ?,
                procedimento = ?,
                descricao = ?,
                profissional_nome = ?,
                data_hora = ?
            WHERE id = ?
        """, (
            dente_regiao.strip(), procedimento,
            descricao.strip(), profissional_nome.strip(),
            data_registro, record_id
        ))
        conn.commit()
        conn.close()

        log_action(user_id, profissional_nome, "PRONTUARIO_EDITADO",
                   f"Procedimento #{record_id} '{procedimento}' atualizado no paciente #{rec['patient_id']} ({data_registro})")
        return True, "Procedimento atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar procedimento: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_record(record_id: int) -> Optional[dict]:
    """Retorna um procedimento específico do prontuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_record(record_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclui um procedimento do prontuário (com registro em auditoria)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT patient_id, procedimento FROM patient_records WHERE id = ?", (record_id,))
        rec = cursor.fetchone()
        if not rec:
            conn.close()
            return False, "Procedimento não encontrado."

        cursor.execute("DELETE FROM patient_records WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "PRONTUARIO_EXCLUIDO",
                   f"Procedimento #{record_id} '{rec['procedimento']}' excluído do paciente #{rec['patient_id']}")
        return True, "Procedimento removido do prontuário."
    except Exception as e:
        return False, f"Erro ao excluir procedimento: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------------------------------------------
# ANEXOS (RAIO-X, EXAMES, IMAGENS)
# -------------------------------------------------------------

def add_attachment(
    patient_id: int,
    source_file_path: str,
    user_id: int,
    user_nome: str
) -> Tuple[bool, str]:
    """Copia o arquivo selecionado para a pasta de uploads do paciente e salva o registro."""
    source_path = Path(source_file_path)
    if not source_path.exists():
        return False, "Arquivo de origem não encontrado."

    dest_folder = UPLOADS_DIR / str(patient_id)
    dest_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{source_path.name}"
    dest_path = dest_folder / safe_name

    try:
        shutil.copy2(source_path, dest_path)
        file_size = dest_path.stat().st_size

        conn = get_db_connection()
        cursor = conn.cursor()
        agora_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO patient_attachments (
                patient_id, nome_arquivo, caminho_arquivo, tamanho_bytes, data_upload
            ) VALUES (?, ?, ?, ?, ?)
        """, (patient_id, source_path.name, str(dest_path), file_size, agora_local))
        conn.commit()
        conn.close()

        log_action(user_id, user_nome, "ANEXO_ENVIADO",
                   f"Arquivo '{source_path.name}' anexado à ficha do paciente #{patient_id}")
        return True, "Arquivo anexado com sucesso!"
    except Exception as e:
        return False, f"Erro ao anexar arquivo: {e}"


def list_attachments(patient_id: int) -> List[dict]:
    """Lista todos os arquivos anexados à ficha do paciente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM patient_attachments
        WHERE patient_id = ?
        ORDER BY data_upload DESC
    """, (patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def open_attachment(attachment_id: int) -> Tuple[bool, str]:
    """Abre o arquivo anexado no visualizador padrão do Windows."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT caminho_arquivo, nome_arquivo FROM patient_attachments WHERE id = ?", (attachment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, "Registro de anexo não encontrado."

    file_path = Path(row["caminho_arquivo"])
    if not file_path.exists():
        return False, f"O arquivo físico não foi encontrado em '{file_path}'."

    try:
        os.startfile(str(file_path))
        return True, f"Abrindo '{row['nome_arquivo']}'..."
    except Exception as e:
        return False, f"Não foi possível abrir o arquivo: {e}"


def delete_attachment(attachment_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Exclui o arquivo físico e o registro do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT patient_id, caminho_arquivo, nome_arquivo FROM patient_attachments WHERE id = ?", (attachment_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Anexo não encontrado."

        file_path = Path(row["caminho_arquivo"])
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

        cursor.execute("DELETE FROM patient_attachments WHERE id = ?", (attachment_id,))
        conn.commit()

        log_action(user_id, user_nome, "ANEXO_EXCLUIDO",
                   f"Anexo '{row['nome_arquivo']}' excluído da ficha #{row['patient_id']}")
        return True, "Anexo excluído com sucesso."
    except Exception as e:
        return False, f"Erro ao excluir anexo: {e}"
    finally:
        conn.close()


# ==============================================================================
# SERVIÇOS DE ANAMNESE ODONTOLÓGICA
# ==============================================================================

def get_patient_anamnese(patient_id: int) -> dict:
    """Retorna a anamnese completa do paciente. Cria estrutura padrão se ainda não existir."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient_anamnese WHERE patient_id = ?", (patient_id,))
    row = cursor.fetchone()
    
    if not row:
        # Se ainda não existe, tenta herdar alergias/obs_medicas do cadastro base do paciente
        cursor.execute("SELECT alergias, observacoes_medicas FROM patients WHERE id = ?", (patient_id,))
        p_row = cursor.fetchone()
        alergias_ini = p_row["alergias"] if p_row and p_row["alergias"] else ""
        obs_ini = p_row["observacoes_medicas"] if p_row and p_row["observacoes_medicas"] else ""
        conn.close()
        return {
            "patient_id": patient_id,
            "queixa_principal": "",
            "historico_doenca_atual": "",
            "hipertensao": 0,
            "diabetes": 0,
            "cardiopatia": 0,
            "problema_coagulacao": 0,
            "doenca_renal_hepatica": 0,
            "gestante_lactante": 0,
            "fumante": 0,
            "bruxismo": 0,
            "alergias_medicamentos": alergias_ini,
            "alergia_latex": 0,
            "medicamentos_uso": "",
            "historico_cirurgico": "",
            "observacoes": obs_ini,
            "atualizado_em": ""
        }

    conn.close()
    return dict(row)


def save_patient_anamnese(patient_id: int, data: dict, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Salva ou atualiza a ficha de anamnese odontológica do paciente."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO patient_anamnese (
                patient_id, queixa_principal, historico_doenca_atual,
                hipertensao, diabetes, cardiopatia, problema_coagulacao,
                doenca_renal_hepatica, gestante_lactante, fumante, bruxismo,
                alergias_medicamentos, alergia_latex, medicamentos_uso,
                historico_cirurgico, observacoes, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(patient_id) DO UPDATE SET
                queixa_principal = excluded.queixa_principal,
                historico_doenca_atual = excluded.historico_doenca_atual,
                hipertensao = excluded.hipertensao,
                diabetes = excluded.diabetes,
                cardiopatia = excluded.cardiopatia,
                problema_coagulacao = excluded.problema_coagulacao,
                doenca_renal_hepatica = excluded.doenca_renal_hepatica,
                gestante_lactante = excluded.gestante_lactante,
                fumante = excluded.fumante,
                bruxismo = excluded.bruxismo,
                alergias_medicamentos = excluded.alergias_medicamentos,
                alergia_latex = excluded.alergia_latex,
                medicamentos_uso = excluded.medicamentos_uso,
                historico_cirurgico = excluded.historico_cirurgico,
                observacoes = excluded.observacoes,
                atualizado_em = excluded.atualizado_em
        """, (
            patient_id,
            data.get("queixa_principal", "").strip(),
            data.get("historico_doenca_atual", "").strip(),
            1 if data.get("hipertensao") else 0,
            1 if data.get("diabetes") else 0,
            1 if data.get("cardiopatia") else 0,
            1 if data.get("problema_coagulacao") else 0,
            1 if data.get("doenca_renal_hepatica") else 0,
            1 if data.get("gestante_lactante") else 0,
            1 if data.get("fumante") else 0,
            1 if data.get("bruxismo") else 0,
            data.get("alergias_medicamentos", "").strip(),
            1 if data.get("alergia_latex") else 0,
            data.get("medicamentos_uso", "").strip(),
            data.get("historico_cirurgico", "").strip(),
            data.get("observacoes", "").strip(),
            agora
        ))

        # Sincroniza campos essenciais no cadastro do paciente (alergias e alertas)
        alergias_resumo = []
        if data.get("alergias_medicamentos", "").strip():
            alergias_resumo.append(data.get("alergias_medicamentos", "").strip())
        if data.get("alergia_latex"):
            alergias_resumo.append("Látex")
        str_alergias = ", ".join(alergias_resumo)

        cursor.execute("""
            UPDATE patients
            SET alergias = ?, atualizado_em = ?
            WHERE id = ?
        """, (str_alergias, agora, patient_id))

        conn.commit()

        log_action(user_id, user_nome, "ANAMNESE_ATUALIZADA",
                   f"Anamnese odontológica do paciente #{patient_id} atualizada com sucesso.")
        return True, "Anamnese salva com sucesso!"

    except Exception as e:
        return False, f"Erro ao salvar anamnese: {e}"
    finally:
        conn.close()


# ==============================================================================
# SERVIÇOS DO ODONTOGRAMA INTERATIVO (FDI)
# ==============================================================================

# Dentes Permanentes Padrão FDI:
# Arcada Superior: 18..11 (Q1 Direito) e 21..28 (Q2 Esquerdo)
# Arcada Inferior: 48..41 (Q4 Direito) e 31..38 (Q3 Esquerdo)
DENTES_FDI_SUPERIORES = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
DENTES_FDI_INFERIORES = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]

NOMES_DENTES = {
    18: "Terceiro Molar Sup. Dir.", 17: "Segundo Molar Sup. Dir.", 16: "Primeiro Molar Sup. Dir.",
    15: "Segundo Pré-Molar Sup. Dir.", 14: "Primeiro Pré-Molar Sup. Dir.", 13: "Canino Sup. Dir.",
    12: "Incisivo Lateral Sup. Dir.", 11: "Incisivo Central Sup. Dir.",
    21: "Incisivo Central Sup. Esq.", 22: "Incisivo Lateral Sup. Esq.", 23: "Canino Sup. Esq.",
    24: "Primeiro Pré-Molar Sup. Esq.", 25: "Segundo Pré-Molar Sup. Esq.", 26: "Primeiro Molar Sup. Esq.",
    27: "Segundo Molar Sup. Esq.", 28: "Terceiro Molar Sup. Esq.",
    48: "Terceiro Molar Inf. Dir.", 47: "Segundo Molar Inf. Dir.", 46: "Primeiro Molar Inf. Dir.",
    45: "Segundo Pré-Molar Inf. Dir.", 44: "Primeiro Pré-Molar Inf. Dir.", 43: "Canino Inf. Dir.",
    42: "Incisivo Lateral Inf. Dir.", 41: "Incisivo Central Inf. Dir.",
    31: "Incisivo Central Inf. Esq.", 32: "Incisivo Lateral Inf. Esq.", 33: "Canino Inf. Esq.",
    34: "Primeiro Pré-Molar Inf. Esq.", 35: "Segundo Pré-Molar Inf. Esq.", 36: "Primeiro Molar Inf. Esq.",
    37: "Segundo Molar Inf. Esq.", 38: "Terceiro Molar Inf. Esq."
}

STATUS_DENTE_CORES = {
    "higido": {"nome": "Hígido / Sadio", "cor": "#10b981", "badge": "✓ Hígido"},
    "carie": {"nome": "Cárie / A Tratar", "cor": "#ef4444", "badge": "● Cárie"},
    "restaurado": {"nome": "Restaurado", "cor": "#3b82f6", "badge": "■ Restaurado"},
    "canal": {"nome": "Canal / Endodontia", "cor": "#f59e0b", "badge": "⚡ Canal"},
    "protese": {"nome": "Prótese / Coroa", "cor": "#8b5cf6", "badge": "👑 Prótese"},
    "implante": {"nome": "Implante", "cor": "#06b6d4", "badge": "🔩 Implante"},
    "ausente": {"nome": "Ausente / Extraído", "cor": "#64748b", "badge": "✕ Ausente"}
}


def get_patient_odontograma(patient_id: int) -> Dict[int, dict]:
    """Retorna o mapa de todos os dentes com seu status atual no odontograma."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT numero_dente, status, faces, observacoes, atualizado_em
        FROM patient_odontograma
        WHERE patient_id = ?
    """, (patient_id,))
    rows = cursor.fetchall()
    conn.close()

    resultado = {}
    for r in rows:
        resultado[r["numero_dente"]] = {
            "numero_dente": r["numero_dente"],
            "status": r["status"],
            "faces": r["faces"] or "",
            "observacoes": r["observacoes"] or "",
            "atualizado_em": r["atualizado_em"]
        }
    return resultado


def save_tooth_status(patient_id: int, numero_dente: int, status: str, faces: str,
                       observacoes: str, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Atualiza ou insere o status de um dente específico no odontograma."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO patient_odontograma (
                patient_id, numero_dente, status, faces, observacoes, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(patient_id, numero_dente) DO UPDATE SET
                status = excluded.status,
                faces = excluded.faces,
                observacoes = excluded.observacoes,
                atualizado_em = excluded.atualizado_em
        """, (patient_id, numero_dente, status, faces.strip(), observacoes.strip(), agora))
        conn.commit()

        nome_dente = NOMES_DENTES.get(numero_dente, f"Dente {numero_dente}")
        status_label = STATUS_DENTE_CORES.get(status, {}).get("nome", status)
        log_action(user_id, user_nome, "ODONTOGRAMA_ATUALIZADO",
                   f"{nome_dente} atualizado para '{status_label}' no paciente #{patient_id}")
        return True, "Dente atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar dente: {e}"
    finally:
        conn.close()


def reset_odontograma(patient_id: int, user_id: int, user_nome: str) -> Tuple[bool, str]:
    """Limpa as anotações do odontograma retornando todos os dentes para o estado inicial hígido."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM patient_odontograma WHERE patient_id = ?", (patient_id,))
        conn.commit()
        log_action(user_id, user_nome, "ODONTOGRAMA_RESET", f"Odontograma resetado para o paciente #{patient_id}")
        return True, "Odontograma resetado com sucesso."
    except Exception as e:
        return False, f"Erro ao resetar: {e}"
    finally:
        conn.close()
