import pandas as pd

def read_dataframe(url: str, time_column: str = 'DT', utc_time: bool = True, sort_date: bool = True):
    df = pd.read_json(url)
    df.loc[time_column] = pd.to_datetime(df[time_column], utc=utc_time)
    df.sort_values(by=time_column, ascending=False, inplace=True)
    return df