import unittest
import tempfile
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from datetime import date
import database.connection as db_conn
import services.sublocacao_service as sub_svc
import services.pix_service as pix_svc


class TestPhase4Sublocacao(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = db_conn.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_clinica_p4.db"
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

    def test_01_configuracoes_sublocacao_e_pix(self):
        cfg = sub_svc.get_sublocacao_settings()
        self.assertEqual(cfg["tarifa_hora"], 50.0)

        ok, msg = sub_svc.save_sublocacao_settings(
            60.0, 200.0, 350.0, "lara.pix@email.com", "LARA CAMILA", "IRECE", 1, "Dra. Lara"
        )
        self.assertTrue(ok)

        cfg_nova = sub_svc.get_sublocacao_settings()
        self.assertEqual(cfg_nova["tarifa_hora"], 60.0)
        self.assertEqual(cfg_nova["pix_chave"], "lara.pix@email.com")

    def test_02_cadastro_e_precificacao_parceiro(self):
        # Parceiro com tarifa própria
        ok, msg, pid1 = sub_svc.create_partner(
            "Dr. Rodrigo Biomédico", "Biomedicina", "74999991111", "11122233344",
            "rodrigo@email.com", "hora", 40.0, False, "Parceiro semanal", 1, "Dra. Lara"
        )
        self.assertTrue(ok)
        p1 = sub_svc.get_partner(pid1)
        self.assertEqual(p1["valor_acordado"], 40.0)
        self.assertEqual(p1["usar_valor_padrao"], 0)

        # Parceiro usando tarifa padrão da clínica
        ok, msg, pid2 = sub_svc.create_partner(
            "Dra. Camila Psicóloga", "Psicologia", "74999992222", "",
            "", "hora", 0.0, True, "", 1, "Dra. Lara"
        )
        self.assertTrue(ok)
        p2 = sub_svc.get_partner(pid2)
        self.assertEqual(p2["usar_valor_padrao"], 1)

    def test_03_ciclo_completo_reserva_checkin_checkout_e_ajuste_manual(self):
        ok, msg, pid = sub_svc.create_partner(
            "Dra. Marina Fisioterapeuta", "Fisioterapia", "74999993333", "",
            "", "hora", 50.0, False, "", 1, "Dra. Lara"
        )
        self.assertTrue(ok)

        # 1. Reserva das 14:00 às 16:00
        hoje_str = date.today().strftime("%Y-%m-%d")
        ok, msg, rid = sub_svc.create_rental(pid, hoje_str, "14:00", "16:00", "Sessão agendada", 1, "Dra. Lara")
        self.assertTrue(ok)
        r = sub_svc.get_rental(rid)
        self.assertEqual(r["status_sessao"], "Agendado")
        self.assertEqual(r["valor_final"], 100.0)  # 2h * 50

        # 2. Check-in às 14:05
        ok, msg = sub_svc.checkin_rental(rid, "14:05", 1, "Dra. Lara")
        self.assertTrue(ok)
        r = sub_svc.get_rental(rid)
        self.assertEqual(r["status_sessao"], "Em Uso")
        self.assertEqual(r["horario_checkin"], "14:05")

        # 3. Check-out às 16:35 (2h30min = 150min -> 150/60 * 50 = R$ 125.00)
        ok, msg, val_calc = sub_svc.checkout_rental(rid, "16:35", 1, "Dra. Lara")
        self.assertTrue(ok)
        self.assertEqual(val_calc, 125.0)

        # 4. Ajuste Manual do Valor (ex: dar desconto ou arredondar para R$ 120.00)
        ok, msg = sub_svc.update_rental_final_value(rid, 120.0, "Desconto de R$5 concedido", 1, "Dra. Lara")
        self.assertTrue(ok)
        r = sub_svc.get_rental(rid)
        self.assertEqual(r["valor_final"], 120.0)

        # 5. Geração de Pix e Marcação como Pago
        pix_code = pix_svc.generate_pix_copy_paste("749991266602", "LARA CAMILA", "IRECE", r["valor_final"])
        self.assertTrue(pix_code.startswith("000201"))
        self.assertIn("120.00", pix_code)

        ok, msg = sub_svc.mark_rental_as_paid(rid, "Pix", 1, "Dra. Lara")
        self.assertTrue(ok)
        r = sub_svc.get_rental(rid)
        self.assertEqual(r["status_pagamento"], "Pago")


if __name__ == "__main__":
    unittest.main()
