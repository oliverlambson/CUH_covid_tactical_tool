import pandas as pd

def get_color_numbers(df, scenario, wards=False, beds=False):
    """
    Gets summary figures for number of wards and number of beds by ward color for a given scenario.
    
    Parameters
    ----------
    df : DataFrame
        CUH wards
    scenario : string
        scenario A, B, or C
    wards : bool
        wards
    beds : bool
        beds
    
    Returns
    -------
    dfr : DataFrame
        number of wards and number of beds grouped by ward color for given scenario 

    Example
    -------
    from cuhvid.wards import get_bed_numbers
    get_bed_numbers(df, 'A')
    
    """
    if not(wards | beds):
        raise Exception('No columns to summarise.')

    # all_colors = pd.unique(df_wards[['A_color', 'B_color', 'C_color']].values.ravel('K'))
    all_colors = ['R', 'A', 'G', 'excl.']

    agg_cols = {}
    if wards:
        agg_cols['Wards'] = (f'{scenario}_no_beds', 'count')
    if beds:
        agg_cols['Beds'] = (f'{scenario}_no_beds', 'sum')

    dfr = (
        df.groupby(by=f'{scenario}_color')
            .agg(**agg_cols)
            .reindex(all_colors, fill_value=0)
            .rename_axis(None)
    )

    return dfr

from cuhvid.wards2 import Wards
def get_ward_beds(df_gen):
    w = Wards()
    df_Wards = w.df

    d_A = get_color_numbers(df_Wards, 'A', beds=True)

    # initialise to base setup
    df_gen['GIM_R_beds'] = d_A.loc['R', 'Beds']
    df_gen['GIM_A_beds'] = d_A.loc['A', 'Beds']
    df_gen['GIM_G_beds'] = d_A.loc['G', 'Beds']

    # TODO: logic here to calculate no. beds remaining & ward opening
    # for now: no ward changeovers
    df_gen['GIM_R_beds_avail'] = df_gen['GIM_R_beds'] - df_gen['GIM_R_gen']
    df_gen['GIM_A_beds_avail'] = df_gen['GIM_A_beds'] - df_gen['GIM_A_gen']

    return df_gen