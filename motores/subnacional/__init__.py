"""Precatórios SUBNACIONAIS (estados e municípios) - um módulo por faixa de propostas."""
from motores.subnacional.ate_2017 import RegraAte2017
from motores.subnacional.p2018_2020 import Regra2018a2020
from motores.subnacional.p2021_2024 import Regra2021a2024
from motores.subnacional.p2025_2026 import Regra2025a2026
from motores.subnacional.p2027 import Regra2027

REGRAS = [
    RegraAte2017(),
    Regra2018a2020(),
    Regra2021a2024(),
    Regra2025a2026(),
    Regra2027(),
]
