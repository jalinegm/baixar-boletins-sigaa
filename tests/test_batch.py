import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from baixar_boletins.batch import ExecucaoInterrompida, executar


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csv = self.root / "alunos.csv"
        self.csv.write_text("Matricula\n12345\n67890\n", encoding="utf-8")
        self.output = self.root / "boletins"

    @patch("baixar_boletins.batch.time.sleep")
    @patch("baixar_boletins.batch.gerar_pdf")
    @patch("baixar_boletins.batch.SigaaSessao")
    def test_processa_e_retoma_sem_abrir_navegador(self, session_class, pdf, _sleep):
        events = []

        def save_pdf(_page, path):
            Path(path).write_bytes(b"%PDF-1.4\n")

        pdf.side_effect = save_pdf
        first = executar(
            self.csv, pasta=self.output,
            on_event=lambda kind, **data: events.append((kind, data)),
        )
        self.assertEqual(first["sucesso"], 2)
        self.assertEqual([e[0] for e in events].count("resultado"), 2)
        self.assertEqual(session_class.call_count, 1)

        second = executar(self.csv, pasta=self.output)
        self.assertEqual(second["sucesso"], 2)
        self.assertEqual(session_class.call_count, 1)

    @patch("baixar_boletins.batch.SigaaSessao")
    def test_interrompe_antes_de_abrir_navegador(self, session_class):
        with self.assertRaises(ExecucaoInterrompida):
            executar(self.csv, pasta=self.output, should_stop=lambda: True)
        session_class.return_value.abrir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
