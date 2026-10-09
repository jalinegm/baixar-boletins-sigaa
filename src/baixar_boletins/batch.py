import random
import time
from pathlib import Path

from . import input_csv, report
from .pdf_render import gerar_pdf
from .sigaa_nav import NaoEncontrada, SigaaSessao

URL_PADRAO = "https://sig.iffarroupilha.edu.br/sigaa/verMenuTecnicoIntegrado.do"
PERFIL_PADRAO = "./.perfil-sigaa"
PASTA_PADRAO = "boletins"
MAX_TENTATIVAS = 3


class ExecucaoInterrompida(Exception):
    pass


def executar(csv_path, pasta=PASTA_PADRAO, url=URL_PADRAO,
             perfil=PERFIL_PADRAO, reprocessar=False, on_event=None,
             wait_for_link=None, should_stop=None):
    def emitir(kind, **data):
        if on_event:
            on_event(kind, **data)

    def conferir_parada():
        if should_stop and should_stop():
            raise ExecucaoInterrompida()

    matriculas, duplicadas, invalidas = input_csv.carregar_matriculas(csv_path)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    progresso = report.Progresso(pasta / ".progresso.json").carregar()
    pendentes = progresso.pendentes(matriculas, reprocessar)
    emitir(
        "inicializado", matriculas=matriculas, duplicadas=duplicadas,
        invalidas=invalidas, pendentes=pendentes, pasta=pasta,
        status={m: progresso.status(m) for m in matriculas},
    )

    if pendentes:
        def informar(mensagem):
            emitir("orientacao", mensagem=mensagem)

        sessao = SigaaSessao(
            url, perfil, on_status=informar, wait_for_link=wait_for_link,
            check_stop=conferir_parada,
        )
        try:
            conferir_parada()
            emitir("orientacao", mensagem="Abrindo o navegador do SIGAA...")
            sessao.abrir()
            sessao.abrir_busca()
            conferir_parada()

            for matricula in pendentes:
                conferir_parada()
                emitir("iniciando", matricula=matricula)
                status = report.STATUS_ERRO
                detalhe = ""
                for tentativa in range(1, MAX_TENTATIVAS + 1):
                    try:
                        pagina = sessao.abrir_boletim(matricula)
                        gerar_pdf(pagina, pasta / f"{matricula}.pdf")
                        sessao.voltar_para_busca()
                        status = report.STATUS_SUCESSO
                        break
                    except NaoEncontrada:
                        status = report.STATUS_NAO_ENCONTRADA
                        break
                    except Exception as exc:
                        detalhe = str(exc)
                        emitir(
                            "tentativa", matricula=matricula,
                            tentativa=tentativa, detalhe=detalhe,
                        )
                        if tentativa < MAX_TENTATIVAS:
                            time.sleep(2)
                            try:
                                sessao.abrir_busca()
                            except Exception as nav_exc:
                                emitir(
                                    "tentativa", matricula=matricula,
                                    tentativa=tentativa,
                                    detalhe=f"Falha ao reabrir busca: {nav_exc}",
                                )

                progresso.definir(matricula, status)
                emitir("resultado", matricula=matricula, status=status,
                       detalhe=detalhe if status == report.STATUS_ERRO else "")
                time.sleep(random.uniform(1.0, 2.0))
        finally:
            sessao.fechar()

    resumo = {
        "total": len(matriculas),
        "sucesso": sum(progresso.status(m) == report.STATUS_SUCESSO for m in matriculas),
        "nao_encontrada": sum(
            progresso.status(m) == report.STATUS_NAO_ENCONTRADA for m in matriculas
        ),
        "erro": sum(progresso.status(m) == report.STATUS_ERRO for m in matriculas),
        "pasta": pasta.resolve(),
        "nao_encontradas": [
            m for m in matriculas if progresso.status(m) == report.STATUS_NAO_ENCONTRADA
        ],
        "erros": [m for m in matriculas if progresso.status(m) == report.STATUS_ERRO],
    }
    emitir("concluido", resumo=resumo)
    return resumo
