"""
Leitura das bases de índices.

Ordem de busca para cada base:
  1. URL da planilha pública do Google Sheets (config.py ou st.secrets)
  2. CSV local na pasta 'dados/' do repositório (fallback / testes)
"""
import io
import os
import re
import urllib.error
import urllib.request

import pandas as pd

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

ARQUIVOS_LOCAIS = {
    "IPCA15": "IPCA-15-BASE-PYTHON.csv",
    "POUPANCA": "POUPANCA-BASE-PYTHON.csv",
    "SELIC": "SELIC-BASE-PYTHON.csv",
    "IPCA": "IPCA-BASE-PYTHON.csv",
    "GRACA": "BASE-ANO-PROPOSTA-PERIODO-GRACA.csv",
}


# ------------------------------------------------------------------------------
# Google Sheets
# ------------------------------------------------------------------------------
def url_exportacao_csv(url_planilha: str) -> str:
    """
    Converte o link normal de uma planilha pública
    (https://docs.google.com/spreadsheets/d/<ID>/edit#gid=<GID>)
    no link de exportação CSV da aba indicada pelo gid.
    """
    m_id = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url_planilha)
    if not m_id:
        raise ValueError(f"Link de planilha inválido: {url_planilha}")
    m_gid = re.search(r"[#&?]gid=(\d+)", url_planilha)
    gid = m_gid.group(1) if m_gid else "0"
    return f"https://docs.google.com/spreadsheets/d/{m_id.group(1)}/export?format=csv&gid={gid}"


def _baixar_texto(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        conteudo = resp.read()
    texto = conteudo.decode("utf-8-sig", errors="replace")
    if texto.lstrip().lower().startswith("<!doctype html") or "<html" in texto[:500].lower():
        raise PermissionError(
            "O Google devolveu uma página HTML em vez do CSV. Verifique se a planilha está "
            "compartilhada como 'Qualquer pessoa com o link – Leitor'.")
    return texto


def _ler_csv_texto(texto: str) -> pd.DataFrame:
    """Lê CSV detectando o separador (Google exporta com vírgula; os arquivos locais usam ';')."""
    primeira = texto.splitlines()[0] if texto else ""
    sep = ";" if primeira.count(";") >= primeira.count(",") and ";" in primeira else ","
    df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    # remove linhas totalmente vazias
    df = df[~(df.apply(lambda r: "".join(r).strip() == "", axis=1))]
    return df


# ------------------------------------------------------------------------------
# Normalização de números e datas (aceita formato BR e US)
# ------------------------------------------------------------------------------
def para_numero(valor):
    """'1,0078' -> 1.0078 | '1.234,56' -> 1234.56 | 'R$ 871,04' -> 871.04 | '1.97%' -> 1.97"""
    if valor is None:
        return float("nan")
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).replace("R$", "").replace("%", "")
    s = re.sub(r"[\s\xa0]+", "", s)
    if s == "":
        return float("nan")
    if "," in s and "." in s:
        # o último separador é o decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _preparar_indice(df: pd.DataFrame, nome: str) -> pd.DataFrame:
    if "data" not in df.columns or "n_indice" not in df.columns:
        raise ValueError(f"A base {nome} precisa das colunas 'data' e 'n_indice'. "
                         f"Colunas encontradas: {list(df.columns)}")
    out = pd.DataFrame()
    out["data"] = pd.to_datetime(df["data"].str.strip(), dayfirst=True, errors="coerce")
    out["n_indice"] = df["n_indice"].apply(para_numero)
    col_var = next((c for c in df.columns if c.startswith(("variac", "variaç"))), None)
    if col_var:
        out["variacao"] = df[col_var].apply(para_numero)   # usada só na verificação das bases
    out = out.dropna(subset=["data", "n_indice"])
    out["data"] = out["data"].apply(lambda dt: dt.replace(day=1))
    return out.sort_values("data").reset_index(drop=True)


def _preparar_graca(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.upper() for c in df.columns]
    obrig = ["ANO_PROPOSTA", "DATA_BASE_INICIAL_CALCULOS", "FIM_PER_GRACA"]
    faltando = [c for c in obrig if c not in df.columns]
    if faltando:
        raise ValueError(f"A base de período de graça está sem as colunas {faltando}.")
    out = pd.DataFrame()
    out["ANO_PROPOSTA"] = df["ANO_PROPOSTA"].apply(para_numero)
    out["DATA_BASE_INICIAL_CALCULOS"] = pd.to_datetime(
        df["DATA_BASE_INICIAL_CALCULOS"].str.strip(), dayfirst=True, errors="coerce")
    out["FIM_PER_GRACA"] = pd.to_datetime(df["FIM_PER_GRACA"].str.strip(), dayfirst=True, errors="coerce")
    out = out.dropna()
    out["ANO_PROPOSTA"] = out["ANO_PROPOSTA"].astype(int)
    for c in ["DATA_BASE_INICIAL_CALCULOS", "FIM_PER_GRACA"]:
        out[c] = out[c].apply(lambda dt: dt.replace(day=1))
    return out.reset_index(drop=True)


# ------------------------------------------------------------------------------
# API pública
# ------------------------------------------------------------------------------
def carregar_base(nome: str, url: str = "") -> tuple[pd.DataFrame, str]:
    """Retorna (DataFrame tratado, origem)."""
    if url and url.strip():
        texto = _baixar_texto(url_exportacao_csv(url.strip()))
        origem = "Google Sheets"
    else:
        caminho = os.path.join(PASTA_DADOS, ARQUIVOS_LOCAIS[nome])
        with open(caminho, "rb") as f:
            bruto = f.read()
        try:
            texto = bruto.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = bruto.decode("latin1")
        origem = f"arquivo local ({ARQUIVOS_LOCAIS[nome]})"

    df = _ler_csv_texto(texto)
    # normaliza cabeçalhos com acento (ex.: 'variacao-mês')
    if nome == "GRACA":
        return _preparar_graca(df), origem
    df.columns = [c.lower() for c in df.columns]
    return _preparar_indice(df, nome), origem


def carregar_todas(urls: dict) -> tuple[tuple, pd.DataFrame, dict]:
    """
    urls: {'IPCA15': '...', 'POUPANCA': '...', 'SELIC': '...', 'IPCA': '...', 'GRACA': '...'}
    Retorna ((ipca15, poup, selic, ipca), df_graca, {nome: origem})
    """
    dfs, origens, erros = {}, {}, []
    for nome in ARQUIVOS_LOCAIS:
        try:
            dfs[nome], origens[nome] = carregar_base(nome, urls.get(nome, ""))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                erros.append(f"{nome}: planilha não está pública (erro {e.code}). Compartilhe como "
                             f"'Qualquer pessoa com o link – Leitor'.")
            else:
                erros.append(f"{nome}: erro HTTP {e.code} ao baixar a planilha.")
        except Exception as e:
            erros.append(f"{nome}: {e}")
    if erros:
        raise RuntimeError("\n\n".join(erros))
    bases = (dfs["IPCA15"], dfs["POUPANCA"], dfs["SELIC"], dfs["IPCA"])
    return bases, dfs["GRACA"], origens
