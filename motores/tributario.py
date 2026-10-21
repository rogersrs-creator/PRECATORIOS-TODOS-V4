"""
Precatórios de natureza TRIBUTÁRIA (Subnacional e Nacional, todas as propostas).

Regra (conferida com os cálculos homologados de tributários):
  - SELIC simples SOMENTE sobre o valor principal, da data-base do cálculo até cada pagamento
    e até a data final;
  - o valor da SELIC é lançado no campo Selic (DESTINO_SELIC); os juros informados não mudam;
  - não há período de graça nem troca de índice: a mesma regra vale antes e depois das
    EC 113/2021 e 136/2025;
  - a data-base do cálculo é a do próprio precatório (pode ser anterior à data-base da proposta);
    por padrão, é a data-base da proposta.
Pagamentos: abatimento proporcional ao peso de principal, juros e Selic (esteira comum).

Observação: como a SELIC incide só sobre o principal, o total e o saldo são os mesmos lançando a
SELIC no campo Selic ou no campo Juros. Para lançar nos juros, troque DESTINO_SELIC para "juros".
"""
from motores.base import Regra, var_selic

DESTINO_SELIC = "selic"     # "selic" (campo Selic) ou "juros"


class RegraTributario(Regra):
    natureza = "Tributário"
    nome = "Tributário"
    ano_ini, ano_fim = 1900, 2099      # todas as propostas cadastradas na planilha GRACA
    usa_selic = True                   # relatório com o campo Selic
    selic_obrigatorio = False          # o campo Selic inicial é opcional (padrão 0,00)
    data_base_propria = True           # o usuário informa a data-base do cálculo
    compara_selic = False              # V5: sem comparação IPCA × SELIC (já é SELIC)
    modelo_descricao = ("SELIC simples só sobre o principal, da data-base do cálculo até o pagamento, "
                        "lançada no campo Selic. Juros não mudam. Sem período de graça.")

    def __init__(self, esfera):
        self.esfera = esfera

    def atualizar_psj(self, p, j, s, d_ini, d_fim, graca, bases):
        correcao = p * var_selic(bases, d_ini, d_fim)
        if DESTINO_SELIC == "juros":
            return p, j + correcao, s
        return p, j, s + correcao

    def atualizar(self, p, j, d_ini, d_fim, graca, bases):
        return p, j + p * var_selic(bases, d_ini, d_fim)

    def classificar(self, data_ref, last_date, graca, bases):
        return "SELIC (tributário)", var_selic(bases, last_date, data_ref), 0.0


REGRAS = {
    "Subnacional": RegraTributario("Subnacional"),
    "Nacional": RegraTributario("Nacional"),
}
