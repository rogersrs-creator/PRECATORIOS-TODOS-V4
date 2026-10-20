"""
Subnacional - Proposta 2027 (V3: com o componente Juros Selic).

Componentes: Valor Principal (P), Juros (J) e Juros Selic (S) - os três informados no formulário.

Da inclusão em proposta até o fim do período de graça:
  - IPCA sobre cada campo, somando o acréscimo no próprio campo (P, J e S).
Após o fim do período de graça:
  - IPCA sobre cada campo, somando o acréscimo no próprio campo;
  - depois, juros de 0,1666...% a.m. sobre o Valor Principal (já corrigido),
    somados no campo Juros. O campo Juros Selic recebe só o IPCA.
Pagamentos: abatimento proporcional ao peso de P, J e S no total (esteira comum).
"""
from motores.base import JUROS_MENSAL, Regra, meses_inteiros, var_ipca


class Regra2027(Regra):
    esfera = "Subnacional"
    nome = "Proposta 2027"
    ano_ini, ano_fim = 2027, 2027
    usa_selic = True
    modelo_descricao = ("Graça: IPCA sobre principal, juros e juros Selic → após a graça: IPCA sobre os três "
                 "+ juros 0,1666% a.m. sobre o principal, lançados nos juros.")

    def atualizar_psj(self, p, j, s, d_ini, d_fim, graca, bases):
        t = d_ini
        while t < d_fim:
            if t < graca:
                next_t = min(d_fim, graca)
                v = var_ipca(bases, t, next_t)
                p, j, s = p * (1 + v), j * (1 + v), s * (1 + v)
            else:
                next_t = d_fim
                v = var_ipca(bases, t, next_t)
                var_juros = meses_inteiros(t, next_t) * JUROS_MENSAL
                p, j, s = p * (1 + v), j * (1 + v), s * (1 + v)
                j = j + p * var_juros
            t = next_t
        return p, j, s

    def atualizar(self, p, j, d_ini, d_fim, graca, bases):
        p, j, _ = self.atualizar_psj(p, j, 0.0, d_ini, d_fim, graca, bases)
        return p, j

    def classificar(self, data_ref, last_date, graca, bases):
        if data_ref <= graca:
            return "IPCA (Graça)", var_ipca(bases, last_date, data_ref), 0.0
        m = max(last_date, graca)
        return "IPCA + JUROS", var_ipca(bases, m, data_ref), meses_inteiros(m, data_ref) * JUROS_MENSAL
