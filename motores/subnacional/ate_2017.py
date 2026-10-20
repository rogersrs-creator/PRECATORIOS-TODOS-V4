"""Subnacional - Propostas até 2017 (origem: PREC-EXTRA-ATE-2017.py)."""
from motores.base import (MARCO_FIM_POUPANCA as FASE1, JUROS_MENSAL,
                          Regra, meses_inteiros, passo_correcao, passo_ipca_juros,
                          passo_selic_simples, var_ipca, var_ipca15, var_selic)


class RegraAte2017(Regra):
    esfera = "Subnacional"
    nome = "Propostas até 2017"
    ano_ini, ano_fim = 1900, 2017
    modelo_descricao = ("Graça e até 11/2021: IPCA-15 (sem poupança) → 12/2021 a {fim_selic}: SELIC simples "
                 "→ a partir de {ini_ipca}: IPCA + juros 0,1666% a.m.")

    def atualizar(self, p, j, d_ini, d_fim, graca, bases):
        t = d_ini
        while t < d_fim:
            if t < graca:
                next_t = min(d_fim, graca)
                p, j = passo_correcao(p, j, var_ipca15(bases, t, next_t))
            elif t < FASE1:
                next_t = min(d_fim, FASE1)
                p, j = passo_correcao(p, j, var_ipca15(bases, t, next_t))
            elif t < self.marco_ipca:
                next_t = min(d_fim, self.marco_ipca)
                p, j = passo_selic_simples(p, j, var_selic(bases, t, next_t))
            else:
                next_t = d_fim
                p, j = passo_ipca_juros(p, j, bases, t, next_t)
            t = next_t
        return p, j

    def classificar(self, data_ref, last_date, graca, bases):
        if data_ref <= graca:
            return "IPCA-15 (Graça)", var_ipca15(bases, last_date, data_ref), 0.0
        if data_ref <= FASE1:
            return "IPCA-15", var_ipca15(bases, last_date, data_ref), 0.0
        if data_ref <= self.marco_ipca:
            m = max(last_date, FASE1)
            return "SELIC SIMPLES", var_selic(bases, m, data_ref), 0.0
        m = max(last_date, self.marco_ipca)
        return "IPCA + JUROS", var_ipca(bases, m, data_ref), meses_inteiros(m, data_ref) * JUROS_MENSAL
