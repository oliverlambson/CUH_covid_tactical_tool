import numpy as np
import pandas as pd
import scipy.stats as st

def _stddev(mean_adm, sd_coeff, sd_const):
    return sd_coeff * mean_adm + sd_const

def get_admissions(alpha, loc, scale, peak_adm, sd_coeff, sd_const, n_days=92):
    """
    Generates wave of daily covid admissions.
    
    A gamma distribution function is scaled to use number of days on the x-axis
    and number of daily admissions of the y-axis.
    
    Noise is added to the signal according to a linear relationship between number
    of admissions and the corresponding standard deviation.
    
    Parameters
    ----------
    alpha : float
        gamma alpha
    loc : float
        gamma location
    scale : float
        gamma scale
    peak_adm : int
        gamma peak no. daily covid+ admissions
    sd_coeff : float
        coefficient of linear regression of mean admissions vs std dev.
    df_const : float
        constant of linear regression of mean admissions vs std dev.
    n_days : int, default 92
        number of days for calculation (no elements)
    
    Returns
    -------
    t : list of int
        day number
    y : list of float
        gamma value
    y_g : list of float
        gamma value with random variance according to standard deviation
    y_l : list of float
        lower bound for daily gamma value
    y_u : list of float
        upper bound for daily gamma value
        
    TODO
    ----
    Refactor to return dataframe
    """
    t = np.arange(0, n_days, 1)
    
    y = st.gamma.pdf(t, alpha, loc=loc, scale=scale)
    y = y*peak_adm/np.max(y)
    
    sd = _stddev(mean_adm=y, sd_coeff=sd_coeff, sd_const=sd_const)
    
    y_noise = st.norm.rvs(size=len(y)) * sd
    
    y_g = np.round(np.clip(y + y_noise, a_min=0, a_max=None)).astype(np.int)
    
    y_l = np.clip(y - 1.96*sd, a_min=0, a_max=None)
    y_u = np.clip(y + 1.96*sd, a_min=0, a_max=None)
    
    return pd.DataFrame(data={'y':y, 'y_gen':y_g, 'y_lower':y_l, 'y_upper':y_u}, index=pd.Series(t, name='Day'))