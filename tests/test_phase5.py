import unittest
import tempfile
import sys
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import database.connection as db_conn
import services.inventory_service as inv_svc


class TestPhase5Inventory(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = db_conn.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_clinica_p5.db"
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

    def test_create_and_get_item(self):
        ok, msg, item_id = inv_svc.create_item(
            nome="Resina Z350 XT A2",
            categoria="Dentística & Resinas",
            unidade="Seringa",
            quantidade=5.0,
            estoque_minimo=2.0,
            lote="L12345",
            data_validade="2027-12-31",
            preco_custo=140.0,
            localizacao="Gaveteiro 1",
            fornecedor="Dental Cremer",
            user_id=1,
            user_nome="Dra. Lara"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(item_id)

        item = inv_svc.get_item(item_id)
        self.assertEqual(item["nome"], "Resina Z350 XT A2")
        self.assertEqual(item["quantidade"], 5.0)
        self.assertEqual(item["estoque_minimo"], 2.0)

    def test_stock_movement_in_and_out(self):
        _, _, item_id = inv_svc.create_item(
            nome="Anestésico Mepivacaína",
            categoria="Anestésicos & Farmacologia",
            unidade="Caixa",
            quantidade=10.0,
            estoque_minimo=3.0,
            preco_custo=85.0
        )

        # 1. Saída (Consumo Clínico) de 4 caixas
        ok, msg = inv_svc.add_stock_movement(item_id, "Saida", 4.0, "Uso em cirurgias", 1, "Dra. Lara")
        self.assertTrue(ok)
        item = inv_svc.get_item(item_id)
        self.assertEqual(item["quantidade"], 6.0)

        # 2. Entrada (Compra) de 5 caixas
        ok, msg = inv_svc.add_stock_movement(item_id, "Entrada", 5.0, "Nota Fiscal 987", 1, "Dra. Lara")
        self.assertTrue(ok)
        item = inv_svc.get_item(item_id)
        self.assertEqual(item["quantidade"], 11.0)

        # 3. Tentativa de saída maior que o saldo (deve ser bloqueada)
        ok, msg = inv_svc.add_stock_movement(item_id, "Saida", 20.0, "Uso excessivo", 1, "Dra. Lara")
        self.assertFalse(ok)
        self.assertIn("Saldo insuficiente", msg)

        # 4. Verifica histórico de movimentações
        movs = inv_svc.list_movements(item_id)
        self.assertGreaterEqual(len(movs), 3)  # Cadastro inicial + Saída + Entrada

    def test_kpis_and_alerts(self):
        hoje = date.today()
        vencido_str = (hoje - timedelta(days=5)).strftime("%Y-%m-%d")
        avencer_str = (hoje + timedelta(days=10)).strftime("%Y-%m-%d")
        normal_str = (hoje + timedelta(days=365)).strftime("%Y-%m-%d")

        # Item 1: Estoque baixo (qtd 1 <= min 2)
        inv_svc.create_item("Luva Nitrílica M", "Biossegurança & Descartáveis", "Caixa", 1.0, 2.0, preco_custo=35.0, data_validade=normal_str)
        # Item 2: Vencido
        inv_svc.create_item("Ácido Fosfórico Vencido", "Dentística & Resinas", "Frasco", 4.0, 1.0, preco_custo=20.0, data_validade=vencido_str)
        # Item 3: A vencer em 10 dias
        inv_svc.create_item("Adesivo Single Bond", "Dentística & Resinas", "Frasco", 2.0, 1.0, preco_custo=100.0, data_validade=avencer_str)

        kpis = inv_svc.get_inventory_kpis()
        self.assertEqual(kpis["total_itens"], 3)
        self.assertEqual(kpis["estoque_baixo"], 1)  # Luva
        self.assertEqual(kpis["vencidos_ou_avencer"], 2)  # Ácido + Adesivo
        # Valor total: (1*35) + (4*20) + (2*100) = 35 + 80 + 200 = 315.0
        self.assertEqual(kpis["valor_total"], 315.0)

        # Filtro de busca por alerta
        baixos = inv_svc.search_items(filtro_alerta="baixo")
        self.assertEqual(len(baixos), 1)
        self.assertEqual(baixos[0]["nome"], "Luva Nitrílica M")


if __name__ == "__main__":
    unittest.main()
