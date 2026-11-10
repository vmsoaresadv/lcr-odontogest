"""
Testes Unitários da Fase 8: Prescrições, Receituários e Atestados Odontológicos Inteligentes
Testa criação, edição, exclusão e geração de documentos e modelos.
"""

import sys
import unittest
from PySide6.QtWidgets import QApplication

from database.connection import init_db
from services.patient_service import create_patient
from services.clinical_docs_service import (
    list_prescription_templates, get_prescription_template,
    create_prescription_template, update_prescription_template, delete_prescription_template,
    list_certificate_templates, get_certificate_template,
    create_certificate_template, update_certificate_template, delete_certificate_template,
    issue_clinical_document, list_patient_issued_documents, get_issued_document, delete_issued_document,
    gerar_html_receituario, gerar_html_atestado
)


class TestClinicalDocsService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_prescription_templates_crud(self):
        # 1. Criação
        ok, msg, tid = create_prescription_template(
            nome="Medicamento Teste",
            concentracao_forma="500mg",
            posologia="1 cp a cada 8h por 5 dias",
            orientacoes="Tomar com água",
            categoria="Analgésicos"
        )
        self.assertTrue(ok)
        self.assertIsNotNone(tid)

        # 2. Leitura
        t = get_prescription_template(tid)
        self.assertIsNotNone(t)
        self.assertEqual(t["nome_medicamento"], "Medicamento Teste")
        self.assertEqual(t["categoria"], "Analgésicos")

        # 3. Atualização
        ok_up, msg_up = update_prescription_template(
            template_id=tid,
            nome="Medicamento Teste Atualizado",
            concentracao_forma="750mg",
            posologia="1 cp a cada 12h",
            categoria="Analgésicos"
        )
        self.assertTrue(ok_up)
        t_up = get_prescription_template(tid)
        self.assertEqual(t_up["nome_medicamento"], "Medicamento Teste Atualizado")
        self.assertEqual(t_up["concentracao_forma"], "750mg")

        # 4. Exclusão (Desativação)
        ok_del, _ = delete_prescription_template(tid)
        self.assertTrue(ok_del)
        templates_ativos = list_prescription_templates(categoria="Analgésicos")
        self.assertNotIn(tid, [x["id"] for x in templates_ativos])

    def test_certificate_templates_crud(self):
        # 1. Criação
        ok, msg, cid = create_certificate_template(
            titulo="Atestado de Teste Repouso",
            tipo="Atestado",
            texto_padrao="Paciente esteve sob cuidados necessitando de {dias} dias.",
            dias_repouso=3
        )
        self.assertTrue(ok)
        self.assertIsNotNone(cid)

        # 2. Leitura
        c = get_certificate_template(cid)
        self.assertIsNotNone(c)
        self.assertEqual(c["dias_repouso"], 3)

        # 3. Atualização
        ok_up, _ = update_certificate_template(
            template_id=cid,
            titulo="Atestado Editado",
            tipo="Atestado",
            texto_padrao="Texto modificado",
            dias_repouso=2
        )
        self.assertTrue(ok_up)
        c_up = get_certificate_template(cid)
        self.assertEqual(c_up["titulo"], "Atestado Editado")
        self.assertEqual(c_up["dias_repouso"], 2)

        # 4. Exclusão
        ok_del, _ = delete_certificate_template(cid)
        self.assertTrue(ok_del)
        certs_ativos = list_certificate_templates(tipo="Atestado")
        self.assertNotIn(cid, [x["id"] for x in certs_ativos])

    def test_issue_document_and_html_generation(self):
        # Cria paciente teste com CPF dinâmico/único
        import random
        rand_cpf = f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}"
        ok_pat, msg_pat, pid = create_patient(
            nome="Paciente Documentos Teste",
            cpf=rand_cpf,
            data_nascimento="1990-05-15",
            telefone="(74) 99999-0000",
            email="paciente@teste.com",
            endereco="Rua Teste, 100",
            alergias="Nenhuma",
            observacoes_medicas="Saudável",
            user_id=1,
            user_nome="Dra. Lara Camila"
        )
        self.assertTrue(ok_pat, msg_pat)
        self.assertIsNotNone(pid)

        # Emite Receituário
        meds = [
            {"nome": "Amoxicilina", "concentracao": "500mg", "posologia": "1 cap 8/8h por 7 dias", "orientacoes": "Após as refeições"},
            {"nome": "Ibuprofeno", "concentracao": "600mg", "posologia": "1 comp 8/8h se dor", "orientacoes": ""}
        ]
        ok_rec, msg_rec, doc_rec_id = issue_clinical_document(
            tipo_documento="Receituario",
            patient_id=pid,
            titulo="Receita Pós-Operatória",
            conteudo=meds,
            user_id=1,
            usuario_nome="Dra. Lara Camila"
        )
        self.assertTrue(ok_rec)
        self.assertIsNotNone(doc_rec_id)

        # Emite Atestado
        ok_at, msg_at, doc_at_id = issue_clinical_document(
            tipo_documento="Atestado",
            patient_id=pid,
            titulo="Atestado 2 Dias",
            conteudo="Paciente realizou cirurgia.",
            dias_repouso=2,
            cid="K01.1",
            user_id=1,
            usuario_nome="Dra. Lara Camila"
        )
        self.assertTrue(ok_at)
        self.assertIsNotNone(doc_at_id)

        # Valida histórico de emissões do paciente
        docs = list_patient_issued_documents(pid)
        self.assertEqual(len(docs), 2)

        # Valida geração de HTML de Receita
        html_r = gerar_html_receituario("Paciente Documentos Teste", "999.888.777-66", meds)
        self.assertIn("Amoxicilina", html_r)
        self.assertIn("Receituário Odontológico", html_r)
        self.assertIn("Dra. Lara Camila", html_r)

        # Valida geração de HTML de Atestado
        html_a = gerar_html_atestado("Paciente Documentos Teste", "999.888.777-66", "Atestado", "Paciente realizou cirurgia.", dias_repouso=2, cid="K01.1")
        self.assertIn("Atestado Odontológico", html_a)
        self.assertIn("K01.1", html_a)
        self.assertIn("2 (dois) dia(s)", html_a)

        # Exclui documento emitido
        ok_del, _ = delete_issued_document(doc_rec_id)
        self.assertTrue(ok_del)
        self.assertEqual(len(list_patient_issued_documents(pid)), 1)

    def test_clinical_docs_ui_instantiation(self):
        from ui.clinical_docs_widget import (
            ClinicalDocsWidget, PrescriptionFormDialog, CertificateFormDialog,
            ManagePrescriptionTemplatesDialog, ManageCertificateTemplatesDialog
        )
        fake_user = {"id": 1, "nome": "Dra. Lara Camila", "perfil": "admin"}
        widget = ClinicalDocsWidget(patient_id=1, current_user=fake_user)
        self.assertIsNotNone(widget)

        dlg_p = PrescriptionFormDialog(patient_id=1, patient_nome="Paciente Teste", patient_cpf="111.222.333-44", current_user=fake_user)
        self.assertIsNotNone(dlg_p)

        dlg_c = CertificateFormDialog(patient_id=1, patient_nome="Paciente Teste", patient_cpf="111.222.333-44", current_user=fake_user)
        self.assertIsNotNone(dlg_c)

        dlg_mp = ManagePrescriptionTemplatesDialog(current_user=fake_user)
        self.assertIsNotNone(dlg_mp)

        dlg_mc = ManageCertificateTemplatesDialog(current_user=fake_user)
        self.assertIsNotNone(dlg_mc)


if __name__ == "__main__":
    unittest.main()
