import json
from typing import List, Dict
import requests
import streamlit as st

@st.cache_data(show_spinner=False)
def buscar_artigos_pubmed(
    termo: str,
    ano_inicio: int,
    ano_fim: int,
    limite: int = 50
) -> List[str]:
    
    consulta = f"{termo} AND ({ano_inicio}:{ano_fim}[dp])"

    resposta = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={
            "db": "pubmed",
            "retmode": "json",
            "term": consulta,
            "retmax": limite,
            "sort": "pub date",
        },
        timeout=30
    )
    resposta.raise_for_status()
    dados = resposta.json()

    return dados.get("esearchresult", {}).get("idlist", [])


@st.cache_data(show_spinner=False)
def get_detalhes_pubmed(id_artigos: List[str]) -> List[Dict]:
    
    if not id_artigos:
        return []

    resposta = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(id_artigos),
        },
        timeout=30
    )
    resposta.raise_for_status()
    resultados = resposta.json().get("result", {})

    artigos = []
    for pid in resultados.get("uids", []):
        item = resultados.get(pid, {})
        artigos.append({
            "id_pubmed": pid,
            "titulo": item.get("title"),
            "revista": item.get("fulljournalname") or item.get("source"),
            "data_publicacao": item.get("pubdate"),
            "autores": ", ".join([a.get("name", "") for a in item.get("authors", [])]),
            "resumo": item.get("elocationid") or "",
        })

    return artigos


@st.cache_data(show_spinner=False)
def buscar_patentes(
    termo: str,
    ano_inicio: int,
    ano_fim: int,
    limite: int = 50
) -> List[Dict]:
   
    
    consulta = {
        "_and": [
            {"_text_any": {"patent_title": termo}},
            {"_gte": {"patent_date": f"{ano_inicio}-01-01"}},
            {"_lte": {"patent_date": f"{ano_fim}-12-31"}},
        ]
    }

    campos = [
        "patent_number", "patent_title", "patent_date",
        "assignees.organization", "inventors.country"
    ]

    resposta = requests.get(
        "https://api.patentsview.org/patents/query",
        params={
            "q": json.dumps(consulta),
            "f": ",".join(campos),
            "o": json.dumps({"per_page": min(limite, 100)}),
        },
        timeout=30
    )
    resposta.raise_for_status()
    dados = resposta.json()

    patentes = []
    for p in dados.get("patents", []):
        titulares = p.get("assignees", [])
        inventores = p.get("inventors", [])

        patentes.append({
            "numero_patente": p.get("patent_number"),
            "titulo_patente": p.get("patent_title"),
            "data_patente": p.get("patent_date"),
            "titulares": ", ".join({
                (a.get("organization") or "").strip()
                for a in titulares if a.get("organization")
            }),
            "paises_inventores": ", ".join(sorted({
                i.get("country") for i in inventores if i.get("country")
            })),
        })

    return patentes
