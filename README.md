#  Site Sobre Saúde — Python + Streamlit

[![Deploy Status](https://img.shields.io/badge/deploy-streamlit-success?style=flat-square)](https://appsaude.streamlit.app/)

Uma aplicação web interativa sobre temas relacionados à saúde, construída com **Python** e **Streamlit**, consumindo **APIs públicas** e utilizando **MongoDB Atlas** como banco de dados.

---

##  Demonstração

Acesse o aplicativo ao vivo clicando no link abaixo:  
 **[App Saúde Online](https://appsaude.streamlit.app/)**


---

## Tecnologias utilizadas

-  **Python**
-  **Streamlit** — framework rápido e intuitivo para criação de apps interativos em Python
-  **MongoDB Atlas** — banco de dados em nuvem
-  **APIs públicas** — dados do PubMed e COVID-19 (NYTimes)
-  **deep_translator** — para tradução automática de artigos

---
## Como conectar ao banco de dados
- Para conectar ao banco de dados basta inserir a conexão com o MongoDB Atlas, o nome do usuario e a senha, o Cluster e o nome da database

## Estrutura
```
├── .streamlit/           ← Configurações do Streamlit
├── app.py                ← Arquivo principal com a lógica do app
├── requirements.txt      ← Lista de dependências Python
├── utils/                ← Funções auxiliares (API, DB, tradução etc.)
└── prints/               ← Prints de telas usados no README
```

---

## Funcionalidades

-  Buscar artigos científicos do **PubMed**
-  Traduzir automaticamente os artigos para **português**
-  Visualizar **dados epidemiológicos** de COVID-19 (NYTimes)
-  Agrupar artigos por **tópicos (clusters)**
-  Gerar relatórios em **Markdown** ou **PDF**
-  Opção de salvar interações (anonimamente)


## Exemplo de uso 

Pesquisa de artigos

1 - Abra o app.

2 - Digite “tratamento de diabetes” como tema.

3 - Escolha o período de 2015 a 2025.

4 - Defina a quantidade de artigos (50).

5 - Clique em Rodar jornada.

6 - O sistema exibirá:

7 - Títulos traduzidos

8 - Periódicos

9 - Ano de publicação

10 - Gráfico epidemiológico COVID-19





