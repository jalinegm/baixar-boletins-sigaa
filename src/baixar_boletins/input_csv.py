import csv
import unicodedata
from pathlib import Path


class ErroCSV(Exception):
    pass


def carregar_matriculas(caminho):
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroCSV(f"Arquivo CSV não encontrado: {caminho}")

    with open(caminho, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if leitor.fieldnames is None:
            raise ErroCSV("CSV vazio (sem cabeçalho)")

        coluna = _localizar_coluna(leitor.fieldnames)
        if coluna is None:
            raise ErroCSV("CSV sem a coluna 'Matrícula' (com ou sem acento)")

        matriculas = []
        duplicadas = []
        invalidas = []
        vistos = set()

        for linha in leitor:
            valor = (linha.get(coluna) or "").strip()
            if not valor:
                continue
            if not valor.isdigit():
                invalidas.append(valor)
                continue
            if valor in vistos:
                duplicadas.append(valor)
            else:
                vistos.add(valor)
                matriculas.append(valor)

    if not matriculas:
        raise ErroCSV("CSV sem matrículas válidas")

    return matriculas, duplicadas, invalidas


def _localizar_coluna(nomes):
    for nome in nomes:
        if not nome:
            continue
        normalized = unicodedata.normalize("NFKD", nome.strip()).casefold()
        normalized = "".join(
            character for character in normalized
            if not unicodedata.combining(character)
        )
        if normalized == "matricula":
            return nome
    return None
