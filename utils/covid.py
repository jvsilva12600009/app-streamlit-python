import pandas as pd

COVID_DATA_URL = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"

def get_dados_covid() -> pd.DataFrame:
    
    df = pd.read_csv(COVID_DATA_URL, parse_dates=["date"])
    
    df = df.rename(columns={
        "data": "data",
        "estado": "estado",
        "caso": "casos",
        "obitos": "obitos"
    })
    
    return df
