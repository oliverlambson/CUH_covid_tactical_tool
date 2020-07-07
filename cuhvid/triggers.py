import pandas as pd

def get_rolling_mean(df, columns, no_days, center=False):
    """
    Appends columns for rolling mean of specified columns to df.
    
    Parameters
    ----------
    df : DataFrame
        daily Covid records
    columns : list of String
        columns to calculate rolling means for
    no_days : int
        number of days for rolling window
    centered : bool
        center rolling window
    
    Returns
    -------
    df : Series
        rolling mean of daily Covid admissions

    Example
    -------
    from cuhvid.triggers import get_rolling_mean
    df = get_rolling_mean(
        df, 
        columns=['Admissions'], 
        no_days=no_days.value, 
        center=centered.value
    )
    
    """
    df_rm = df[columns].rolling(no_days, center=center).mean()
    df = df.join(df_rm, rsuffix='_rm')
    return df