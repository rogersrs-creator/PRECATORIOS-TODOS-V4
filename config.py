"""
Links das planilhas públicas do Google Sheets.

Cole aqui o link da ABA correta (copie da barra do navegador com a aba aberta,
ele termina em '#gid=NUMERO'). Pode ser uma planilha com 5 abas ou 5 planilhas separadas.

Se um link ficar vazio (""), o app usa o CSV correspondente da pasta 'dados/' do repositório.

Alternativa: em vez de editar este arquivo, cadastre os mesmos nomes em
Streamlit Cloud > App > Settings > Secrets, na seção [planilhas]
(os Secrets têm prioridade sobre este arquivo).
"""

PLANILHAS = {
    # colunas: data;variacao-mes;n_indice
    "IPCA15":   "https://docs.google.com/spreadsheets/d/1dLjw4_pBk2j55aU8cGEf-0YD-6bBuciv2b2VzmZTP5U/edit?gid=1703299339#gid=1703299339",
    # colunas: data;variacao-mes;n_indice
    "POUPANCA": "https://docs.google.com/spreadsheets/d/15p8EWBw9N19uyQzsxgip42OuOPQIyAnV-zwAk7PPOKE/edit?gid=1434923967#gid=1434923967",
    # colunas: data;variacao-mes;n_indice
    "SELIC":    "https://docs.google.com/spreadsheets/d/129ivdR59PZCXlMRAl1h-9pLosQnW90TEmz6HOS17d7Q/edit?gid=850105924#gid=850105924",
    # colunas: data;variacao-mes;n_indice
    "IPCA":     "https://docs.google.com/spreadsheets/d/11GKOkuxJs4GSsLRQv8h79n-XdcVrAADgMR-7fjxvd2o/edit?gid=1260545934#gid=1260545934",
    # colunas: ANO_PROPOSTA;DATA_BASE_INICIAL_CALCULOS;FIM_PER_GRACA
    "GRACA":    "https://docs.google.com/spreadsheets/d/15bxluzMKAxs66fTgnRb4AY14ouN1ks79jQ4IFwlg_RE/edit?gid=935090251#gid=935090251",
}
