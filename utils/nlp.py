import re
import unicodedata
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.cluster import KMeans
from nltk.corpus import stopwords
import nltk


try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")



PALAVRAS_PARADAS = set(stopwords.words("portuguese")).union(ENGLISH_STOP_WORDS)




def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r"[^a-z0-9\s]", " ", text) 
    return text.strip()


def build_topics(
    textos: List[str],
    n_clusters: int = 5,
    num_clusters: int | None = None,   
    max_caracteristicas: int = 5000,
) -> List[List[str]]:
    if not textos:
        return []
    if num_clusters is not None:
        n_clusters = num_clusters
    vetor = TfidfVectorizer(
        max_features=max_caracteristicas,
        stop_words=list(PALAVRAS_PARADAS),
        preprocessor=normalize,
    )
    X = vetor.fit_transform(textos)
    n_clusters = min(n_clusters, X.shape[0])
    if n_clusters < 2:
        return []
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    kmeans.fit(X)
    ordem_centroides = kmeans.cluster_centers_.argsort()[:, ::-1]
    termos = vetor.get_feature_names_out()
    topicos = []
    for i in range(n_clusters):
        termos_topico = [termos[ind] for ind in ordem_centroides[i, :10]]
        topicos.append(termos_topico)

    return topicos
