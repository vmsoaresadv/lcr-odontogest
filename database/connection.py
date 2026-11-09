import os
import sqlite3
from datetime import datetime
from pathlib import Path
from version import get_app_dir

# Caminho base do projeto (suporta desenvolvimento e executável .exe)
BASE_DIR = get_app_dir()
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "clinica.db"


def get_db_connection() -> sqlite3.Connection:
    """Retorna uma conexão ativa com o banco de dados SQLite com WAL habilitado."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Inicializa as tabelas fundamentais do sistema se ainda não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabela de Usuários (com controle de perfis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK(perfil IN ('admin', 'secretaria')),
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # 2. Tabela de Logs de Auditoria (LGPD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            usuario_nome TEXT NOT NULL,
            acao TEXT NOT NULL,
            detalhe TEXT,
            data_hora TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_data ON audit_logs(data_hora DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_acao ON audit_logs(acao);")

    # 3. Tabela de Pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            alergias TEXT,
            observacoes_medicas TEXT,
            data_ultimo_atendimento_manual TEXT,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # 4. Tabela de Prontuário / Evolução Clínica Odontológica
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            dente_regiao TEXT,
            procedimento TEXT NOT NULL,
            descricao TEXT,
            profissional_nome TEXT NOT NULL,
            data_hora TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)

    # 5. Tabela de Anexos (Raio-X, Exames, Documentos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            nome_arquivo TEXT NOT NULL,
            caminho_arquivo TEXT NOT NULL,
            tamanho_bytes INTEGER,
            data_upload TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)

    # 6. Tabela da Agenda de Consultas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            data_consulta TEXT NOT NULL,
            horario TEXT NOT NULL,
            procedimento TEXT,
            status TEXT NOT NULL CHECK(status IN ('Agendado', 'Confirmado', 'Realizado', 'Cancelado', 'Remarcado', 'Faltou')) DEFAULT 'Agendado',
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)

    # 7. Tabela de Configurações do Sistema (Modelos de Mensagens WhatsApp, Chave Pix, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinic_settings (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );
    """)

    # 8. Tabela de Profissionais Parceiros da Sublocação da Sala 2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            especialidade TEXT,
            telefone TEXT,
            cpf TEXT,
            email TEXT,
            tipo_cobranca TEXT NOT NULL DEFAULT 'hora' CHECK(tipo_cobranca IN ('hora', 'turno', 'diaria', 'fixo')),
            valor_acordado REAL NOT NULL DEFAULT 50.0,
            usar_valor_padrao INTEGER NOT NULL DEFAULT 0,
            ativo INTEGER NOT NULL DEFAULT 1,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # 9. Tabela de Reservas e Sessões de Uso da Sala 2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            data_locacao TEXT NOT NULL,
            horario_previsto_inicio TEXT NOT NULL,
            horario_previsto_fim TEXT NOT NULL,
            horario_checkin TEXT,
            horario_checkout TEXT,
            duracao_minutos INTEGER DEFAULT 0,
            tipo_cobranca_aplicada TEXT NOT NULL DEFAULT 'hora',
            valor_base_hora REAL DEFAULT 50.0,
            valor_calculado REAL DEFAULT 0.0,
            valor_final REAL NOT NULL DEFAULT 0.0,
            status_sessao TEXT NOT NULL CHECK(status_sessao IN ('Agendado', 'Em Uso', 'Finalizado', 'Cancelado')) DEFAULT 'Agendado',
            status_pagamento TEXT NOT NULL CHECK(status_pagamento IN ('Pendente', 'Pago')) DEFAULT 'Pendente',
            forma_pagamento TEXT DEFAULT 'Pix',
            data_pagamento TEXT,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(partner_id) REFERENCES room_partners(id) ON DELETE CASCADE
        );
    """)

    # 10. Tabela de Controle de Estoque de Materiais e Insumos Odontológicos (Fase 5)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            unidade TEXT NOT NULL DEFAULT 'Unidade',
            quantidade REAL NOT NULL DEFAULT 0,
            estoque_minimo REAL NOT NULL DEFAULT 1,
            lote TEXT,
            data_validade TEXT,
            preco_custo REAL DEFAULT 0.0,
            localizacao TEXT,
            fornecedor TEXT,
            observacoes TEXT,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_nome ON inventory_items(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_cat ON inventory_items(categoria);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_val ON inventory_items(data_validade);")

    # 11. Tabela de Movimentações de Estoque (Histórico de Entradas, Saídas e Consumo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Entrada', 'Saida', 'Ajuste')),
            quantidade REAL NOT NULL,
            quantidade_anterior REAL NOT NULL,
            quantidade_nova REAL NOT NULL,
            motivo TEXT,
            user_id INTEGER,
            usuario_nome TEXT NOT NULL,
            data_hora TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_mov_item ON inventory_movements(item_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_mov_data ON inventory_movements(data_hora DESC);")

    # 12. Tabela de Categorias Customizáveis de Materiais (Fase 5)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # Popula categorias padrão se vazia
    cursor.execute("SELECT COUNT(*) FROM inventory_categories")
    if cursor.fetchone()[0] == 0:
        padroes = [
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
        for cat_nome in padroes:
            cursor.execute("INSERT OR IGNORE INTO inventory_categories (nome) VALUES (?)", (cat_nome,))

    # 13. Tabela de Categorias Financeiras (Fase 6)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        );
    """)

    # Popula categorias financeiras padrão se vazia
    cursor.execute("SELECT COUNT(*) FROM financial_categories")
    if cursor.fetchone()[0] == 0:
        padroes_fin = [
            ("Procedimentos Clínicos / Consultas", "Receita"),
            ("Sublocação", "Receita"),
            ("Outras Receitas", "Receita"),
            ("Insumos e Materiais Dentais", "Despesa"),
            ("Prótese e Laboratório Dental", "Despesa"),
            ("Aluguel, IPTU e Condomínio", "Despesa"),
            ("Energia Elétrica, Água e Internet", "Despesa"),
            ("Salários e Encargos", "Despesa"),
            ("CRO e Taxas Regulatórias", "Despesa"),
            ("Manutenção de Equipamentos", "Despesa"),
            ("Marketing e Divulgação", "Despesa"),
            ("Sistemas e Tarifas Bancárias", "Despesa"),
            ("Outras Despesas", "Despesa")
        ]
        for c_nome, c_tipo in padroes_fin:
            cursor.execute("INSERT INTO financial_categories (nome, tipo) VALUES (?, ?)", (c_nome, c_tipo))

    # 14. Tabela de Movimentações Financeiras / Fluxo de Caixa (Fase 6)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_competencia TEXT NOT NULL,
            data_vencimento TEXT,
            data_pagamento TEXT,
            status TEXT NOT NULL CHECK(status IN ('Pago', 'Pendente', 'Cancelado')) DEFAULT 'Pago',
            forma_pagamento TEXT NOT NULL DEFAULT 'Pix',
            parcelas INTEGER DEFAULT 1,
            patient_id INTEGER,
            rental_id INTEGER,
            comprovante_path TEXT,
            observacoes TEXT,
            user_id INTEGER,
            usuario_nome TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE SET NULL,
            FOREIGN KEY(rental_id) REFERENCES room_rentals(id) ON DELETE SET NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fin_data_comp ON financial_transactions(data_competencia DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fin_tipo ON financial_transactions(tipo);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fin_status ON financial_transactions(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fin_rental ON financial_transactions(rental_id);")

    # 15. Tabela de Anamnese Odontológica Completa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_anamnese (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE NOT NULL,
            queixa_principal TEXT,
            historico_doenca_atual TEXT,
            hipertensao INTEGER DEFAULT 0,
            diabetes INTEGER DEFAULT 0,
            cardiopatia INTEGER DEFAULT 0,
            problema_coagulacao INTEGER DEFAULT 0,
            doenca_renal_hepatica INTEGER DEFAULT 0,
            gestante_lactante INTEGER DEFAULT 0,
            fumante INTEGER DEFAULT 0,
            bruxismo INTEGER DEFAULT 0,
            alergias_medicamentos TEXT,
            alergia_latex INTEGER DEFAULT 0,
            medicamentos_uso TEXT,
            historico_cirurgico TEXT,
            observacoes TEXT,
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anamnese_patient ON patient_anamnese(patient_id);")

    # 16. Tabela do Odontograma Interativo (Mapeamento de dentes por paciente)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_odontograma (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            numero_dente INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'higido',
            faces TEXT DEFAULT '',
            observacoes TEXT DEFAULT '',
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            UNIQUE(patient_id, numero_dente),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_odonto_patient ON patient_odontograma(patient_id);")

    # 17. Tabela de Orçamentos e Planos de Tratamento Odontológico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            valor_bruto REAL NOT NULL DEFAULT 0.0,
            desconto REAL NOT NULL DEFAULT 0.0,
            valor_final REAL NOT NULL DEFAULT 0.0,
            forma_pagamento TEXT,
            status TEXT NOT NULL CHECK(status IN ('Pendente', 'Aprovado', 'Recusado', 'Concluído')) DEFAULT 'Pendente',
            observacoes TEXT,
            data_criacao TEXT NOT NULL,
            data_aprovacao TEXT,
            aprovado_por TEXT,
            user_id INTEGER NOT NULL,
            user_nome TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            atualizado_em TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_patient ON patient_budgets(patient_id);")

    # 18. Tabela de Itens do Orçamento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_budget_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER NOT NULL,
            dente_regiao TEXT,
            procedimento TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            valor_unitario REAL NOT NULL DEFAULT 0.0,
            valor_total REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY(budget_id) REFERENCES patient_budgets(id) ON DELETE CASCADE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_items ON patient_budget_items(budget_id);")

    # Migrações suaves para tabelas existentes
    try:
        cursor.execute("ALTER TABLE patients ADD COLUMN data_ultimo_atendimento_manual TEXT;")
    except sqlite3.OperationalError:
        pass  # Já existe

    try:
        cursor.execute("ALTER TABLE patients ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1;")
    except sqlite3.OperationalError:
        pass  # Já existe

    # Migração / Padronização de nomenclatura: 'Sublocação de Consultório (Sala 2)' -> 'Sublocação'
    try:
        cursor.execute("UPDATE financial_categories SET nome = 'Sublocação' WHERE nome = 'Sublocação de Consultório (Sala 2)'")
        cursor.execute("UPDATE financial_transactions SET categoria = 'Sublocação' WHERE categoria = 'Sublocação de Consultório (Sala 2)'")
        # Substitui '&' por 'e' em categorias e lançamentos
        cursor.execute("UPDATE financial_categories SET nome = REPLACE(nome, ' & ', ' e ') WHERE nome LIKE '% & %'")
        cursor.execute("UPDATE financial_transactions SET categoria = REPLACE(categoria, ' & ', ' e ') WHERE categoria LIKE '% & %'")
        cursor.execute("UPDATE inventory_categories SET nome = REPLACE(nome, ' & ', ' e ') WHERE nome LIKE '% & %'")
        cursor.execute("UPDATE inventory_items SET categoria = REPLACE(categoria, ' & ', ' e ') WHERE categoria LIKE '% & %'")
    except Exception:
        pass

    conn.commit()
    conn.close()


def fazer_backup_diario() -> bool:
    """Cria uma cópia de segurança diária do banco SQLite na pasta data/backups/."""
    try:
        if not DB_PATH.exists():
            return False
        backups_dir = DATA_DIR / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        backup_file = backups_dir / f"clinica_backup_{hoje_str}.db"

        # Se o backup de hoje ainda não existe, cria agora
        if not backup_file.exists():
            import shutil
            shutil.copy2(DB_PATH, backup_file)
            return True
        return True
    except Exception:
        return False
