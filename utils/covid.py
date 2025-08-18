import pandas as pd

COVID_DATA_URL = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"

def get_dados_covid() -> pd.DataFrame:
    """
    Carrega os dados de COVID-19 (NYTimes).
    Retorna DataFrame com colunas: data, estado, casos, obitos
    """
    df = pd.read_csv(COVID_DATA_URL, parse_dates=["date"])
    
    df = df.rename(columns={
        "data": "data",
        "estado": "estado",
        "caso": "casos",
        "obitos": "obitos"
    })
    
    return df
