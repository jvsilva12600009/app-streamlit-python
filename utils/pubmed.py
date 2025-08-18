import requests
import pandas as pd
from typing import List, Dict


def get_dados_pubmed(termo: str, max_resultados: int = 50, ano_inicio: int = 2000, ano_fim: int = 2025) -> pd.DataFrame:
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    url_busca = (
        f"{base_url}esearch.fcgi?db=pubmed"
        f"&term={termo}"
        f"&retmax={max_resultados}"
        f"&retmode=json"
        f"&datetype=pdat"
        f"&mindate={ano_inicio}"
        f"&maxdate={ano_fim}"
    )
    resp_busca = requests.get(url_busca)
    dados_busca = resp_busca.json()
    ids = dados_busca.get("esearchresult", {}).get("idlist", [])

    if not ids:
        return pd.DataFrame(columns=["pmid", "titulo", "ano"])
s
    ids_str = ",".join(ids)
    url_detalhes = f"{base_url}esummary.fcgi?db=pubmed&id={ids_str}&retmode=json"
    resp_detalhes = requests.get(url_detalhes)
    dados_detalhes = resp_detalhes.json()

    artigos: List[Dict] = []
    for pmid, detalhes in dados_detalhes.get("result", {}).items():
        if pmid == "uids":
            continue

        titulo = detalhes.get("title", "").strip()
        data_pub = detalhes.get("pubdate", "")

      
        ano = None
        if data_pub:
            ano = data_pub.split(" ")[0]  

        artigos.append({
            "pmid": pmid,
            "titulo": titulo if titulo else "Sem título",
            "ano": ano if ano else "",
        })

    return pd.DataFrame(artigos)
