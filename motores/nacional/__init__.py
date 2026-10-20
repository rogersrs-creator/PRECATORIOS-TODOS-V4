"""
Precatórios NACIONAIS (União).

Até a EC 136/2025 as regras são iguais às dos subnacionais. A diferença é o início do
IPCA + juros 0,1666% a.m.: para a União começa um mês depois (marco 01/09/2025):
  - SELIC simples até a variação de agosto/2025;
  - IPCA a partir da variação de setembro/2025 (aplicada em outubro).

Cada motor nacional herda o motor subnacional da mesma faixa e troca apenas o marco.
Período de graça: mesma tabela GRACA das propostas subnacionais.
"""
from motores.base import MARCO_INICIO_IPCA_NACIONAL
from motores.subnacional.ate_2017 import RegraAte2017
from motores.subnacional.p2018_2020 import Regra2018a2020
from motores.subnacional.p2021_2024 import Regra2021a2024
from motores.subnacional.p2025_2026 import Regra2025a2026
from motores.subnacional.p2027 import Regra2027


def _nacional(base_cls):
    return type(base_cls.__name__ + "Nacional", (base_cls,), {
        "esfera": "Nacional",
        "marco_ipca": MARCO_INICIO_IPCA_NACIONAL,
    })


NacionalAte2017 = _nacional(RegraAte2017)
Nacional2018a2020 = _nacional(Regra2018a2020)
Nacional2021a2024 = _nacional(Regra2021a2024)
Nacional2025a2026 = _nacional(Regra2025a2026)
Nacional2027 = _nacional(Regra2027)

REGRAS = [
    NacionalAte2017(),
    Nacional2018a2020(),
    Nacional2021a2024(),
    Nacional2025a2026(),
    Nacional2027(),
]
