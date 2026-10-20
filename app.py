"""
App Streamlit - Atualização de Precatórios (todas as propostas até 2027)
Executar localmente:  streamlit run app.py
"""
from datetime import date

import pandas as pd
import streamlit as st

import config
from fontes import carregar_todas, para_numero
from motores import ESFERAS, Bases, esfera_disponivel, processar_esteira, regra_para
from relatorio import gerar_csv, gerar_excel, tabela_para_tela
from importacao import importar_texto
from validacao import validar_data_final, validar_pagamentos

st.set_page_config(page_title="Atualização de Precatórios", page_icon="📊", layout="wide")


# ------------------------------------------------------------------------------
# Bases de índices (cache de 1 hora; botão na barra lateral força recarga)
# ------------------------------------------------------------------------------
def obter_urls() -> dict:
    urls = dict(config.PLANILHAS)
    try:
        if "planilhas" in st.secrets:
            urls.update({k.upper(): v for k, v in st.secrets["planilhas"].items()})
    except Exception:
        pass
    return urls


@st.cache_data(ttl=3600, show_spinner="Carregando índices...")
def carregar_bases_cache(urls_itens: tuple):
    return carregar_todas(dict(urls_itens))


with st.sidebar:
    st.header("Bases de índices")
    if st.button("🔄 Recarregar índices", use_container_width=True):
        carregar_bases_cache.clear()
        st.session_state.pop("resultado", None)

try:
    tupla_bases, df_graca, origens = carregar_bases_cache(tuple(sorted(obter_urls().items())))
except Exception as e:
    st.error(f"Não foi possível carregar as bases de índices.\n\n**Detalhe:** {e}")
    st.stop()

bases = Bases(*tupla_bases)
ultima_data_comum = min(df["data"].max() for df in bases)

with st.sidebar:
    for nome, df in zip(["IPCA-15", "Poupança", "SELIC", "IPCA"], bases):
        st.caption(f"**{nome}**: {len(df)} meses · até {df['data'].max():%m/%Y}")
    anos_graca = sorted(df_graca["ANO_PROPOSTA"].unique().tolist())
    st.caption(f"**Período de graça**: propostas {anos_graca[0]} a {anos_graca[-1]}"
               if anos_graca else "**Período de graça**: vazio")
    with st.expander("Origem dos dados"):
        for k, v in origens.items():
            st.write(f"{k}: {v}")
    with st.expander("Regimes de cálculo"):
        for esf, regras in ESFERAS.items():
            st.markdown(f"**{esf}**")
            for r in regras:
                st.caption(f"{r.nome}{'' if r.disponivel else ' (em desenvolvimento)'}: {r.descricao}")

# ------------------------------------------------------------------------------
# Esfera e ano (fora do formulário para mostrar o regime na hora)
# ------------------------------------------------------------------------------
st.title("📊 Atualização de Precatórios")

c_esf, c_ano, c_reg = st.columns([1.2, 1, 3])
esfera = c_esf.radio("Esfera", list(ESFERAS.keys()), horizontal=True)

if not esfera_disponivel(esfera):
    st.info(f"O modelo de cálculo para a esfera **{esfera}** ainda está em desenvolvimento. "
            "Selecione **Subnacional** para calcular.")
    st.stop()

anos_disponiveis = [a for a in anos_graca if (r := regra_para(esfera, a)) and r.disponivel]
ano_proposta = c_ano.selectbox("Ano da proposta", anos_disponiveis, index=None,
                               placeholder="Selecione o ano...")

anos_sem_graca = [a for a in range(2021, 2028) if a not in anos_graca and regra_para(esfera, a)]
if anos_sem_graca:
    c_reg.warning("Sem período de graça cadastrado para as propostas "
                  f"{', '.join(map(str, anos_sem_graca))}. Inclua esses anos na planilha GRACA.")

if ano_proposta is None:
    st.stop()

regra = regra_para(esfera, ano_proposta)
linha_graca = df_graca[df_graca["ANO_PROPOSTA"] == ano_proposta].iloc[0]
data_inicial = linha_graca["DATA_BASE_INICIAL_CALCULOS"]
fim_graca = linha_graca["FIM_PER_GRACA"]

c_reg.info(f"**Regime: {regra.esfera} – {regra.nome}**  \n{regra.descricao}  \n"
           f"Data-base inicial: {data_inicial:%d/%m/%Y} · Fim da graça: {fim_graca:%d/%m/%Y}")

# ------------------------------------------------------------------------------
# Formulário de entrada
# ------------------------------------------------------------------------------
PAGAMENTOS_VAZIOS = pd.DataFrame({
    "Data de Pagamento": pd.Series(dtype="datetime64[ns]"),
    "Valor Depositado": pd.Series(dtype="float"),
})

# ------------------------------------------------------------------------------
# Importação dos pagamentos (copiar da tela do sistema e colar aqui)
# ------------------------------------------------------------------------------
st.session_state.setdefault("pag_versao", 0)
with st.expander("📋 Importar pagamentos da tela do sistema", expanded="pag_importados" not in st.session_state):
    st.caption("Na tela do sistema, selecione a tabela **com o cabeçalho**, copie (Ctrl+C), "
               "cole abaixo (Ctrl+V) e clique em **Importar**. Os pagamentos vão para a tabela do "
               "formulário, onde podem ser conferidos e corrigidos antes do cálculo.")
    texto_colado = st.text_area("Texto copiado", height=150, label_visibility="collapsed",
                                placeholder="Data de Pagamento\tSituação\tQuitado\t...\tValor Depositado")
    ci1, ci2, ci3 = st.columns([2, 1, 1])
    ignorar_quitados = ci1.checkbox("Ignorar linhas com Quitado = Sim", value=True)
    if ci2.button("Importar", type="primary", use_container_width=True):
        df_imp, avisos_imp = importar_texto(texto_colado, ignorar_quitados)
        st.session_state["pag_importados"] = df_imp
        st.session_state["avisos_importacao"] = avisos_imp
        st.session_state["pag_versao"] += 1
        st.session_state.pop("resultado", None)
    if ci3.button("Limpar tabela", use_container_width=True):
        st.session_state.pop("pag_importados", None)
        st.session_state.pop("avisos_importacao", None)
        st.session_state["pag_versao"] += 1
        st.session_state.pop("resultado", None)

if "pag_importados" in st.session_state:
    n_imp = len(st.session_state["pag_importados"])
    st.success(f"{n_imp} pagamento(s) importado(s). Confira a tabela abaixo antes de calcular.")
    for aviso in st.session_state.get("avisos_importacao", []):
        st.warning(aviso)

HOJE = date.today()
DATA_MIN = data_inicial.date()                      # nada antes da data-base da proposta
DATA_FINAL_MAX = date(HOJE.year + 5, 12, 31)       # limite para a data final da dívida
valor_data_final = min(max(HOJE.replace(day=1), DATA_MIN), DATA_FINAL_MAX)

with st.form("form_calculo"):
    st.subheader("Dados da proposta")
    usa_selic = getattr(regra, "usa_selic", False)
    c1, c2, c3, *c4 = st.columns(4 if usa_selic else 3)
    data_final = c1.date_input("Data final da dívida", value=valor_data_final,
                               min_value=DATA_MIN, max_value=DATA_FINAL_MAX,
                               format="DD/MM/YYYY",
                               help="Só o mês/ano é considerado (o dia é ajustado para 1º).")
    principal_txt = c2.text_input("Valor principal (R$)", placeholder="Ex.: 871,04")
    juros_txt = c3.text_input("Juros (R$)", value="0,00")
    selic_txt = (c4[0].text_input("Juros Selic (R$) *", placeholder="Obrigatório (ex.: 0,00)",
                                  help="Campo obrigatório nesta proposta. Informe 0,00 se não houver.")
                 if usa_selic else "")

    st.subheader("Pagamentos efetuados")
    st.caption("Adicione uma linha por pagamento (botão **+** abaixo da tabela), **em ordem "
               "cronológica**: a 1ª linha é o pagamento 1, a 2ª o pagamento 2, e assim por diante. "
               f"Datas aceitas: de {DATA_MIN:%d/%m/%Y} até hoje. Deixe vazia se não houve pagamento.")
    pagamentos_editados = st.data_editor(
        st.session_state.get("pag_importados", PAGAMENTOS_VAZIOS),
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key=f"editor_pagamentos_{st.session_state['pag_versao']}",
        column_config={
            "Data de Pagamento": st.column_config.DateColumn(
                format="DD/MM/YYYY", required=True, min_value=DATA_MIN, max_value=HOJE),
            "Valor Depositado": st.column_config.NumberColumn(
                format="R$ %.2f", min_value=0.0, step=0.01, required=True),
        },
    )

    enviado = st.form_submit_button("Calcular", type="primary", use_container_width=True)

# ------------------------------------------------------------------------------
# Validação e cálculo
# ------------------------------------------------------------------------------
if enviado:
    erros = []
    principal = para_numero(principal_txt)
    juros = para_numero(juros_txt) if juros_txt.strip() else 0.0
    if pd.isna(principal) or principal <= 0:
        erros.append("Informe um **valor principal** válido (ex.: 871,04).")
    if pd.isna(juros) or juros < 0:
        erros.append("Informe um valor de **juros** válido (use 0,00 se não houver).")
    selic = 0.0
    if usa_selic:
        selic = para_numero(selic_txt) if selic_txt.strip() else float("nan")
        if not selic_txt.strip():
            erros.append("O campo **Juros Selic** é obrigatório nesta proposta (informe 0,00 se não houver).")
        elif pd.isna(selic) or selic < 0:
            erros.append("Informe um valor de **Juros Selic** válido (ex.: 1.234,56).")

    data_final_ts = pd.Timestamp(data_final).replace(day=1)
    erros += validar_data_final(data_final_ts, data_inicial)

    pags, erros_pag = validar_pagamentos(pagamentos_editados, data_inicial, data_final_ts, HOJE)
    erros += erros_pag

    if erros:
        for e in erros:
            st.error(e)
        st.session_state.pop("resultado", None)
    else:
        df_final = processar_esteira(
            regra, pags[["ordem_pagamento", "data_pagamento", "Valor_Depositado"]],
            principal, juros, data_inicial, fim_graca, data_final_ts, bases, selic_inicial=selic)

        parametros = {
            "Esfera": regra.esfera,
            "Regime de cálculo": regra.nome,
            "Ano da proposta": ano_proposta,
            "Data-base inicial": data_inicial.strftime("%d/%m/%Y"),
            "Fim do período de graça": fim_graca.strftime("%d/%m/%Y"),
            "Data final da dívida": data_final_ts.strftime("%d/%m/%Y"),
            "Valor principal inicial": float(principal),
            "Juros iniciais": float(juros),
        }
        if usa_selic:
            parametros["Juros Selic iniciais"] = float(selic)
        st.session_state["resultado"] = {
            "df": df_final,
            "parametros": parametros,
            "excel": gerar_excel(df_final, parametros, pags),
            "csv": gerar_csv(df_final),
            "aviso_indice": data_final_ts > ultima_data_comum,
        }

# ------------------------------------------------------------------------------
# Resultado (fica em session_state para não sumir ao clicar em Download)
# ------------------------------------------------------------------------------
res = st.session_state.get("resultado")
if res:
    p = res["parametros"]
    if (p["Esfera"], p["Ano da proposta"]) != (esfera, ano_proposta):
        st.caption("O resultado abaixo é do cálculo anterior. Clique em **Calcular** para atualizar.")
    st.divider()
    st.subheader("Resultado")
    st.caption(f"{p['Esfera']} · {p['Regime de cálculo']} · proposta {p['Ano da proposta']} · "
               f"data-base {p['Data-base inicial']} · fim da graça {p['Fim do período de graça']} · "
               f"data final {p['Data final da dívida']}")

    if res["aviso_indice"]:
        st.warning(f"A data final é posterior ao último índice disponível em todas as bases "
                   f"({ultima_data_comum:%m/%Y}). Para os meses sem índice foi usado o último valor existente.")

    ultima = res["df"].iloc[-1]
    fmt = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    tem_selic = "Saldo_Selic" in res["df"].columns
    cols_m = st.columns(4 if tem_selic else 3)
    cols_m[0].metric("Saldo principal", fmt(ultima["Saldo_Principal"]))
    cols_m[1].metric("Saldo juros", fmt(ultima["Saldo_Juros"]))
    if tem_selic:
        cols_m[2].metric("Saldo juros Selic", fmt(ultima["Saldo_Selic"]))
    cols_m[-1].metric("Saldo total", fmt(ultima["Saldo_Total"]))

    st.dataframe(tabela_para_tela(res["df"]), use_container_width=True, hide_index=True)

    nome_base = f"RELATORIO-{p['Esfera'].upper()}-PROPOSTA-{p['Ano da proposta']}"
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Baixar Excel (.xlsx)", res["excel"], file_name=f"{nome_base}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       type="primary", use_container_width=True)
    d2.download_button("⬇️ Baixar CSV (formato atual)", res["csv"], file_name=f"{nome_base}.csv",
                       mime="text/csv", use_container_width=True)
