import os
import re
import uuid
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from utils.db import get_db, registrar_evento
from utils.nlp import build_topics
from utils.pubmed import get_dados_pubmed
from utils.covid import get_dados_covid
from deep_translator import GoogleTranslator
translator = GoogleTranslator(source="en", target="pt")

st.set_page_config(page_title="App Saúde – Jornada de Inovação", page_icon=None, layout="wide")

# ========================
# Estilos customizados
# ========================
st.markdown(
    """
    <style>
    
    .stApp {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        font-family: "Segoe UI", sans-serif;
        color: #212529;
    }
    h1, h2, h3 {
        color: #003366;
        font-weight: 600;
    }
    .stCard {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    section[data-testid="stSidebar"] {
        background-color: #f1f3f6;
        border-right: 2px solid #dee2e6;
    }
    div.stButton > button {
        background-color: #003366;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
        font-weight: 500;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #00509e;
        transform: scale(1.02);
    }
    </style>
    """,
    unsafe_allow_html=True
)

def get_configuracao(chave: str, padrao: str | None = None):
    """Lê configuração do st.secrets ou variável de ambiente."""
    try:
        return st.secrets[chave]
    except Exception:
        return os.getenv(chave, padrao)


def primeira_coluna_existente(df: pd.DataFrame, candidatas: list[str]) -> str | None:
    for coluna in candidatas:
        if coluna in df.columns:
            return coluna
    return None


def extrair_ano(valor: str):
    if pd.isna(valor) or valor is None:
        return pd.NA
    try:
        match = re.search(r"(19|20)\d{2}", str(valor))
        return int(match.group(0)) if match else pd.NA
    except Exception:
        return pd.NA


def normalizar_artigos(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["pmid", "titulo", "periodico", "data_publicacao", "resumo", "ano"])

    # Padroniza nomes vindos da API
    if "title" in df.columns:
        df.rename(columns={"title": "titulo"}, inplace=True)
    if "year" in df.columns:
        df.rename(columns={"year": "ano"}, inplace=True)
    if "journal" in df.columns:
        df.rename(columns={"journal": "periodico"}, inplace=True)
    if "pubdate" in df.columns:
        df.rename(columns={"pubdate": "data_publicacao"}, inplace=True)
    if "abstract" in df.columns:
        df.rename(columns={"abstract": "resumo"}, inplace=True)

    # Normaliza ano
    df["ano"] = df["ano"].apply(extrair_ano) if "ano" in df.columns else df["data_publicacao"].apply(extrair_ano)
    return df


def traduzir_termos(lista_termos: list[str]) -> list[str]:
    traduzidos = []
    for termo in lista_termos:
        try:
            t = translator.translate(termo)
            traduzidos.append(t)
        except Exception:
            traduzidos.append(termo)  
    return traduzidos

def gerar_pdf(texto: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    flowables = []

    for linha in texto.splitlines():
        if linha.strip().startswith("# "):  
            flowables.append(Paragraph(f"<b>{linha.replace('#', '').strip()}</b>", styles["Title"]))
        elif linha.strip().startswith("## "):  
            flowables.append(Paragraph(f"<b>{linha.replace('#', '').strip()}</b>", styles["Heading2"]))
        else:  # texto normal
            flowables.append(Paragraph(linha, styles["Normal"]))
        flowables.append(Spacer(1, 8))

    doc.build(flowables)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def gerar_relatorio(
    tema: str,
    ano_inicio: int,
    ano_fim: int,
    artigos: pd.DataFrame,
    covid_periodo: pd.DataFrame,
    topicos: list[list[str]],
    lacunas: list[str],
    resumo_estados: pd.DataFrame
) -> str:
    linhas = [
        f"# Relatório – Jornada de Inovação\n",
        f"**Tema:** {tema}\n",
        f"**Período:** {ano_inicio}–{ano_fim}\n",
        f"**Artigos (recuperados):** {len(artigos)}\n",
        f"**Linhas COVID (NYTimes) no período:** {len(covid_periodo)}\n\n"
    ]

    if not artigos.empty:
        linhas.append("## Artigos (amostra)\n")
        for _, a in artigos.head(10).iterrows():
            data_pub = a.get("ano", "")
            titulo = a.get("titulo") or "(sem título)"
            linhas.append(f"- {titulo} ({data_pub})\n")

    if not covid_periodo.empty and not resumo_estados.empty:
        linhas.append("\n## COVID-19 (amostra de estados)\n")
        for estado, linha in resumo_estados.head(10).iterrows():
            linhas.append(f"- {estado}: casos={int(linha['casos'])}, mortes={int(linha['mortes'])}\n")

    if topicos:
        linhas.append("\n## Tópicos\n")
        for i, t in enumerate(topicos, 1):
            linhas.append(f"- Tópico {i}: {', '.join(t)}\n")

    if lacunas:
        linhas.append("\n## Oportunidades (heurísticas)\n")
        for g in lacunas:
            linhas.append(f"- {g}\n")

    linhas.append("\n---\n**Fontes:** PubMed (NCBI E-utilities), NYTimes COVID-19 dataset (https://github.com/nytimes/covid-19-data).\n")
    return "".join(linhas)


# ---------------------------
# Configuração e sessão
# ---------------------------
BANCO = get_configuracao("DB_NAME", "appsaude")
LOG_PADRAO = True

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

cliente, banco = get_db()

# ---------------------------
# Barra lateral
# ---------------------------
with st.sidebar:
    st.title("Jornada Interativa")
    st.caption("Exploração guiada de oportunidades tecnológicas em saúde.")

    tema = st.text_input("Tema/assunto (ex.: tratamento de diabetes)", value="tratamento de diabetes")
    ano_inicio, ano_fim = st.slider(
        "Período (ano)",
        2000,
        datetime.utcnow().year,
        (2015, datetime.utcnow().year),
    )
    qtd_artigos = st.number_input("Qtd. de artigos (PubMed)", min_value=5, max_value=200, value=50, step=5)

    st.subheader("Privacidade")
    st.checkbox("Permitir salvar interações (anônimo)", key="consent_logging", value=LOG_PADRAO)

    rodar_btn = st.button("Rodar jornada")

# ---------------------------
# Conteúdo principal
# ---------------------------
st.title("App Saúde – Jornada de Desenvolvimento e Inovação")
st.write(
    "Digite um tema na barra lateral e clique em **Rodar jornada**. "
    "O app vai buscar artigos (PubMed), carregar dados epidemiológicos (NYTimes COVID), sugerir tópicos e gerar um relatório."
)


artigos_df = pd.DataFrame()
covid_df = pd.DataFrame()
covid_periodo = pd.DataFrame()
resumo_estados = pd.DataFrame()

if rodar_btn and tema.strip():
    consentimento = st.session_state.get("consent_logging", LOG_PADRAO)

    if consentimento:
        registrar_evento(
            banco,
            st.session_state.session_id,
            "run_journey",
            {"topic": tema, "years": [int(ano_inicio), int(ano_fim)], "n_articles": int(qtd_artigos)}
        )

    # ----------------------- PubMed -----------------------
    with st.spinner("Buscando PubMed..."):
        try:
            artigos_df = get_dados_pubmed(
                termo=tema,
                max_resultados=int(qtd_artigos),
                ano_inicio=int(ano_inicio),
                ano_fim=int(ano_fim)
            )
            artigos_df = normalizar_artigos(artigos_df)
        except Exception as e:
            st.error(f"Erro ao buscar PubMed: {e}")
            artigos_df = pd.DataFrame()

    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.subheader("Artigos (PubMed)")
    if artigos_df.empty:
        st.info("Nenhum artigo encontrado para o tema no período selecionado.")
    else:
        st.dataframe(
            artigos_df[["titulo", "ano"]].rename(columns={
                "titulo": "Título",
                "ano": "Ano"
            }).head(200),
            use_container_width=True
        )

        st.metric("Total artigos", len(artigos_df))

        if artigos_df["ano"].notna().sum() > 0:
            serie = artigos_df["ano"].dropna().astype(int).value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(6,4))
            serie.plot(kind="bar", ax=ax, color="#003366")
            ax.set_xlabel("Ano")
            ax.set_ylabel("Número de Artigos")
            ax.set_title("Publicações por Ano (PubMed)", fontsize=14, weight="bold", color="#003366")
            ax.grid(axis="y", linestyle="--", alpha=0.7)
            st.pyplot(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------COVID NYTimes -----------------------------
    with st.spinner("Carregando dados NYTimes COVID-19..."):
        try:
            covid_df = get_dados_covid()
        except Exception as e:
            st.error(f"Erro ao carregar dados NYTimes: {e}")
            covid_df = pd.DataFrame()

    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.subheader("Dados epidemiológicos — NYTimes COVID-19 (Estados Unidos)")
    if covid_df.empty:
        covid_periodo = pd.DataFrame()
        resumo_estados = pd.DataFrame()
        st.info("Dados COVID não disponíveis.")
    else:
        col_data = primeira_coluna_existente(covid_df, ["date", "Date", "data", "reported_date"])
        col_cases = primeira_coluna_existente(covid_df, ["cases", "Cases", "casos"])
        col_deaths = primeira_coluna_existente(covid_df, ["deaths", "Deaths", "mortes"])
        col_state = primeira_coluna_existente(covid_df, ["state", "State", "estado"])

        if col_data:
            covid_df.rename(columns={col_data: "data"}, inplace=True)
            covid_df["data"] = pd.to_datetime(covid_df["data"], errors="coerce")
        else:
            st.error("Nenhuma coluna de data encontrada nos dados COVID.")
            covid_df["data"] = pd.NaT

        if col_cases and col_cases != "casos":
            covid_df.rename(columns={col_cases: "casos"}, inplace=True)
        if col_deaths and col_deaths != "mortes":
            covid_df.rename(columns={col_deaths: "mortes"}, inplace=True)
        if col_state and col_state != "estado":
            covid_df.rename(columns={col_state: "estado"}, inplace=True)

        covid_df["casos"] = pd.to_numeric(covid_df.get("casos", pd.NA), errors="coerce")
        covid_df["mortes"] = pd.to_numeric(covid_df.get("mortes", pd.NA), errors="coerce")

        covid_periodo = covid_df[
            (covid_df["data"].dt.year >= int(ano_inicio))
            & (covid_df["data"].dt.year <= int(ano_fim))
        ]

        if covid_periodo.empty:
            resumo_estados = pd.DataFrame()
            st.info("Nenhum dado COVID-19 disponível para o período selecionado.")
        else:
            serie_casos = covid_periodo.groupby("data")["casos"].sum()
            serie_mortes = covid_periodo.groupby("data")["mortes"].sum()
            st.line_chart(pd.DataFrame({"Casos": serie_casos, "Mortes": serie_mortes}))

            if "estado" in covid_periodo.columns:
                resumo_estados = (
                    covid_periodo.groupby("estado")[["casos", "mortes"]]
                    .max()
                    .sort_values("casos", ascending=False)
                )
                st.dataframe(resumo_estados.head(20).rename(columns={
                    "casos": "Casos",
                    "mortes": "Mortes"
                }))
            else:
                resumo_estados = pd.DataFrame()
                st.warning("Coluna de estado não encontrada; mostrando apenas séries agregadas no tempo.")
    st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------Tópicos -----------------------
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.subheader("Tópicos (clusters) — Artigos")

textos_combinados = []
if not artigos_df.empty:
    textos_combinados = [
        f"{row.get('titulo', '')} {row.get('resumo', '')}"
        for _, row in artigos_df.iterrows()
    ]

topicos = []
if textos_combinados:
    try:
        topicos = build_topics(textos_combinados, num_clusters=5, max_caracteristicas=5000)
        
        topicos = [traduzir_termos(t) for t in topicos]

        for idx, t in enumerate(topicos, 1):
            with st.expander(f"Tópico {idx}"):
                st.write(", ".join(t))
    except Exception as e:
        st.warning(f"Não foi possível extrair tópicos: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------- Heurísticas -----------------------
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.subheader("Sinais de oportunidade (heurísticas)")
    lacunas = []
    if not artigos_df.empty and not covid_periodo.empty:
        artigos_por_ano = artigos_df["ano"].dropna().astype(int).value_counts().sort_index()
        covid_por_ano = covid_periodo.groupby(covid_periodo["data"].dt.year)["casos"].sum()

        for ano in sorted(set(artigos_por_ano.index) | set(covid_por_ano.index)):
            qtd_artigos = int(artigos_por_ano.get(ano, 0))
            casos = int(covid_por_ano.get(ano, 0))
            if ano >= int(ano_fim) - 3 and qtd_artigos >= 5 and casos > 100000:
                lacunas.append(f"Ano {ano}: alta produção acadêmica ({qtd_artigos}) com grande carga epidemiológica ({casos} casos).")

    if lacunas:
        for g in lacunas:
            st.write("• ", g)
    else:
        st.caption("Nenhuma oportunidade óbvia detectada com a heurística atual.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------- Relatório -----------------------
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.subheader("Relatório")
    relatorio = gerar_relatorio(tema, ano_inicio, ano_fim, artigos_df, covid_periodo, topicos, lacunas, resumo_estados)
    st.download_button(
        "Baixar relatório (Markdown)",
        data=relatorio.encode("utf-8"),
        file_name=f"relatorio_{datetime.utcnow().date()}_{tema.replace(' ','_')}.md",
        mime="text/markdown"
    )
    pdf_bytes = gerar_pdf(relatorio)
    st.download_button(
        "Baixar relatório (PDF)",
        data=pdf_bytes,
        file_name=f"relatorio_{datetime.utcnow().date()}_{tema.replace(' ','_')}.pdf",
        mime="application/pdf"
    )
    if consentimento:
        registrar_evento(banco, st.session_state.session_id, "journey_done", {"topic": tema, "articles": len(artigos_df), "covid_rows": len(covid_periodo)})
    st.markdown('</div>', unsafe_allow_html=True)
