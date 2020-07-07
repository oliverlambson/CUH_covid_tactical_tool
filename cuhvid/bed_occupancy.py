import numpy as np
import pandas as pd

def get_bed_occupancy(df, LoS_GIM, LoS_ICU, frac_ICU):
    """
    Generates GIM & ICU bed occupancy from daily covid admissions.
    
    Parameters
    ----------
    df : DataFrame
        admissions dataframe output of get_admissions()
    LoS_GIM : int
        ave. length of stay for Covid+ GIM patient
    LoS_ICU : int
        ave. length of stay for Covid+ ICU patient
    frac_ICU : float
        fraction of all admissions that are ICU patients
    
    Returns
    -------
    Day : list of int
        day number
    y : list of float
        gamma value
    y_g : list of float
        gamma value with random variance according to standard deviation
    y_l : list of float
        lower bound for daily gamma value
    y_u : list of float
        upper bound for daily gamma value
    GIM : list of int
        number of beds required for fitted curve of Covid+ GIM patients
    ICU : list of int
        number of beds required for fitted curve Covid+ ICU patients
    GIM_gen : list of int
        number of beds required for generated series Covid+ GIM patients
    ICU_gen : list of int
        number of beds required for generated series Covid+ ICU patients
    """
    df['GIM'] = ((1-frac_ICU)*df.y).rolling(LoS_GIM, min_periods=0).sum()
    df['ICU'] = ((frac_ICU)*df.y).rolling(LoS_ICU, min_periods=0).sum()
    df['tot_occ'] = df['GIM'] + df['ICU']
    df['net_intake'] = df['tot_occ'].diff()
    
    df['GIM_gen'] = np.round((1-frac_ICU)*df.y_gen).rolling(LoS_GIM, min_periods=0).sum()
    df['ICU_gen'] = np.round((frac_ICU)*df.y_gen).rolling(LoS_ICU, min_periods=0).sum()
    df['tot_occ_gen'] = df['GIM_gen'] + df['ICU_gen']

    df['net_intake_gen'] = df['tot_occ_gen'].diff()
    
    return df