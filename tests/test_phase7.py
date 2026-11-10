import os
import unittest
import zipfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
import sys

from services.backup_service import (
    criar_backup_completo, listar_backups_locais, BACKUPS_DIR
)
from services.report_service import (
    gerar_html_dre_financeiro, gerar_html_relatorio_estoque, exportar_html_para_pdf
)
from services.updater_service import parse_version_tuple
from version import __version__, APP_NAME


class TestPhase7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Garante banco inicializado e instância do QApplication para testes com Qt GUI/PDF
        from database.connection import init_db
        init_db()
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_version_constants_and_parsing(self):
        self.assertEqual(__version__, "1.1.0")
        self.assertEqual(APP_NAME, "LCR OdontoGest")

        v_atual = parse_version_tuple("1.1.0")
        v_nova = parse_version_tuple("v1.1.1")
        v_maior = parse_version_tuple("2.0.0")

        self.assertEqual(v_atual, (1, 1, 0))
        self.assertEqual(v_nova, (1, 1, 1))
        self.assertTrue(v_nova > v_atual)
        self.assertTrue(v_maior > v_nova)

    def test_backup_creation_and_contents(self):
        teste_zip = BACKUPS_DIR / "teste_backup_unit.zip"
        if teste_zip.exists():
            teste_zip.unlink()

        sucesso, caminho = criar_backup_completo(str(teste_zip))
        self.assertTrue(sucesso, f"Falha no backup: {caminho}")
        self.assertTrue(os.path.exists(caminho))

        # Valida integridade do arquivo ZIP
        with zipfile.ZipFile(caminho, "r") as z:
            namelist = z.namelist()
            self.assertIn("clinica.db", namelist)
            self.assertIn("manifesto.json", namelist)

        if os.path.exists(caminho):
            os.remove(caminho)

    def test_reports_html_and_pdf(self):
        # 1. DRE
        html_dre = gerar_html_dre_financeiro("2026-11-01", "2026-11-30")
        self.assertIn("Demonstrativo Financeiro", html_dre)
        self.assertIn("Dra. Lara Camila", html_dre)

        # 2. Estoque
        html_est = gerar_html_relatorio_estoque()
        self.assertIn("Posição Geral de Estoque e Validades", html_est)
        self.assertIn("CRO-BA 15247", html_est)

        # 3. Exportação de PDF
        pdf_temp = Path("teste_report_unit.pdf")
        if pdf_temp.exists():
            pdf_temp.unlink()

        sucesso_pdf = exportar_html_para_pdf(html_dre, str(pdf_temp))
        self.assertTrue(sucesso_pdf)
        self.assertTrue(pdf_temp.exists())
        self.assertGreater(pdf_temp.stat().st_size, 1000)

        if pdf_temp.exists():
            pdf_temp.unlink()


if __name__ == "__main__":
    unittest.main()
