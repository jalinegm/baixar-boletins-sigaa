import tkinter as tk
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from baixar_boletins.gui import App


class GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Interface gráfica indisponível: {exc}")
        self.addCleanup(self.root.destroy)
        self.app = App(self.root)

    def test_csv_nao_muda_durante_lote(self):
        self.app.csv_path = Path("alunos.csv")
        self.app.running = True
        with patch("baixar_boletins.gui.filedialog.askopenfilename") as dialog:
            self.app._choose_csv()
        dialog.assert_not_called()
        self.assertEqual(self.app.csv_path, Path("alunos.csv"))

    def test_controles_cabem_na_janela_minima(self):
        self.root.geometry("760x680")
        self.app._set_phase(1)
        self.app.start_button.pack_forget()
        self.app.continue_button.pack(side="right")
        self.app.stop_button.pack(side="left")
        self.root.update()

        self.assertLessEqual(
            self.app.stop_button.winfo_x() + self.app.stop_button.winfo_width(),
            self.app.continue_button.winfo_x(),
        )
        self.app._set_phase(2)
        self.root.update()
        self.assertGreaterEqual(self.app.table.winfo_height(), 100)

    def test_titulo_centralizado_e_acoes_na_ordem(self):
        self.root.update()
        title_center = (
            self.app.title_label.winfo_rootx()
            + self.app.title_label.winfo_width() / 2
        )
        window_center = self.root.winfo_rootx() + self.root.winfo_width() / 2
        self.assertAlmostEqual(title_center, window_center, delta=2)
        self.assertEqual(self.app.choose_button.pack_info()["side"], "right")

        self.app.csv_path = Path("exemplo.csv")
        self.app._set_phase(0)
        self.root.update()
        self.assertEqual(self.app.choose_button.pack_info()["side"], "left")
        self.assertEqual(self.app.keep_file_button.pack_info()["side"], "right")

        self.app._set_phase(1)
        self.assertEqual(self.app.change_button.pack_info()["side"], "left")
        self.assertEqual(self.app.start_button.pack_info()["side"], "right")

    def test_mostra_uma_etapa_por_vez(self):
        panels = (
            self.app.file_panel,
            self.app.process_panel,
            self.app.results_panel,
        )
        for phase in range(3):
            self.app._set_phase(phase)
            self.root.update()
            self.assertEqual(
                [panel.winfo_manager() == "pack" for panel in panels],
                [index == phase for index in range(3)],
            )

    def test_csv_valido_avanca_para_acesso_e_lote_para_resultados(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "exemplo.csv"
            csv_path.write_text("Matricula\n12345\n", encoding="utf-8")
            with patch(
                "baixar_boletins.gui.filedialog.askopenfilename",
                return_value=str(csv_path),
            ):
                self.app._choose_csv()

        self.assertEqual(self.app.phase, 1)
        self.assertEqual(self.app.start_button.cget("state"), "normal")
        self.assertEqual(self.app.choose_button.cget("text"), "Escolher outro CSV")

        self.app._handle_event("iniciando", {"matricula": "12345"})
        self.assertEqual(self.app.phase, 2)
        self.assertEqual(self.app.table.set("12345", "resultado"), "Processando...")

        self.app._handle_event("concluido", {"resumo": {
            "sucesso": 1, "nao_encontrada": 0, "erro": 0,
        }})
        self.app._handle_event("fim_worker", {})
        self.assertEqual(self.app.new_file_button.winfo_manager(), "pack")
        self.assertEqual(self.app.retry_button.winfo_manager(), "")

        self.root.update()
        self.app.phase_widgets[0][2].event_generate("<Button-1>")
        self.assertEqual(self.app.phase, 0)
        self.assertEqual(self.app.csv_path.name, "exemplo.csv")
        self.assertEqual(self.app.keep_file_button.winfo_manager(), "pack")

    def test_voltar_ao_arquivo_permite_trocar_ou_continuar(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "exemplo.csv"
            csv_path.write_text("Matricula\n12345\n", encoding="utf-8")
            with patch(
                "baixar_boletins.gui.filedialog.askopenfilename",
                return_value=str(csv_path),
            ):
                self.app._choose_csv()

            self.root.update()
            self.app.phase_widgets[0][2].event_generate("<Button-1>")
            self.assertEqual(self.app.phase, 0)
            self.assertEqual(self.app.csv_path, csv_path)
            self.assertEqual(self.app.keep_file_button.winfo_manager(), "pack")
            self.assertEqual(self.app.choose_button.cget("text"), "Escolher outro CSV")

            self.app.keep_file_button.invoke()
            self.assertEqual(self.app.phase, 1)

            self.app.change_button.invoke()
            self.assertEqual(self.app.phase, 0)
            self.app.running = True
            self.app._continue_with_file()
            self.assertEqual(self.app.phase, 0)

    def test_sobre_mostra_creditos(self):
        self.app._show_about()
        self.root.update()
        window = self.app.about_window
        self.assertTrue(window.winfo_exists())
        texts = [widget.cget("text") for widget in window.winfo_children()[1].winfo_children()
                 if isinstance(widget, tk.Label)]
        self.assertIn("IFFar Campus Alegrete", texts)
        self.assertTrue(any("Prof. Daniel Temp" in text for text in texts))
        author = next(
            widget for widget in window.winfo_children()[1].winfo_children()
            if isinstance(widget, tk.Label)
            and "Prof. Daniel Temp" in widget.cget("text")
        )
        self.assertNotIn("bold", author.cget("font"))
        window.destroy()

    def test_csv_de_exemplo_pode_ser_salvo_e_lido(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "exemplo.csv"
            with patch(
                "baixar_boletins.gui.filedialog.asksaveasfilename",
                return_value=str(csv_path),
            ), patch("baixar_boletins.gui.messagebox.showinfo"):
                self.app.example_button.invoke()
            self.assertTrue(csv_path.exists())
            with patch(
                "baixar_boletins.gui.filedialog.askopenfilename",
                return_value=str(csv_path),
            ):
                self.app._choose_csv()
            self.assertEqual(self.app.phase, 1)
            self.assertEqual(self.app.matriculas, ["123456", "789012"])


if __name__ == "__main__":
    unittest.main()
