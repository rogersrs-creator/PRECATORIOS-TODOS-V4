"""Subnacional - Propostas 2025 e 2026 (origem: PREC-EXTRA-2025-2026.py)."""
from motores.base import (JUROS_MENSAL, Regra, meses_inteiros,
                          passo_correcao, passo_ipca_juros, passo_selic_simples,
                          var_ipca, var_ipca15, var_selic)


class Regra2025a2026(Regra):
    esfera = "Subnacional"
    nome = "Propostas 2025 e 2026"
    ano_ini, ano_fim = 2025, 2026
    modelo_descricao = ("Graça antes de {ini_ipca}: IPCA-15 · graça a partir de {ini_ipca}: IPCA sem juros · "
                 "fim da graça antes de {ini_ipca}: SELIC simples · depois: IPCA + juros 0,1666% a.m.")

    def atualizar(self, p, j, d_ini, d_fim, graca, bases):
        t = d_ini
        while t < d_fim:
            if t < graca and t < self.marco_ipca:
                next_t = min(d_fim, min(graca, self.marco_ipca))
                p, j = passo_correcao(p, j, var_ipca15(bases, t, next_t))
            elif t < graca and t >= self.marco_ipca:
                next_t = min(d_fim, graca)
                p, j = passo_correcao(p, j, var_ipca(bases, t, next_t))
            elif t >= graca and t < self.marco_ipca:
                next_t = min(d_fim, self.marco_ipca)
                p, j = passo_selic_simples(p, j, var_selic(bases, t, next_t))
            else:
                next_t = d_fim
                p, j = passo_ipca_juros(p, j, bases, t, next_t)
            t = next_t
        return p, j

    def classificar(self, data_ref, last_date, graca, bases):
        if data_ref <= graca and data_ref <= self.marco_ipca:
            return "IPCA-15 (Graça)", var_ipca15(bases, last_date, data_ref), 0.0
        if data_ref <= graca and data_ref > self.marco_ipca:
            m = max(last_date, self.marco_ipca)
            return "IPCA (Graça - S/ Juros)", var_ipca(bases, m, data_ref), 0.0
        if data_ref > graca and data_ref <= self.marco_ipca:
            m = max(last_date, graca)
            return "SELIC SIMPLES", var_selic(bases, m, data_ref), 0.0
        m = max(last_date, max(self.marco_ipca, graca))
        return "IPCA + JUROS", var_ipca(bases, m, data_ref), meses_inteiros(m, data_ref) * JUROS_MENSAL
