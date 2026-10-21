"""
Registro de regimes de cálculo.

O app escolhe o motor por (esfera, ano da proposta). Para incluir um regime novo,
basta criar o módulo e acrescentá-lo à lista REGRAS da esfera correspondente.
"""
from motores import nacional, subnacional, tributario
from motores.base import COLUNAS_RELATORIO, Bases, processar_esteira  # noqa: F401

ESFERAS = {
    "Subnacional": subnacional.REGRAS,
    "Nacional": nacional.REGRAS,
}
NATUREZAS = ["Não Tributário", "Tributário"]


def regra_para(esfera: str, ano: int, natureza: str = "Não Tributário"):
    """Retorna a Regra que atende ao ano na esfera (e natureza), ou None."""
    if natureza == "Tributário":
        regra = tributario.REGRAS.get(esfera)
        return regra if regra and regra.atende(ano) else None
    for regra in ESFERAS.get(esfera, []):
        if regra.atende(ano):
            return regra
    return None


def esfera_disponivel(esfera: str) -> bool:
    return any(r.disponivel for r in ESFERAS.get(esfera, []))
