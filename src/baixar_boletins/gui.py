import csv
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import input_csv, report
from .batch import ExecucaoInterrompida, executar
from .sigaa_nav import ErroLogin, ErroNavegacao

ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False) else Path.cwd()
)
OUTPUT_DIR = ROOT / "boletins"
PROFILE_DIR = ROOT / ".perfil-sigaa"
ASSET_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2])) / "assets"

BG = "#f5f7f3"
PANEL = "#ffffff"
INK = "#1b3027"
MUTED = "#52665c"
GREEN = "#236947"
GREEN_LIGHT = "#e6f1e9"
LINE = "#dce5dc"
AMBER = "#9b6518"
RED = "#a23732"

STATUS_LABELS = {
    None: "Aguardando",
    report.STATUS_SUCESSO: "Baixado",
    report.STATUS_NAO_ENCONTRADA: "Não encontrado",
    report.STATUS_ERRO: "Erro — tentar novamente",
}


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Boletins SIGAA · IFFar")
        self.root.iconbitmap(default=str(ASSET_DIR / "boletim.ico"))
        self.root.geometry("980x740")
        self.root.minsize(760, 680)
        self.root.configure(bg=BG)
        self.csv_path = None
        self.matriculas = []
        self.events = queue.Queue()
        self.continue_event = threading.Event()
        self.stop_event = threading.Event()
        self.running = False
        self.close_when_done = False
        self.processed = 0
        self.details = {}
        self.closed = False
        self.phase = 0
        self.retry_available = False
        self.about_window = None

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(100, self._drain_events)

    def _label(self, parent, text, size=10, color=INK, weight="normal", **kwargs):
        return tk.Label(
            parent, text=text, bg=parent.cget("bg"), fg=color,
            font=("Segoe UI", size, weight), anchor="w", **kwargs,
        )

    def _button(self, parent, text, command, primary=False):
        button = tk.Button(
            parent, text=text, command=command, relief="flat", cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=16, pady=9,
            bg=GREEN if primary else PANEL,
            fg="white" if primary else GREEN,
            activebackground="#1b563a" if primary else GREEN_LIGHT,
            activeforeground="white" if primary else GREEN,
            highlightthickness=2, highlightbackground=GREEN if primary else LINE,
            highlightcolor=AMBER, takefocus=True,
            disabledforeground="#9aaba1",
        )
        return button

    def _build(self):
        header = tk.Frame(self.root, bg=INK, padx=34, pady=22)
        header.pack(fill="x")
        self.header = header
        self.logo = tk.PhotoImage(file=ASSET_DIR / "iffar-branco-small.png")
        tk.Label(header, image=self.logo, bg=INK).pack(side="left")
        self.title_label = self._label(
            header, "Boletins SIGAA", 25, PANEL, "bold",
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")
        tk.Button(
            header, text="Sobre", command=self._show_about, bg=INK, fg=PANEL,
            activebackground=GREEN, activeforeground=PANEL,
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=7, highlightthickness=1,
            highlightbackground=PANEL, highlightcolor=AMBER, takefocus=True,
        ).pack(side="right")

        steps = tk.Frame(self.root, bg=BG, padx=34, pady=18)
        steps.pack(fill="x")
        self.phase_widgets = []
        for number, title in enumerate(("Arquivo", "Acesso ao SIGAA", "Boletins"), 1):
            item = tk.Frame(steps, bg=BG)
            item.pack(side="left", padx=(0, 28))
            number_label = tk.Label(
                item, text=str(number), bg=GREEN_LIGHT, fg=GREEN,
                font=("Segoe UI", 9, "bold"), width=2, pady=3,
            )
            number_label.pack(side="left")
            title_label = self._label(item, title, 10, MUTED, "bold")
            title_label.pack(side="left", padx=(8, 0))
            if number == 1:
                item.configure(takefocus=True, highlightthickness=2,
                               highlightbackground=BG, highlightcolor=AMBER)
                for widget in (item, number_label, title_label):
                    widget.bind("<Button-1>", self._back_to_file)
                item.bind("<Return>", self._back_to_file)
                item.bind("<space>", self._back_to_file)
            self.phase_widgets.append((item, number_label, title_label))

        outer = tk.Frame(self.root, bg=BG, padx=34, pady=0)
        outer.pack(fill="both", expand=True)

        self.file_panel = tk.Frame(
            outer, bg=PANEL, padx=24, pady=24,
            highlightbackground=LINE, highlightthickness=1,
        )
        top = tk.Frame(self.file_panel, bg=PANEL)
        top.pack(fill="x")
        self._label(top, "Arquivo de matrículas", 12, INK, "bold").pack(side="left")
        self.file_label = self._label(
            self.file_panel, "Nenhum arquivo selecionado", 13, MUTED, "bold",
        )
        self.file_label.pack(fill="x", pady=(22, 4))
        self.file_detail = self._label(
            self.file_panel,
            "O arquivo precisa ter uma coluna Matrícula (com ou sem acento).",
            9, MUTED,
            justify="left",
        )
        self.file_detail.pack(fill="x")
        self.example_button = tk.Button(
            self.file_panel, text="Baixar CSV de exemplo", command=self._save_example,
            bg=PANEL, fg=GREEN, activebackground=PANEL,
            activeforeground="#1b563a", font=("Segoe UI", 9, "bold", "underline"),
            relief="flat", bd=0, cursor="hand2", padx=0, pady=0,
            highlightthickness=2, highlightbackground=PANEL,
            highlightcolor=AMBER, takefocus=True,
        )
        self.example_button.pack(anchor="w", pady=(14, 0))
        self.file_controls = tk.Frame(self.file_panel, bg=PANEL)
        self.file_controls.pack(fill="x", pady=(20, 0))
        self.choose_button = self._button(
            self.file_controls, "Escolher arquivo CSV", self._choose_csv,
            primary=True,
        )
        self.keep_file_button = self._button(
            self.file_controls, "Continuar com este CSV", self._continue_with_file,
            primary=True,
        )

        self.process_panel = tk.Frame(outer, bg=GREEN_LIGHT, padx=24, pady=24)
        self._label(
            self.process_panel, "Acesso ao SIGAA", 12, INK, "bold",
        ).pack(anchor="w")
        self.instruction = self._label(
            self.process_panel, "", 11, INK,
            justify="left",
        )
        self.instruction.pack(fill="x", pady=(10, 24))
        self.process_panel.bind(
            "<Configure>",
            lambda event: self.instruction.configure(
                wraplength=max(180, event.width - 52)
            ),
        )
        controls = tk.Frame(self.process_panel, bg=GREEN_LIGHT)
        controls.pack(fill="x")
        self.start_button = self._button(
            controls, "Abrir SIGAA e baixar", self._start, primary=True,
        )
        self.start_button.pack(side="right")
        self.start_button.configure(state="disabled")
        self.continue_button = self._button(
            controls, "Já escolhi o vínculo · Continuar", self._continue,
            primary=True,
        )
        self.stop_button = self._button(
            controls, "Interromper após esta matrícula", self._stop,
        )
        self.change_button = self._button(
            controls, "Voltar ao arquivo", self._back_to_file,
        )
        self.change_button.pack(side="left")

        self.results_panel = tk.Frame(
            outer, bg=PANEL, highlightbackground=LINE, highlightthickness=1,
        )
        results_head = tk.Frame(self.results_panel, bg=PANEL, padx=18, pady=13)
        results_head.pack(fill="x")
        self._label(results_head, "Acompanhamento", 12, INK, "bold").pack(side="left")
        self.counter = self._label(results_head, "0 de 0", 10, MUTED, "bold")
        self.counter.pack(side="right")
        self.results_stop_button = self._button(
            results_head, "Interromper", self._stop,
        )
        self.new_file_button = self._button(
            results_head, "Outro CSV", self._reset_file,
        )
        self.retry_button = self._button(
            results_head, "Tentar pendentes", self._start, primary=True,
        )
        self.result_message = self._label(
            self.results_panel, "", 10, MUTED, justify="left",
        )
        self.result_message.pack(fill="x", padx=18, pady=(0, 10))

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Boletins.Treeview", background=PANEL, fieldbackground=PANEL,
            foreground=INK, rowheight=34, font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Boletins.Treeview.Heading", background=BG,
            foreground=INK, font=("Segoe UI", 10, "bold"), relief="flat",
        )
        style.map("Boletins.Treeview", background=[("selected", GREEN_LIGHT)],
                  foreground=[("selected", INK)])
        table_frame = tk.Frame(self.results_panel, bg=PANEL)
        table_frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(
            table_frame, columns=("matricula", "resultado"), show="headings",
            style="Boletins.Treeview", selectmode="browse", height=6,
        )
        self.table.heading("matricula", text="Matrícula")
        self.table.heading("resultado", text="Resultado")
        self.table.column("matricula", width=220, stretch=False)
        self.table.column("resultado", width=520)
        self.table.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        scroll.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scroll.set)
        self.table.bind("<Double-1>", self._open_selected_pdf)
        self.table.bind("<Return>", self._open_selected_pdf)
        self.table.bind("<<TreeviewSelect>>", self._show_selected_detail)
        self.table.tag_configure(report.STATUS_SUCESSO, foreground=GREEN)
        self.table.tag_configure(report.STATUS_NAO_ENCONTRADA, foreground=AMBER)
        self.table.tag_configure(report.STATUS_ERRO, foreground=RED)

        detail_row = tk.Frame(self.results_panel, bg=PANEL, padx=18, pady=11)
        detail_row.pack(fill="x")
        self.detail_label = self._label(
            detail_row, "Selecione um PDF baixado para abri-lo.",
            9, MUTED, justify="left",
        )
        self.detail_label.pack(side="left", fill="x", expand=True)
        detail_row.bind(
            "<Configure>",
            lambda event: self.detail_label.configure(
                wraplength=max(160, event.width - 180)
            ),
        )
        self.open_pdf_button = self._button(
            detail_row, "Abrir PDF", self._open_selected_pdf, primary=True,
        )
        self.open_pdf_button.pack(side="right")
        self.open_pdf_button.configure(state="disabled")

        self.footer = tk.Frame(outer, bg=BG)
        style.configure(
            "Boletins.Horizontal.TProgressbar", background=GREEN,
            troughcolor=LINE, borderwidth=0, thickness=7,
        )
        self.progress = ttk.Progressbar(
            self.footer, mode="determinate", maximum=100,
            style="Boletins.Horizontal.TProgressbar",
        )
        self._button(
            self.footer, "Abrir pasta de PDFs", self._open_folder
        ).pack(side="left", padx=(0, 18))
        self.progress.pack(side="left", fill="x", expand=True)
        self._set_phase(0)

    def _set_phase(self, phase):
        self.phase = phase
        self.file_panel.pack_forget()
        self.process_panel.pack_forget()
        self.results_panel.pack_forget()
        self.footer.pack_forget()
        if phase == 0:
            self.file_panel.pack(fill="x", pady=(12, 0))
        elif phase == 1:
            self.process_panel.pack(fill="x", pady=(12, 0))
        else:
            self.results_panel.pack(fill="both", expand=True)
            self.footer.pack(fill="x", pady=(15, 0))
        has_file = bool(self.csv_path)
        self.choose_button.configure(
            text="Escolher outro CSV" if has_file else "Escolher arquivo CSV",
            bg=PANEL if has_file else GREEN,
            fg=GREEN if has_file else PANEL,
            activebackground=GREEN_LIGHT if has_file else "#1b563a",
            activeforeground=GREEN if has_file else PANEL,
            highlightbackground=LINE if has_file else GREEN,
        )
        self.choose_button.pack_forget()
        self.keep_file_button.pack_forget()
        self.choose_button.pack(side="left" if has_file else "right")
        if phase == 0 and has_file:
            self.keep_file_button.pack(side="right")
        for index, (item, number_label, title_label) in enumerate(self.phase_widgets):
            active = index == phase
            done = index < phase
            can_go_back = index == 0 and phase in (1, 2) and not self.running
            number_label.configure(
                bg=GREEN if active else GREEN_LIGHT if done else BG,
                fg=PANEL if active else GREEN if done else MUTED,
                cursor="hand2" if can_go_back else "arrow",
            )
            title_label.configure(
                fg=GREEN if can_go_back else INK if active else MUTED,
                cursor="hand2" if can_go_back else "arrow",
                font=("Segoe UI", 10, "bold", "underline") if can_go_back
                else ("Segoe UI", 10, "bold"),
            )
            item.configure(cursor="hand2" if can_go_back else "arrow")

    def _back_to_file(self, _event=None):
        if self.phase in (1, 2) and not self.running:
            self._set_phase(0)

    def _continue_with_file(self):
        if self.phase == 0 and self.csv_path and not self.running:
            self._set_phase(1)

    def _save_example(self):
        downloads = Path.home() / "Downloads"
        path = filedialog.asksaveasfilename(
            title="Baixar CSV de exemplo",
            initialdir=downloads if downloads.is_dir() else ROOT,
            initialfile="exemplo_matriculas.csv",
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(["Matrícula"])
                writer.writerow(["123456"])
                writer.writerow(["789012"])
        except OSError as exc:
            messagebox.showerror("Erro ao salvar CSV", str(exc))
            return
        messagebox.showinfo("CSV de exemplo", f"Arquivo salvo em:\n{path}")

    def _show_about(self):
        if self.about_window and self.about_window.winfo_exists():
            self.about_window.lift()
            self.about_window.focus_force()
            return
        window = tk.Toplevel(self.root)
        self.about_window = window
        window.title("Sobre · Boletins SIGAA")
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - 510) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - 300) // 2
        window.geometry(f"510x300+{x}+{y}")
        window.minsize(460, 280)
        window.configure(bg=PANEL)
        window.transient(self.root)
        window.grab_set()
        window.lift()
        heading = tk.Frame(window, bg=INK, padx=28, pady=18)
        heading.pack(fill="x")
        self._label(heading, "Sobre", 18, PANEL, "bold").pack(anchor="w")
        body = tk.Frame(window, bg=PANEL, padx=28, pady=24)
        body.pack(fill="both", expand=True)
        description = self._label(
            body,
            "Ferramenta criada como complemento para auxiliar a impressão em "
            "lote de boletins no SIGAA IFFar.",
            11, INK, justify="left", wraplength=440,
        )
        description.pack(fill="x")
        self._label(
            body, "Autores: Prof. Daniel Temp e Profa. Jaline Mombach",
            10, INK, wraplength=440,
        ).pack(fill="x", pady=(22, 3))
        self._label(body, "IFFar Campus Alegrete", 10, MUTED).pack(fill="x")
        self._button(body, "Fechar", window.destroy).pack(anchor="e", pady=(22, 0))

    def _choose_csv(self):
        if self.running:
            return
        path = filedialog.askopenfilename(
            title="Escolher arquivo de matrículas", initialdir=ROOT,
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            matriculas, duplicadas, invalidas = input_csv.carregar_matriculas(path)
        except (input_csv.ErroCSV, OSError, UnicodeError) as exc:
            messagebox.showerror("CSV inválido", str(exc))
            return
        self.csv_path = Path(path)
        self.matriculas = matriculas
        self.details = {}
        self.file_label.configure(text=self.csv_path.name, fg=INK)
        details = [f"{len(matriculas)} matrícula(s) válida(s)"]
        if duplicadas:
            details.append(f"{len(duplicadas)} duplicada(s) ignorada(s)")
        if invalidas:
            details.append(f"{len(invalidas)} inválida(s) ignorada(s)")
        self.file_detail.configure(text=" · ".join(details), fg=MUTED)
        self.instruction.configure(
            text=(
                "Abra o SIGAA. Faça o login no navegador e escolha seu vínculo "
                "quando solicitado."
            ),
            fg=INK,
        )
        self._set_phase(1)
        self.start_button.configure(state="normal")
        self.progress["value"] = 0
        self.counter.configure(text=f"0 de {len(matriculas)}")
        self.open_pdf_button.configure(state="disabled")
        self.table.delete(*self.table.get_children())
        for matricula in matriculas:
            self.table.insert("", "end", iid=matricula,
                              values=(matricula, STATUS_LABELS[None]))

    def _reset_file(self):
        if self.running:
            return
        self.csv_path = None
        self.matriculas = []
        self.details = {}
        self.retry_available = False
        self.file_label.configure(text="Nenhum arquivo selecionado", fg=MUTED)
        self.file_detail.configure(
            text="O arquivo precisa ter uma coluna Matrícula (com ou sem acento).",
            fg=MUTED,
        )
        self.start_button.configure(state="disabled")
        self.table.delete(*self.table.get_children())
        self.counter.configure(text="0 de 0")
        self.progress["value"] = 0
        self.open_pdf_button.configure(state="disabled")
        self.new_file_button.pack_forget()
        self.retry_button.pack_forget()
        self._set_phase(0)

    def _start(self):
        if self.running or not self.csv_path:
            return
        self.running = True
        self.retry_available = False
        self.stop_event.clear()
        self.continue_event.clear()
        self.stop_button.configure(state="normal")
        self.results_stop_button.configure(state="normal")
        self.start_button.pack_forget()
        self.choose_button.configure(state="disabled")
        self.change_button.configure(state="disabled")
        self.change_button.pack_forget()
        self.new_file_button.pack_forget()
        self.retry_button.pack_forget()
        self.stop_button.pack(side="left")
        self.instruction.configure(text="Abrindo o navegador do SIGAA...", fg=INK)
        self._set_phase(1)
        threading.Thread(
            target=self._worker, args=(self.csv_path,), daemon=True,
        ).start()

    def _worker(self, csv_path):
        def on_event(kind, **data):
            self.events.put((kind, data))

        def wait_for_link():
            self.events.put(("aguardando_vinculo", {}))
            self.continue_event.wait()
            if self.stop_event.is_set():
                raise ExecucaoInterrompida()
            self.continue_event.clear()

        try:
            executar(
                csv_path, pasta=OUTPUT_DIR, perfil=PROFILE_DIR,
                on_event=on_event, wait_for_link=wait_for_link,
                should_stop=self.stop_event.is_set,
            )
        except ExecucaoInterrompida:
            self.events.put(("interrompido", {}))
        except input_csv.ErroCSV as exc:
            self.events.put(("falha", {
                "mensagem": "Não foi possível ler o CSV. Escolha o arquivo novamente.",
                "detalhe": str(exc),
            }))
        except ErroLogin as exc:
            self.events.put(("falha", {
                "mensagem": (
                    "Não foi possível acessar os boletins. Confira o login e o "
                    "vínculo no navegador e tente novamente."
                ),
                "detalhe": str(exc),
            }))
        except ErroNavegacao as exc:
            self.events.put(("falha", {
                "mensagem": (
                    "O SIGAA não abriu a tela esperada. Tente novamente; as "
                    "matrículas concluídas serão mantidas."
                ),
                "detalhe": str(exc),
            }))
        except Exception as exc:
            self.events.put(("falha", {
                "mensagem": (
                    "Não foi possível concluir o lote. Tente novamente; as "
                    "matrículas concluídas serão mantidas."
                ),
                "detalhe": str(exc),
            }))
        finally:
            self.events.put(("fim_worker", {}))

    def _drain_events(self):
        if self.closed:
            return
        try:
            while True:
                kind, data = self.events.get_nowait()
                self._handle_event(kind, data)
        except queue.Empty:
            pass
        if not self.closed:
            self.root.after(100, self._drain_events)

    def _handle_event(self, kind, data):
        if kind == "inicializado":
            self.processed = len(data["matriculas"]) - len(data["pendentes"])
            for matricula, status in data["status"].items():
                if self.table.exists(matricula):
                    self.table.set(matricula, "resultado",
                                   STATUS_LABELS.get(status, "Aguardando"))
                    self.table.item(matricula, tags=(status,) if status else ())
            self._update_progress()
            self._show_selected_detail(None)
        elif kind == "orientacao":
            if self.phase == 2:
                self.result_message.configure(text=data["mensagem"], fg=INK)
            else:
                self.instruction.configure(text=data["mensagem"], fg=INK)
        elif kind == "aguardando_vinculo":
            self._set_phase(1)
            self.instruction.configure(
                text=(
                    "No navegador, escolha o vínculo. Volte a esta janela e "
                    "clique em Continuar."
                ),
                fg=GREEN,
            )
            self.continue_button.pack(side="right")
        elif kind == "iniciando":
            self._set_phase(2)
            self.results_stop_button.pack(side="left", padx=(14, 0))
            self.continue_button.pack_forget()
            self.result_message.configure(
                text=f"Buscando boletim da matrícula {data['matricula']}...", fg=INK,
            )
            if self.table.exists(data["matricula"]):
                self.table.set(data["matricula"], "resultado", "Processando...")
                self.table.see(data["matricula"])
        elif kind == "tentativa":
            self.result_message.configure(
                text=f"Matrícula {data['matricula']}: tentativa "
                     f"{data['tentativa']} falhou. Tentando novamente...",
                fg=AMBER,
            )
        elif kind == "resultado":
            self.processed += 1
            if data["detalhe"]:
                self.details[data["matricula"]] = data["detalhe"]
            else:
                self.details.pop(data["matricula"], None)
            self.table.set(data["matricula"], "resultado",
                           STATUS_LABELS.get(data["status"], data["status"]))
            self.table.item(data["matricula"], tags=(data["status"],))
            self._update_progress()
            self._show_selected_detail(None)
        elif kind == "concluido":
            self._set_phase(2)
            resumo = data["resumo"]
            self.retry_available = bool(resumo["erro"])
            self.result_message.configure(
                text=f"Concluído: {resumo['sucesso']} PDF(s), "
                     f"{resumo['nao_encontrada']} não encontrada(s), "
                     f"{resumo['erro']} erro(s).",
                fg=GREEN if not resumo["erro"] else AMBER,
            )
        elif kind == "interrompido":
            self.retry_available = True
            message = (
                "Execução interrompida. Ao iniciar novamente, os PDFs já "
                "concluídos serão mantidos."
            )
            target = self.result_message if self.phase == 2 else self.instruction
            target.configure(
                text=message,
                fg=AMBER,
            )
        elif kind == "falha":
            self.retry_available = True
            target = self.result_message if self.phase == 2 else self.instruction
            target.configure(text=f"Erro: {data['mensagem']}", fg=RED)
            self.detail_label.configure(text=data["detalhe"], fg=MUTED)
            messagebox.showerror("Falha na execução", data["mensagem"])
        elif kind == "fim_worker":
            self.running = False
            self._set_phase(self.phase)
            self.continue_button.pack_forget()
            self.stop_button.pack_forget()
            self.results_stop_button.pack_forget()
            self.start_button.pack(side="right")
            self.start_button.configure(state="normal")
            self.choose_button.configure(state="normal")
            self.change_button.configure(state="normal")
            self.change_button.pack(side="left")
            if self.phase == 2:
                self.new_file_button.pack(side="left", padx=(14, 0))
                if self.retry_available:
                    self.retry_button.pack(side="right", padx=(0, 12))
            if self.close_when_done:
                self.closed = True
                self.root.destroy()

    def _update_progress(self):
        total = len(self.matriculas)
        self.counter.configure(text=f"{self.processed} de {total}")
        self.progress["value"] = 100 * self.processed / total if total else 0

    def _continue(self):
        self.continue_button.pack_forget()
        self.continue_event.set()

    def _stop(self):
        self.stop_event.set()
        self.continue_event.set()
        self.stop_button.configure(state="disabled")
        self.results_stop_button.configure(state="disabled")
        target = self.result_message if self.phase == 2 else self.instruction
        target.configure(text="Interrompendo após a operação atual...", fg=AMBER)

    def _close(self):
        if self.running:
            self.close_when_done = True
            self._stop()
        else:
            self.closed = True
            self.root.destroy()

    def _open_folder(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(OUTPUT_DIR)

    def _open_selected_pdf(self, _event=None):
        selected = self.table.selection()
        if not selected:
            return
        path = OUTPUT_DIR / f"{selected[0]}.pdf"
        completed = (
            self.table.set(selected[0], "resultado")
            == STATUS_LABELS[report.STATUS_SUCESSO]
        )
        if completed and path.exists():
            os.startfile(path)
        else:
            self.detail_label.configure(
                text=(
                    "O PDF desta matrícula não está disponível. "
                    "Execute o lote novamente."
                ),
                fg=AMBER,
            )

    def _show_selected_detail(self, _event):
        selected = self.table.selection()
        available = bool(
            selected
            and self.table.set(selected[0], "resultado")
            == STATUS_LABELS[report.STATUS_SUCESSO]
            and (OUTPUT_DIR / f"{selected[0]}.pdf").exists()
        )
        self.open_pdf_button.configure(state="normal" if available else "disabled")
        if selected and selected[0] in self.details:
            self.detail_label.configure(text=self.details[selected[0]], fg=RED)
        elif (
            selected
            and self.table.set(selected[0], "resultado")
            == STATUS_LABELS[report.STATUS_NAO_ENCONTRADA]
        ):
            self.detail_label.configure(
                text="Nenhum boletim foi encontrado para esta matrícula.", fg=AMBER,
            )
        else:
            self.detail_label.configure(
                text="Selecione um PDF baixado para abri-lo.", fg=MUTED,
            )


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
