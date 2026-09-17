import json
from pathlib import Path

STATUS_PENDENTE = "pendente"
STATUS_SUCESSO = "sucesso"
STATUS_NAO_ENCONTRADA = "nao_encontrada"
STATUS_ERRO = "erro"
STATUS_INVALIDA = "invalida"

FINALIZADOS = {STATUS_SUCESSO, STATUS_NAO_ENCONTRADA, STATUS_INVALIDA}
RETOMAVEIS = {STATUS_PENDENTE, STATUS_ERRO}


class Progresso:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.dados = {}

    def carregar(self):
        if self.caminho.exists():
            with open(self.caminho, "r", encoding="utf-8") as arquivo:
                self.dados = json.load(arquivo)
        return self

    def salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            json.dump(self.dados, arquivo, ensure_ascii=False, indent=2)

    def status(self, matricula):
        return self.dados.get(matricula)

    def definir(self, matricula, status):
        self.dados[matricula] = status
        self.salvar()

    def pendentes(self, matriculas, reprocessar):
        if reprocessar:
            return list(matriculas)
        return [m for m in matriculas if self.status(m) not in FINALIZADOS]

    def resumo(self):
        sucesso = sum(1 for s in self.dados.values() if s == STATUS_SUCESSO)
        nao_encontrada = sum(1 for s in self.dados.values() if s == STATUS_NAO_ENCONTRADA)
        erro = sum(1 for s in self.dados.values() if s == STATUS_ERRO)
        invalida = sum(1 for s in self.dados.values() if s == STATUS_INVALIDA)
        return {
            "total": len(self.dados),
            "sucesso": sucesso,
            "nao_encontrada": nao_encontrada,
            "erro": erro,
            "invalida": invalida,
        }
