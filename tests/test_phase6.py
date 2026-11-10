import unittest
import tempfile
import sys
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import database.connection as db_conn
import services.financial_service as fin_svc
import services.sublocacao_service as sub_svc


class TestPhase6Financial(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = db_conn.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_clinica_p6.db"
        db_conn.DB_PATH = self.test_db

        conn = db_conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, nome TEXT, login TEXT, senha_hash TEXT, perfil TEXT, ativo INTEGER);")
        cursor.execute("INSERT INTO users VALUES (1, 'Dra. Lara', 'dra.lara', 'hash', 'admin', 1);")
        conn.commit()
        conn.close()

        db_conn.init_db()

    def tearDown(self):
        db_conn.DB_PATH = self.orig_db_path
        self.temp_dir.cleanup()

    def test_categories_crud(self):
        # List default categories
        rec_cats = fin_svc.list_financial_categories("Receita")
        self.assertIn("Procedimentos Clínicos / Consultas", rec_cats)
        self.assertIn("Sublocação", rec_cats)

        desp_cats = fin_svc.list_financial_categories("Despesa")
        self.assertIn("Insumos e Materiais Dentais", desp_cats)

        # Create new category
        ok, msg, cat_id = fin_svc.create_financial_category("Harmonização Facial", "Receita", 1, "Dra. Lara")
        self.assertTrue(ok)
        self.assertIsNotNone(cat_id)

        # Check detailed listing
        detailed = fin_svc.list_financial_categories_detailed("Receita")
        nomes = [c["nome"] for c in detailed]
        self.assertIn("Harmonização Facial", nomes)

        # Delete category
        ok, _ = fin_svc.delete_financial_category(cat_id, 1, "Dra. Lara")
        self.assertTrue(ok)

    def test_create_and_get_transaction(self):
        ok, msg, t_id = fin_svc.create_transaction(
            tipo="Receita",
            categoria="Procedimentos Clínicos / Consultas",
            descricao="Restauração Estética Dente 11",
            valor=250.0,
            data_competencia="2026-11-07",
            status="Pago",
            forma_pagamento="Cartão de Crédito",
            parcelas=2,
            user_id=1,
            user_nome="Dra. Lara"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(t_id)

        t = fin_svc.get_transaction(t_id)
        self.assertIsNotNone(t)
        self.assertEqual(t["descricao"], "Restauração Estética Dente 11")
        self.assertEqual(t["valor"], 250.0)
        self.assertEqual(t["forma_pagamento"], "Cartão de Crédito")
        self.assertEqual(t["parcelas"], 2)

    def test_update_and_delete_transaction(self):
        ok, _, t_id = fin_svc.create_transaction(
            tipo="Despesa",
            categoria="Insumos e Materiais Dentais",
            descricao="Compra de Luvas e Babadores",
            valor=120.0,
            data_competencia="2026-11-07",
            status="Pago",
            forma_pagamento="Dinheiro",
            user_id=1,
            user_nome="Dra. Lara"
        )
        self.assertTrue(ok)

        # Update
        ok, msg = fin_svc.update_transaction(
            t_id, "Despesa", "Insumos e Materiais Dentais",
            "Compra de Luvas, Babadores e Anestésicos", 180.0,
            "2026-11-07", status="Pago", forma_pagamento="Pix",
            user_id=1, user_nome="Dra. Lara"
        )
        self.assertTrue(ok)

        t_up = fin_svc.get_transaction(t_id)
        self.assertEqual(t_up["valor"], 180.0)
        self.assertEqual(t_up["forma_pagamento"], "Pix")

        # Delete
        ok_del, _ = fin_svc.delete_transaction(t_id, 1, "Dra. Lara")
        self.assertTrue(ok_del)
        self.assertIsNone(fin_svc.get_transaction(t_id))

    def test_marcar_como_pago(self):
        ok, _, t_id = fin_svc.create_transaction(
            tipo="Receita",
            categoria="Procedimentos Clínicos / Consultas",
            descricao="Clareamento Dental",
            valor=800.0,
            data_competencia="2026-11-07",
            data_vencimento="2026-11-15",
            status="Pendente",
            forma_pagamento="Boleto",
            user_id=1,
            user_nome="Dra. Lara"
        )
        self.assertTrue(ok)

        t_pend = fin_svc.get_transaction(t_id)
        self.assertEqual(t_pend["status"], "Pendente")

        ok_baixa, _ = fin_svc.marcar_como_pago(t_id, "2026-11-10", "Dinheiro", 1, "Dra. Lara")
        self.assertTrue(ok_baixa)

        t_pago = fin_svc.get_transaction(t_id)
        self.assertEqual(t_pago["status"], "Pago")
        self.assertEqual(t_pago["forma_pagamento"], "Dinheiro")
        self.assertEqual(t_pago["data_pagamento"], "2026-11-10")

    def test_financial_kpis_and_dre(self):
        # Receita 1: 500 (Pix, Pago)
        fin_svc.create_transaction("Receita", "Procedimentos Clínicos / Consultas", "Consulta 1", 500.0, "2026-11-05", status="Pago", forma_pagamento="Pix")
        # Receita 2: 300 (Cartão de Débito, Pago)
        fin_svc.create_transaction("Receita", "Procedimentos Clínicos / Consultas", "Consulta 2", 300.0, "2026-11-06", status="Pago", forma_pagamento="Cartão de Débito")
        # Receita 3: 200 (Pendente)
        fin_svc.create_transaction("Receita", "Procedimentos Clínicos / Consultas", "Pendente", 200.0, "2026-11-15", status="Pendente", forma_pagamento="Pix")

        # Despesa 1: 150 (Dinheiro, Pago)
        fin_svc.create_transaction("Despesa", "Aluguel, IPTU & Condomínio", "Condomínio", 150.0, "2026-11-01", status="Pago", forma_pagamento="Dinheiro")
        # Despesa 2: 50 (Pendente)
        fin_svc.create_transaction("Despesa", "Insumos e Materiais Dentais", "Brocas", 50.0, "2026-11-20", status="Pendente", forma_pagamento="Boleto")

        kpis = fin_svc.get_financial_kpis("2026-11-01", "2026-11-30")
        self.assertEqual(kpis["total_receitas"], 800.0)
        self.assertEqual(kpis["total_despesas"], 150.0)
        self.assertEqual(kpis["saldo_liquido"], 650.0)
        self.assertEqual(kpis["pendente_receber"], 200.0)
        self.assertEqual(kpis["pendente_pagar"], 50.0)

        dre = fin_svc.get_dre_resumido("2026-11-01", "2026-11-30")
        self.assertEqual(dre["total_receitas"], 800.0)
        self.assertEqual(dre["total_despesas"], 150.0)
        self.assertEqual(dre["resultado_liquido"], 650.0)

    def test_sync_sublocacao_receita(self):
        # Cria parceiro e locação válidos para respeitar chave estrangeira
        ok_p, _, p_id = sub_svc.create_partner(
            nome="Dr. Rafael", especialidade="Ortodontia", telefone="74999990000",
            cpf="111.222.333-44", email="rafael@email.com", tipo_cobranca="hora",
            valor_acordado=60.0, usar_valor_padrao=False, observacoes="Sala 2",
            user_id=1, user_nome="Dra. Lara"
        )
        self.assertTrue(ok_p)
        ok_r, _, r_id = sub_svc.create_rental(
            partner_id=p_id, data_locacao="2026-11-07", horario_inicio="08:00",
            horario_fim="12:00", observacoes="Atendimento",
            user_id=1, user_nome="Dra. Lara"
        )
        self.assertTrue(ok_r)

        ok, msg = fin_svc.sync_sublocacao_receita(
            rental_id=r_id,
            valor=160.0,
            data_locacao="2026-11-07",
            forma_pagamento="Cartão de Crédito",
            partner_nome="Dr. Rafael",
            user_id=1,
            user_nome="Dra. Lara"
        )
        self.assertTrue(ok)

        txs = fin_svc.search_transactions(categoria="Sublocação")
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["valor"], 160.0)
        self.assertEqual(txs[0]["forma_pagamento"], "Cartão de Crédito")
        self.assertIn("Dr. Rafael", txs[0]["descricao"])

    def test_nota_fiscal_flow(self):
        # 1. Cria transação com Nota Fiscal
        ok, msg, tid = fin_svc.create_transaction(
            tipo="Receita",
            categoria="Procedimentos Clínicos / Consultas",
            descricao="Restauração Estética c/ NF",
            valor=350.0,
            data_competencia="2026-11-09",
            status="Pago",
            forma_pagamento="Pix",
            nota_fiscal_emitida=1,
            numero_nota_fiscal="NF-2026-99"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(tid)

        t = fin_svc.get_transaction(tid)
        self.assertIsNotNone(t)
        self.assertEqual(t["nota_fiscal_emitida"], 1)
        self.assertEqual(t["numero_nota_fiscal"], "NF-2026-99")

        # 2. Atualiza transação
        ok, msg = fin_svc.update_transaction(
            trans_id=tid,
            tipo="Receita",
            categoria="Procedimentos Clínicos / Consultas",
            descricao="Restauração Estética c/ NF Atualizada",
            valor=400.0,
            data_competencia="2026-11-09",
            status="Pago",
            forma_pagamento="Pix",
            nota_fiscal_emitida=0,
            numero_nota_fiscal=None
        )
        self.assertTrue(ok)
        t2 = fin_svc.get_transaction(tid)
        self.assertEqual(t2["nota_fiscal_emitida"], 0)
        self.assertIsNone(t2["numero_nota_fiscal"])

        # 3. Baixa rápida com marcação de NF
        ok, msg, tid2 = fin_svc.create_transaction(
            tipo="Receita",
            categoria="Outras Receitas",
            descricao="Procedimento Pendente",
            valor=200.0,
            data_competencia="2026-11-09",
            status="Pendente",
            forma_pagamento="Boleto"
        )
        self.assertTrue(ok)
        ok, msg = fin_svc.marcar_como_pago(
            trans_id=tid2,
            data_pagamento="2026-11-09",
            forma_pagamento="Pix",
            nota_fiscal_emitida=1,
            numero_nota_fiscal="NF-1001"
        )
        self.assertTrue(ok)
        t_baixa = fin_svc.get_transaction(tid2)
        self.assertEqual(t_baixa["status"], "Pago")
        self.assertEqual(t_baixa["nota_fiscal_emitida"], 1)
        self.assertEqual(t_baixa["numero_nota_fiscal"], "NF-1001")

    def test_recorrente_e_alertas_vencimento(self):
        # 1. Cria transação recorrente de aluguel
        ok, msg, tid = fin_svc.create_transaction(
            tipo="Despesa",
            categoria="Aluguel, IPTU e Condomínio",
            descricao="Aluguel Consultório Recorrente",
            valor=1500.0,
            data_competencia="2026-11-01",
            data_vencimento="2026-11-05",
            status="Pendente",
            forma_pagamento="Boleto",
            recorrente=1,
            dia_vencimento_recorrente=5
        )
        self.assertTrue(ok)
        self.assertIsNotNone(tid)

        # 2. Verifica templates cadastrados
        templates = fin_svc.list_recurring_templates(apenas_ativos=True)
        self.assertTrue(any(t["descricao"] == "Aluguel Consultório Recorrente" for t in templates))
        tmpl = next(t for t in templates if t["descricao"] == "Aluguel Consultório Recorrente")
        self.assertEqual(tmpl["dia_vencimento"], 5)

        # 3. Geração para o mês seguinte (2026-12)
        gerados = fin_svc.gerar_transacoes_recorrentes_pendentes(mes_ano_ref="2026-12")
        self.assertGreaterEqual(gerados, 1)

        # Verifica se gerou o lançamento com vencimento correto
        txs_dez = fin_svc.search_transactions(data_inicio="2026-12-01", data_fim="2026-12-31")
        self.assertTrue(any("Aluguel Consultório Recorrente" in t["descricao"] for t in txs_dez))
        t_dez = next(t for t in txs_dez if "Aluguel Consultório Recorrente" in t["descricao"])
        self.assertEqual(t_dez["status"], "Pendente")
        self.assertEqual(str(t_dez["data_vencimento"])[:10], "2026-12-05")

        # 4. Alertas de vencimento:
        # Se criarmos uma despesa vencendo hoje:
        from datetime import date
        hoje_str = date.today().isoformat()
        ok, msg, tid_hoje = fin_svc.create_transaction(
            tipo="Despesa",
            categoria="Insumos e Materiais Dentais",
            descricao="Dental Cremer Vence Hoje",
            valor=350.0,
            data_competencia=hoje_str,
            data_vencimento=hoje_str,
            status="Pendente"
        )
        self.assertTrue(ok)

        alertas = fin_svc.verificar_alertas_vencimento(dias_antecedencia=1)
        self.assertTrue(any(a["id"] == tid_hoje for a in alertas))
        alerta_item = next(a for a in alertas if a["id"] == tid_hoje)
        self.assertEqual(alerta_item["urgencia"], "hoje")
        self.assertIn("Hoje", alerta_item["urgencia_label"])

        # 5. Cancela molde de recorrência
        self.assertTrue(fin_svc.cancel_recurring_template(tmpl["id"]))
        templates_pos = fin_svc.list_recurring_templates(apenas_ativos=True)
        self.assertFalse(any(t["id"] == tmpl["id"] for t in templates_pos))


if __name__ == "__main__":
    unittest.main()
