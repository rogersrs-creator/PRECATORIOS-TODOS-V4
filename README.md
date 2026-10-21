# Atualização de Precatórios – App Streamlit V4 (todas as propostas até 2027, subnacionais e nacionais)

Reúne num só app os cálculos que antes eram feitos por 5 scripts locais:

| Esfera | Regime | Anos de proposta | Script de origem |
|---|---|---|---|
| Subnacional | Propostas até 2017 | até 2017 | `PREC-EXTRA-ATE-2017.py` |
| Subnacional | Propostas 2018 a 2020 | 2018–2020 | `PREC-EXTRA-2018-2020.py` |
| Subnacional | Propostas 2021 a 2024 | 2021–2024 | `PREC-EXTRA-2021-2024.py` |
| Subnacional | Propostas 2025 e 2026 | 2025–2026 | `PREC-EXTRA-2025-2026.py` |
| Subnacional | Proposta 2027 | 2027 | `gemini-code-...py` (ramo 2027) |
| Nacional | os mesmos 5 grupos | 2012–2027 | iguais aos subnacionais, com IPCA a partir de 09/2025 |

O usuário escolhe a **esfera** e o **ano da proposta**; o app seleciona o motor sozinho e mostra
na tela qual regime está sendo aplicado. Os motores foram conferidos contra os scripts
originais em 1.050 cenários aleatórios, com diferença zero.

## Estrutura

```
app.py                     # interface (esfera, ano, formulário, resultado, downloads)
importacao.py              # leitura dos pagamentos colados da tela do sistema
validacao.py               # validação das datas e da ordem dos pagamentos
fontes.py                  # leitura das bases (Google Sheets ou CSV local)
relatorio.py               # geração do Excel e do CSV
config.py                  # links das planilhas do Google Sheets
requirements.txt
motores/
├── __init__.py            # registro: escolhe o motor por (esfera, ano)
├── base.py                # índices, passos de atualização e esteira de amortização (comuns)
├── subnacional/
│   ├── __init__.py        # lista dos regimes subnacionais
│   ├── ate_2017.py
│   ├── p2018_2020.py
│   ├── p2021_2024.py
│   ├── p2025_2026.py
│   └── p2027.py
├── nacional/
│   └── __init__.py        # motores nacionais (União)
└── tributario.py          # precatórios de natureza tributária (as duas esferas)
dados/                     # CSVs de reserva (usados se um link do config.py estiver vazio)
.streamlit/config.toml
```

**As pastas `motores/`, `motores/subnacional/` e `motores/nacional/` são obrigatórias.**
Sem elas o app não abre.

## Planilha do período de graça (GRACA)

Todas as propostas usam **uma única** tabela de período de graça, com as colunas
`ANO_PROPOSTA;DATA_BASE_INICIAL_CALCULOS;FIM_PER_GRACA`.
O arquivo `dados/BASE-ANO-PROPOSTA-PERIODO-GRACA.csv` já reúne as propostas de 2012 a 2027
(junção dos antigos arquivos ATE-2020, 2021-ATE-2024, 2025-2026 e 2027). Importe esse arquivo na
planilha GRACA do Google Sheets, substituindo o conteúdo atual.
Para uma proposta nova (ex.: 2028), basta acrescentar a linha na planilha e criar o regime em `motores/`.
O app só oferece os anos que existem nessa planilha e avisa quais estão faltando.

## Como incluir os precatórios nacionais

1. Crie um arquivo em `motores/nacional/` (ex.: `p2025_2026.py`), copiando o regime subnacional
   mais parecido e ajustando o que muda nos métodos `atualizar()` e `classificar()`.
   Defina `esfera = "Nacional"` e a faixa `ano_ini`/`ano_fim`.
2. Em `motores/nacional/__init__.py`, importe a classe nova e coloque-a na lista `REGRAS`
   (removendo `NacionalEmDesenvolvimento` quando todos os anos estiverem cobertos).
3. Faça o commit. O app passa a liberar a opção "Nacional" automaticamente.

Se os nacionais usarem datas de graça diferentes, será preciso uma planilha de graça própria;
isso é um ajuste pequeno em `fontes.py` e `app.py`.

## Publicar

1. Crie um repositório novo no GitHub (ex.: `PRECATORIOS-CALCULO`).
2. Envie **todo** o conteúdo desta pasta mantendo as subpastas: arraste a pasta inteira para a
   tela de upload do GitHub ou use "Publish to GitHub" no VS Code.
3. Em share.streamlit.io: Create app → repositório novo → branch `main` → arquivo `app.py` → Deploy.

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Importar pagamentos da tela do sistema

No app, abra "Importar pagamentos da tela do sistema", cole a tabela copiada do sistema
(com o cabeçalho) e clique em Importar. O app lê as colunas "Data de Pagamento" e
"Valor Depositado" pelo nome e, por padrão, ignora as linhas com Quitado = Sim.
Os pagamentos vão para a tabela do formulário para conferência antes do cálculo.

## V3 – Proposta 2027 com Juros Selic

- O formulário mostra o campo **Juros Selic** (obrigatório) ao lado de Valor Principal e Juros
  apenas para a proposta 2027 (regimes com `usa_selic = True`).
- Graça: IPCA sobre principal, juros e juros Selic, cada um somado no próprio campo.
- Após a graça: IPCA sobre os três campos e, depois, juros de 0,1666...% a.m. sobre o principal
  corrigido, somados no campo Juros.
- Pagamentos: abatimento proporcional ao peso de principal, juros e juros Selic no total.
- O relatório da proposta 2027 ganha as colunas juros_selic_proposta, Per_Selic_Pagto e Saldo_Selic;
  os demais regimes continuam com o relatório no formato anterior.

## Precatórios nacionais (União)

Até a EC 136/2025 as regras são iguais às dos subnacionais. A diferença é o início do IPCA + juros:
- Subnacional: marco 01/08/2025 (SELIC até a variação de julho/2025; IPCA a partir da variação de agosto, aplicada em setembro).
- Nacional: marco 01/09/2025 (SELIC até a variação de agosto/2025; IPCA a partir da variação de setembro, aplicada em outubro).

Cada motor nacional (`motores/nacional/__init__.py`) herda o subnacional da mesma faixa e troca só o atributo
`marco_ipca`. O período de graça usa a mesma tabela GRACA.

## Precatórios tributários

Escolha **Natureza › Tributário** (ao lado da esfera). Vale para Subnacional e Nacional e para todas as propostas.
- SELIC simples **só sobre o principal**, da data-base do cálculo até cada pagamento e até a data final.
- O valor da SELIC vai para o campo **Selic**; os juros informados não mudam. Como a SELIC incide só sobre o
  principal, total e saldo seriam os mesmos lançando-a nos juros (para isso, troque `DESTINO_SELIC` em
  `motores/tributario.py`).
- Não há período de graça nem troca de índice nas EC 113/2021 e 136/2025.
- **Data-base do cálculo:** é a do próprio precatório e pode ser anterior à da proposta. O padrão é a data-base da
  proposta (planilha GRACA).
- O campo Selic inicial é opcional (padrão 0,00).
- Pagamentos: mesma amortização proporcional dos demais regimes.

Conferido com 8 cálculos homologados de tributários (propostas 2018, 2020, 2022, 2026 e 2027, com e sem pagamentos):
todos conferem ao centavo. Os casos estão na pasta `conferencia/` (arquivos `...-TRIBUTARIO-...`), sem número de
processo nem nome de parte.

## Conferência automática (casos homologados)

Na barra lateral, escolha **Página › Conferência de casos homologados**. A página faz duas verificações:

1. **Consistência das bases de índices:** confere todas as linhas das quatro bases (IPCA-15, Poupança, SELIC, IPCA):
   cada número-índice precisa bater com o anterior e com a variação do mês, e não pode haver mês repetido ou faltando.
   Encontra erros de digitação em qualquer mês, inclusive nos que nenhum caso usa.
2. **Casos homologados:** refaz cada relatório da pasta `conferencia/` com os índices e os motores atuais e compara
   todas as linhas (total na data e saldo após cada pagamento), com tolerância de R$ 0,05. Em caso de divergência,
   mostra a linha a partir da qual o caso diverge.

Use depois de atualizar as planilhas do Google Sheets e depois de publicar uma versão nova.

**Para incluir um caso novo:** gere o relatório Excel no próprio app (com os dados do processo homologado), confira o
saldo com o valor homologado e coloque o arquivo na pasta `conferencia/` do repositório. Também é possível testar um
relatório sem colocá-lo na pasta, enviando-o pelo campo de upload da página.
