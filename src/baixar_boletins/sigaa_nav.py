"""Navegação no SIGAA IFFar (JSF stateful).

Fluxo mapeado no sistema real (set/2026):

- menu.jsf > link com texto "Emitir Boletim" (id varia por perfil; no Gestor Geral é
  ``menuTecnicoForm:emitirBoletimTecnicoGestorGeral``)
  -> tela "Buscar Discente" (form ``formulario``, postback em busca_discente.jsf).
- Busca: ``formulario:checkMatricula`` + ``formulario:matriculaDiscente`` + ``formulario:buscar``.
- Resultado: tabela com ``input[type=image]#form:selecionarDiscente`` por linha;
  sem resultado -> ``#painel-erros`` ("Não foram encontrados discentes...").
- Selecionar abre o "Boletim Escolar" NA MESMA ABA (sem popup). O link "Voltar" do
  boletim é ``history.back()``, que retorna à tela de busca utilizável.
- Aluno com mais de um ano escolar (ex.: reprovado e rematriculado): Selecionar abre
  antes a tabela "Anos Escolares" (boletim/selecao.jsf), com um link
  "Selecionar Ano Escolar" por linha. Escolhe-se o ano atual do cabeçalho do SIGAA.
"""

import re
from datetime import date
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# O link "Emitir Boletim" muda de id conforme o perfil (Gestor Geral:
# menuTecnicoForm:emitirBoletimTecnicoGestorGeral; Coordenação: outro id/form).
# Por isso ele é localizado pelo texto; o id do Gestor Geral só desempata.
TEXTO_LINK_BOLETIM = re.compile(r"^\s*Emitir\s+Boletim\s*$", re.I)
ID_PREFERIDO_BOLETIM = "emitirBoletimTecnicoGestorGeral"
SEL_CHECK_MATRICULA = "[id$=':checkMatricula']"
SEL_CAMPO_MATRICULA = "[id$=':matriculaDiscente']"
SEL_BOTAO_BUSCAR = "[id$=':buscar']"
SEL_SELECIONAR = "input[id$=':selecionarDiscente'], input[type='image'][title*='Selecionar']"
SEL_ERROS = "#painel-erros"
SEL_SENHA = "input[type='password']"
URL_VINCULOS = "vinculos.jsf"

TEXTO_BOLETIM = "Boletim Escolar"
TEXTO_ANOS_ESCOLARES = "Anos Escolares"
SEL_LINHAS_ANOS = "table.listagem:has(caption:text-is('Anos Escolares')) tbody tr"
SEL_SELECIONAR_ANO = "a:has(img[title='Selecionar Ano Escolar'])"
RE_ANO_ATUAL = re.compile(r"Ano\s+Atual:\s*(\d{4})")
RE_ANO_LINHA = re.compile(r"^\s*(\d{4})")
TEXTO_INESPERADO = re.compile(r"Comportamento\s+Inesperado", re.I)

TIMEOUT_PAGINA = 30000
TEMPO_LOGIN_S = 600


class NaoEncontrada(Exception):
    pass


class ErroNavegacao(Exception):
    pass


class ErroLogin(ErroNavegacao):
    pass


class SigaaSessao:
    def __init__(self, url, perfil, pasta_debug="debug"):
        self.url = url
        self.perfil = perfil
        self.pasta_debug = Path(pasta_debug)
        self._pw = None
        self.context = None
        self.page = None
        self._voltas_extras = 0

    def abrir(self):
        self._pw = sync_playwright().start()
        self.context = self._pw.chromium.launch_persistent_context(
            self.perfil, headless=False
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_PAGINA)

    def fechar(self):
        if self.context:
            self.context.close()
        if self._pw:
            self._pw.stop()

    # ------------------------------------------------------------------ login/menu

    def _links_boletim(self):
        return self.page.locator("a").filter(has_text=TEXTO_LINK_BOLETIM)

    def _no_menu(self):
        return self._links_boletim().count() > 0

    def _link_boletim(self):
        """Escolhe o link "Emitir Boletim" a clicar, independente do perfil."""
        links = self._links_boletim()
        visiveis = [links.nth(i) for i in range(links.count()) if links.nth(i).is_visible()]
        candidatos = visiveis or [links.nth(i) for i in range(links.count())]
        for link in candidatos:
            if ID_PREFERIDO_BOLETIM in (link.get_attribute("id") or ""):
                return link
        return candidatos[0]

    def _na_tela_login(self):
        return self.page.locator(SEL_SENHA).count() > 0

    def _na_tela_vinculos(self):
        return URL_VINCULOS in self.page.url

    def abrir_busca(self):
        """Garante login e deixa a página na tela "Buscar Discente"."""
        # A URL deve ser a action de entrada do módulo (verMenuTecnicoIntegrado.do):
        # ela inicializa o contexto "Ensino Técnico" na sessão. Abrir menu.jsf direto
        # desenha o menu, mas o clique em "Emitir Boletim" cai em "Comportamento Inesperado".
        self.page.goto(self.url, wait_until="domcontentloaded")
        avisou = False
        avisou_vinculo = False
        reentradas = 0
        for _ in range(TEMPO_LOGIN_S // 2):
            self.page.wait_for_load_state("domcontentloaded")
            if self._no_menu():
                break
            if self._na_tela_login():
                if not avisou:
                    print("Faça login no SIGAA na janela do navegador aberta...")
                    avisou = True
                self.page.wait_for_timeout(2000)
                continue
            if self._na_tela_vinculos():
                if not avisou_vinculo:
                    print("Escolha o vínculo/perfil na janela do navegador e pressione Enter para continuar...")
                    input()
                    avisou_vinculo = True
                continue
            # Logado, mas em outra página (portal, aviso, erro): reentra no módulo.
            self.page.wait_for_timeout(2000)
            if self._na_tela_login() or self._no_menu():
                continue
            if reentradas < 5:
                reentradas += 1
                self.page.goto(self.url, wait_until="domcontentloaded")
            elif reentradas == 5:
                reentradas += 1
                self.salvar_debug("entrada_modulo")
                print("Abra manualmente o módulo 'Ensino Técnico Integrado' na janela...")
        else:
            self.salvar_debug("menu_sem_emitir_boletim")
            raise ErroLogin("Link 'Emitir Boletim' não encontrado dentro do tempo limite.")

        link = self._link_boletim()
        with self.page.expect_navigation(wait_until="domcontentloaded"):
            if link.is_visible():
                link.click()
            else:
                # Link em aba oculta do menu: dispara o onclick do JSF direto.
                link.evaluate("el => el.click()")
        try:
            self.page.wait_for_selector(SEL_CAMPO_MATRICULA)
        except PlaywrightTimeoutError as exc:
            self.salvar_debug("abrir_busca")
            raise ErroNavegacao("Tela 'Buscar Discente' não abriu.") from exc

    # ------------------------------------------------------------------ por aluno

    def _checar_inesperado(self, etapa):
        if TEXTO_INESPERADO.search(self.page.content()):
            self.salvar_debug(etapa)
            raise ErroNavegacao("SIGAA exibiu 'Comportamento Inesperado'.")

    def abrir_boletim(self, matricula):
        """Da tela de busca, abre o boletim do aluno na mesma aba."""
        self._voltas_extras = 0
        if self.page.locator(SEL_CAMPO_MATRICULA).count() == 0:
            self.abrir_busca()

        check = self.page.locator(SEL_CHECK_MATRICULA)
        if not check.is_checked():
            check.check()
        self.page.locator(SEL_CAMPO_MATRICULA).fill(matricula)

        with self.page.expect_navigation(wait_until="domcontentloaded"):
            self.page.locator(SEL_BOTAO_BUSCAR).click()
        self._checar_inesperado(f"busca_{matricula}")

        linha = self.page.locator(f"tr:has(> td:text-is('{matricula}'))")
        botao = linha.locator(SEL_SELECIONAR)
        if botao.count() == 0:
            if self.page.locator(SEL_ERROS).count() > 0:
                raise NaoEncontrada(matricula)
            self.salvar_debug(f"busca_{matricula}")
            raise NaoEncontrada(matricula)

        with self.page.expect_navigation(wait_until="load"):
            botao.first.click()
        self._checar_inesperado(f"boletim_{matricula}")
        if self.page.locator(SEL_LINHAS_ANOS).count() > 0:
            self._selecionar_ano_escolar(matricula)
        corpo = self.page.inner_text("body")
        if TEXTO_BOLETIM not in corpo or matricula not in corpo:
            self.salvar_debug(f"boletim_{matricula}")
            raise ErroNavegacao(f"Boletim de {matricula} não carregou.")
        return self.page

    def _ano_atual(self):
        encontrado = RE_ANO_ATUAL.search(self.page.inner_text("body"))
        return int(encontrado.group(1)) if encontrado else date.today().year

    def _selecionar_ano_escolar(self, matricula):
        """Na tela "Anos Escolares", abre o boletim do ano atual (ou o mais recente)."""
        linhas = self.page.locator(SEL_LINHAS_ANOS)
        anos = {}
        for i in range(linhas.count()):
            linha = linhas.nth(i)
            ano = RE_ANO_LINHA.match(linha.locator("td").first.inner_text())
            if ano and linha.locator(SEL_SELECIONAR_ANO).count() > 0:
                anos[int(ano.group(1))] = linha
        if not anos:
            self.salvar_debug(f"anos_{matricula}")
            raise ErroNavegacao(f"Nenhum ano escolar selecionável para {matricula}.")

        ano_atual = self._ano_atual()
        escolhido = ano_atual if ano_atual in anos else max(anos)
        if escolhido != ano_atual:
            print(f"  [{matricula}] ano {ano_atual} não encontrado; usando {escolhido}.")
        with self.page.expect_navigation(wait_until="load"):
            anos[escolhido].locator(SEL_SELECIONAR_ANO).first.click()
        self._checar_inesperado(f"boletim_{matricula}")
        self._voltas_extras = 1

    def voltar_para_busca(self):
        """Equivale ao link 'Voltar' do boletim (history.back)."""
        # Se passou pela tela "Anos Escolares", é preciso voltar uma página a mais.
        voltas = 1 + self._voltas_extras
        self._voltas_extras = 0
        try:
            for _ in range(voltas):
                self.page.go_back(wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            pass
        if self.page.locator(SEL_CAMPO_MATRICULA).count() == 0:
            self.abrir_busca()

    # ------------------------------------------------------------------ debug

    def salvar_debug(self, etapa):
        try:
            self.pasta_debug.mkdir(parents=True, exist_ok=True)
            base = self.pasta_debug / etapa
            self.page.screenshot(path=f"{base}.png", full_page=True)
            Path(f"{base}.html").write_text(self.page.content(), encoding="utf-8")
            print(f"  (debug salvo em {base}.png/.html)")
        except Exception:
            pass
