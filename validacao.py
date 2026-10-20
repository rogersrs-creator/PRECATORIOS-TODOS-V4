"""
Validação dos pagamentos digitados no formulário.

Regras:
  - cada linha precisa de data e valor;
  - a data precisa ser válida, com ano de 4 dígitos, entre a data-base inicial e hoje,
    e não pode passar da data final da dívida;
  - a ORDEM das linhas é a ordem do pagamento (linha 1 = pagamento 1). As datas precisam
    seguir essa ordem: um pagamento não pode ter data anterior à do pagamento de cima.
    Assim, uma data digitada errado é apontada em vez de ser reordenada em silêncio.
"""
from datetime import date

import pandas as pd

ANO_MIN, ANO_MAX = 1900, 2099


def _fmt(d):
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def validar_pagamentos(df_editor: pd.DataFrame, data_inicial: pd.Timestamp,
                       data_final: pd.Timestamp, hoje: date | None = None):
    """
    df_editor: DataFrame do st.data_editor com 'Data de Pagamento' e 'Valor Depositado'.
    data_inicial / data_final: datas no dia 1º do mês.
    Retorna (pagamentos, erros). 'pagamentos' tem ordem_pagamento, data_pagamento e
    Valor_Depositado, na ordem digitada; só deve ser usado se 'erros' estiver vazio.
    """
    hoje = pd.Timestamp(hoje or date.today())
    erros = []
    pags = df_editor.dropna(how="all").reset_index(drop=True).copy()
    pags["ordem_pagamento"] = range(1, len(pags) + 1)

    datas = pd.to_datetime(pags["Data de Pagamento"], errors="coerce")
    valores = pd.to_numeric(pags["Valor Depositado"], errors="coerce")

    for i in range(len(pags)):
        n = i + 1
        d, v = datas.iloc[i], valores.iloc[i]
        if pd.isna(d):
            erros.append(f"Pagamento {n}: **data em branco ou inválida**.")
        elif not (ANO_MIN <= d.year <= ANO_MAX):
            erros.append(f"Pagamento {n}: ano **{d.year}** inválido (use 4 dígitos, ex.: 2025).")
        else:
            if d.replace(day=1) < data_inicial:
                erros.append(f"Pagamento {n} ({_fmt(d)}): anterior à data-base inicial "
                             f"({data_inicial:%m/%Y}).")
            if d > hoje:
                erros.append(f"Pagamento {n} ({_fmt(d)}): data no futuro. "
                             "Informe apenas pagamentos já efetuados.")
            if d.replace(day=1) > data_final:
                erros.append(f"Pagamento {n} ({_fmt(d)}): posterior à data final da dívida "
                             f"({data_final:%m/%Y}).")
        if pd.isna(v):
            erros.append(f"Pagamento {n}: **valor em branco**.")
        elif v < 0:
            erros.append(f"Pagamento {n}: valor negativo.")

    # Ordem cronológica: compara cada data com a maior data anterior válida
    maior, n_maior = None, None
    for i in range(len(pags)):
        d = datas.iloc[i]
        if pd.isna(d) or not (ANO_MIN <= d.year <= ANO_MAX):
            continue
        if maior is not None and d < maior:
            erros.append(f"Pagamento {i + 1} ({_fmt(d)}) tem data **anterior** à do pagamento "
                         f"{n_maior} ({_fmt(maior)}). Confira as datas: os pagamentos devem estar "
                         "em ordem cronológica, do mais antigo para o mais recente.")
        if maior is None or d >= maior:
            maior, n_maior = d, i + 1

    pags["data_pagamento"] = datas
    pags["Valor_Depositado"] = valores
    return pags[["ordem_pagamento", "data_pagamento", "Valor_Depositado"]], erros


def validar_data_final(data_final: pd.Timestamp, data_inicial: pd.Timestamp):
    erros = []
    if not (ANO_MIN <= data_final.year <= ANO_MAX):
        erros.append(f"Data final da dívida com ano **{data_final.year}** inválido.")
    elif data_final < data_inicial:
        erros.append(f"A data final é anterior à data-base inicial ({data_inicial:%m/%Y}).")
    return erros
