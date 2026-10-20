"""Subnacional - Propostas 2018 a 2020 (origem: PREC-EXTRA-2018-2020.py)."""
from motores.base import (MARCO_FIM_POUPANCA as FASE1, JUROS_MENSAL,
                          Regra, meses_inteiros, passo_correcao, passo_ipca_juros,
                          passo_selic_simples, var_ipca, var_ipca15, var_poupanca, var_selic)


class Regra2018a2020(Regra):
    esfera = "Subnacional"
    nome = "Propostas 2018 a 2020"
    ano_ini, ano_fim = 2018, 2020
    modelo_descricao = ("Graça: IPCA-15 → fim da graça a 11/2021: IPCA-15 + poupança → 12/2021 a {fim_selic}: "
                 "SELIC simples → a partir de {ini_ipca}: IPCA + juros 0,1666% a.m.")

    def atualizar(self, p, j, d_ini, d_fim, graca, bases):
        t = d_ini
        while t < d_fim:
            if t < graca:
                next_t = min(d_fim, graca)
                p, j = passo_correcao(p, j, var_ipca15(bases, t, next_t))
            elif t < FASE1:
                next_t = min(d_fim, FASE1)
                v_ipca = var_ipca15(bases, t, next_t)
                v_poup = var_poupanca(bases, t, next_t)
                p_new = p * (1 + v_ipca)
                j = j * (1 + v_ipca) + (p_new * v_poup)
                p = p_new
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
            m = max(last_date, graca)
            return "IPCA-15 + POUP", var_ipca15(bases, m, data_ref), var_poupanca(bases, m, data_ref)
        if data_ref <= self.marco_ipca:
            m = max(last_date, FASE1)
            return "SELIC SIMPLES", var_selic(bases, m, data_ref), 0.0
        m = max(last_date, self.marco_ipca)
        return "IPCA + JUROS", var_ipca(bases, m, data_ref), meses_inteiros(m, data_ref) * JUROS_MENSAL
