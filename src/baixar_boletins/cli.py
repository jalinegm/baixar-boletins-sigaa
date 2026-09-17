import argparse
import random
import sys
import time
from pathlib import Path

from . import input_csv, report
from .pdf_render import gerar_pdf
from .sigaa_nav import ErroLogin, ErroNavegacao, NaoEncontrada, SigaaSessao

URL_PADRAO = "https://sig.iffarroupilha.edu.br/sigaa/verMenuTecnicoIntegrado.do"
PERFIL_PADRAO = "./.perfil-sigaa"
PASTA_PADRAO = "boletins"
MAX_TENTATIVAS = 3


def _parser():
    parser = argparse.ArgumentParser(
        description="Emissão em lote de boletins do SIGAA IFFar"
    )
    parser.add_argument("csv", help="Caminho do arquivo CSV com a coluna 'Matricula'")
    parser.add_argument("--pasta", default=PASTA_PADRAO, help="Pasta de saída dos PDFs")
    parser.add_argument("--url", default=URL_PADRAO, help="URL base do SIGAA")
    parser.add_argument(
        "--reprocessar", action="store_true", help="Reprocessa matrículas já concluídas"
    )
    parser.add_argument(
        "--perfil",
        default=PERFIL_PADRAO,
        help="Diretório do perfil persistente do navegador",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)

    try:
        matriculas, duplicadas, invalidas = input_csv.carregar_matriculas(args.csv)
    except input_csv.ErroCSV as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if duplicadas:
        print(f"Aviso: {len(duplicadas)} matrícula(s) duplicada(s) ignorada(s).")
    if invalidas:
        print(f"Aviso: {len(invalidas)} matrícula(s) inválida(s): {', '.join(invalidas)}")

    pasta = Path(args.pasta)
    pasta.mkdir(parents=True, exist_ok=True)

    progresso = report.Progresso(pasta / ".progresso.json").carregar()
    pendentes = progresso.pendentes(matriculas, args.reprocessar)

    if not pendentes:
        _imprimir_resumo(progresso, pasta, matriculas)
        return 0

    sessao = SigaaSessao(args.url, args.perfil)
    try:
        sessao.abrir()
        sessao.abrir_busca()
    except ErroLogin as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sessao.fechar()
        return 3
    except ErroNavegacao as exc:
        print(f"Erro de navegação: {exc}", file=sys.stderr)
        sessao.fechar()
        return 2

    for matricula in pendentes:
        status = report.STATUS_ERRO
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
                print(
                    f"  [{matricula}] tentativa {tentativa}/{MAX_TENTATIVAS} falhou: {exc}",
                    file=sys.stderr,
                )
                if tentativa < MAX_TENTATIVAS:
                    time.sleep(2)
                    try:
                        sessao.abrir_busca()
                    except Exception as exc_nav:
                        print(f"  [{matricula}] falha ao reabrir busca: {exc_nav}", file=sys.stderr)

        progresso.definir(matricula, status)
        print(f"  [{matricula}] -> {status}")
        time.sleep(random.uniform(1.0, 2.0))

    sessao.fechar()
    _imprimir_resumo(progresso, pasta, matriculas)
    return 0


def _imprimir_resumo(progresso, pasta, matriculas):
    resumo = progresso.resumo()
    nao_encontradas = [
        m for m in matriculas if progresso.status(m) == report.STATUS_NAO_ENCONTRADA
    ]
    erros = [m for m in matriculas if progresso.status(m) == report.STATUS_ERRO]

    print()
    print("Resumo da execução:")
    print(f"  Total processado: {resumo['total']}")
    print(f"  PDFs gerados: {resumo['sucesso']}")
    print(f"  Não encontradas: {resumo['nao_encontrada']}")
    print(f"  Erros: {resumo['erro']}")
    print(f"  Pasta de saída: {pasta.resolve()}")
    if nao_encontradas:
        print(f"  Matrículas não encontradas: {', '.join(nao_encontradas)}")
    if erros:
        print(f"  Matrículas com erro: {', '.join(erros)}")


if __name__ == "__main__":
    sys.exit(main())
