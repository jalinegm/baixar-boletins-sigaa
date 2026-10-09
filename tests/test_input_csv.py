import tempfile
import unittest
from pathlib import Path

from baixar_boletins.input_csv import carregar_matriculas


class InputCsvTests(unittest.TestCase):
    def test_aceita_variantes_do_cabecalho(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matriculas.csv"
            for header in ("Matrícula", "Matricula", "MATRICULA", "matricula"):
                with self.subTest(header=header):
                    path.write_text(f"{header}\n123456\n", encoding="utf-8-sig")
                    matriculas, duplicadas, invalidas = carregar_matriculas(path)
                    self.assertEqual(matriculas, ["123456"])
                    self.assertEqual(duplicadas, [])
                    self.assertEqual(invalidas, [])
