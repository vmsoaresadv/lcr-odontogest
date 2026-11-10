"""
Testes Unitários para a Linha do Tempo 360°, Automações de Pós-Operatório e Aniversariantes.
"""

import sys
import unittest
from datetime import date, timedelta
from PySide6.QtWidgets import QApplication

from database.connection import init_db
from services.patient_service import create_patient, get_patient_timeline_events, add_record
from services.schedule_service import (
    create_appointment, update_appointment_status,
    get_post_operative_patients, get_birthday_patients,
    build_post_operative_message, build_birthday_message
)
from services.financial_service import create_transaction


class TestTimelineAndAutomations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_post_operative_and_birthday_messages(self):
        msg_pos = build_post_operative_message("Carlos Silva", "Exodontia Simples")
        self.assertIn("Carlos", msg_pos)
        self.assertIn("Exodontia Simples", msg_pos)
        self.assertIn("Dra. Lara Camila", msg_pos)

        msg_niver = build_birthday_message("Mariana Souza")
        self.assertIn("Mariana", msg_niver)
        self.assertIn("Feliz Aniversário", msg_niver)

    def test_timeline_events_aggregation(self):
        # 1. Cria paciente de teste
        import random
        cpf_num = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
        ok, msg, pid = create_patient(
            nome="Paciente Timeline Teste",
            cpf=cpf_num,
            data_nascimento="1995-11-10",
            telefone="(74) 99999-0000",
            email="timeline@teste.com",
            endereco="Rua Central, 12",
            alergias="",
            observacoes_medicas="",
            user_id=1,
            user_nome="Admin"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(pid)

        # 2. Cria consulta realizada
        hoje_str = date.today().strftime("%Y-%m-%d")
        ok_app, _ = create_appointment(pid, hoje_str, "14:00", "Avaliação e Limpeza", "", 1, "Admin")
        self.assertTrue(ok_app)

        # 3. Cria prontuário
        ok_rec, _ = add_record(
            patient_id=pid,
            dente_regiao="16",
            procedimento="Restauração Resina",
            descricao="Procedimento bem sucedido",
            profissional_nome="Dra. Lara Camila",
            user_id=1
        )
        self.assertTrue(ok_rec)

        # 4. Cria transação financeira
        ok_trans, msg_t, tid = create_transaction("Receita", "Procedimentos Clínicos / Consultas", "Pagamento Consulta", 250.0, hoje_str, patient_id=pid)
        self.assertTrue(ok_trans)

        # 5. Busca eventos na Linha do Tempo 360°
        eventos = get_patient_timeline_events(pid)
        self.assertGreaterEqual(len(eventos), 3)

        categorias = [e["categoria"] for e in eventos]
        self.assertIn("clinico", categorias)
        self.assertIn("financeiro", categorias)

    def test_ui_components_instantiation(self):
        from ui.timeline_360_widget import Timeline360Widget
        from ui.schedule_view import AppointmentConclusionDialog
        from ui.financial_view import TransactionFormDialog

        fake_user = {"id": 1, "nome": "Admin", "perfil": "admin"}
        t_widget = Timeline360Widget(patient_id=1, current_user=fake_user)
        self.assertIsNotNone(t_widget)

        fake_app = {"id": 1, "patient_id": 1, "paciente_nome": "Carlos", "procedimento": "Consulta"}
        dlg_concl = AppointmentConclusionDialog(fake_app, fake_user)
        self.assertIsNotNone(dlg_concl)

        dlg_trans = TransactionFormDialog(fake_user, tipo="Receita", initial_data={"descricao": "Teste", "valor": 150.0})
        self.assertIsNotNone(dlg_trans)


if __name__ == "__main__":
    unittest.main()
