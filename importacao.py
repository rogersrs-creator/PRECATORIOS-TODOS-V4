"""
Importação dos pagamentos a partir do texto copiado da tela do sistema (Ctrl+C / Ctrl+V).

Formato esperado (colunas separadas por tabulação, com cabeçalho):
  Data de Pagamento | Situação | Quitado | Banco | Agência | Conta | Valor Original | Valor Depositado

- Lê as colunas pelo NOME, então a ordem das colunas pode mudar.
- Se não houver cabeçalho (ou ele vier diferente), usa um modo alternativo: em cada linha,
  a primeira data dd/mm/aaaa é a data do pagamento e o último valor em R$ é o valor depositado.
- Linhas com Quitado = "Sim" podem ser ignoradas (opção na tela).
"""
import re
import unicodedata

import pandas as pd

from fontes import para_numero

RE_DATA = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
RE_VALOR = re.compile(r"(?:R\$\s*)?-?\d{1,3}(?:\.\d{3})*,\d{2}\b|(?:R\$\s*)-?\d+(?:,\d{1,2})?")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def _data(txt):
    m = RE_DATA.search(str(txt))
    if not m:
        return None
    d, mth, y = map(int, m.groups())
    try:
        return pd.Timestamp(year=y, month=mth, day=d)
    except ValueError:
        return None


def importar_texto(texto: str, ignorar_quitados: bool = True):
    """
    Retorna (DataFrame com 'Data de Pagamento' e 'Valor Depositado', avisos).
    Os avisos listam linhas ignoradas ou que não puderam ser lidas.
    """
    avisos = []
    linhas = [l for l in texto.replace("\r", "").split("\n") if l.strip()]
    if not linhas:
        return pd.DataFrame(columns=["Data de Pagamento", "Valor Depositado"]), ["Nada para importar."]

    # Localiza o cabeçalho (linha que contém "data de pagamento" e "valor depositado")
    sep = "\t" if any("\t" in l for l in linhas) else None
    idx_cab, cols = None, None
    for i, l in enumerate(linhas[:5]):
        n = _norm(l)
        if "data de pagamento" in n and "valor depositado" in n and sep:
            idx_cab, cols = i, [_norm(c) for c in l.split(sep)]
            break

    registros = []
    corpo = linhas[idx_cab + 1:] if idx_cab is not None else linhas
    for num, l in enumerate(corpo, start=1):
        if idx_cab is not None:
            partes = l.split(sep)
            campo = lambda nome: partes[cols.index(nome)].strip() if nome in cols and cols.index(nome) < len(partes) else ""
            data = _data(campo("data de pagamento"))
            valor = para_numero(campo("valor depositado"))
            quitado = _norm(campo("quitado")) if "quitado" in cols else ""
        else:
            data = _data(l)
            valores = RE_VALOR.findall(l)
            valor = para_numero(valores[-1]) if valores else float("nan")
            quitado = "sim" if re.search(r"\bsim\b", _norm(l)) else ""

        if data is None and pd.isna(valor):
            avisos.append(f"Linha {num} ignorada (não parece um pagamento): “{l.strip()[:60]}”")
            continue
        if data is None or pd.isna(valor):
            avisos.append(f"Linha {num}: não foi possível ler a {'data' if data is None else 'valor'}. "
                          "A linha foi importada incompleta; corrija na tabela.")
        if ignorar_quitados and quitado == "sim":
            v = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            avisos.append(f"Linha {num} ({data:%d/%m/%Y} – R$ {v}) ignorada: Quitado = Sim.")
            continue
        registros.append({"Data de Pagamento": data, "Valor Depositado": valor})

    df = pd.DataFrame(registros, columns=["Data de Pagamento", "Valor Depositado"])
    df["Data de Pagamento"] = pd.to_datetime(df["Data de Pagamento"])
    df["Valor Depositado"] = df["Valor Depositado"].astype(float)
    return df, avisos
