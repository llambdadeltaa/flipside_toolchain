import pandas as pd

def read_dataframe(url: str, time_column: str = 'DT', utc_time: bool = True):
    df = pd.read_json(url)
    df.loc[time_column] = pd.to_datetime(df[time_column], utc=True)
    return df