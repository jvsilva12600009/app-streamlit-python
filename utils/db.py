import os
from datetime import datetime
from typing import Tuple

from pymongo import MongoClient
import streamlit as st


def get_configuracao(chave: str, padrao: str | None = None):
    """Obtém configuração do secrets.toml ou de variáveis de ambiente."""
    try:
        return st.secrets[chave]
    except Exception:
        return os.getenv(chave, padrao)


MONGODB_URI = get_configuracao("MONGODB_URI")
NOME_BANCO = get_configuracao("DB_NAME", "saudeja")


@st.cache_resource(show_spinner=False)
def get_db() -> Tuple[MongoClient, object]:
    """
    Retorna conexão e banco de dados MongoDB.
    A conexão é cacheada para evitar múltiplas instâncias.
    """
    if not MONGODB_URI:
        st.error("MONGODB_URI não configurada. Defina em .streamlit/secrets.toml ou variáveis de ambiente.")
        st.stop()

    cliente = MongoClient(MONGODB_URI, tls=True, uuidRepresentation="standard")
    return cliente, cliente[NOME_BANCO]


def registrar_evento(banco, id_sessao: str, acao: str, dados: dict | None = None):
    """
    Registra evento no banco (ex: cliques, ações do usuário).
    Não interrompe a interface caso o log falhe.
    """
    try:
        if not st.session_state.get("consent_logging", True):
            return

        banco["eventos"].insert_one({
            "id_sessao": id_sessao,
            "acao": acao,
            "dados": dados or {},
            "timestamp": datetime.utcnow(),
            "versao_app": "1.0.0"
        })
    except Exception as erro:
        # não interrompe a UI por falha de log
        st.sidebar.warning(f"")
