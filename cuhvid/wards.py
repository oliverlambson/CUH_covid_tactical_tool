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
def get_ward_beds(df):
    w = Wards()
    df_Wards = w.df

    df_A = get_color_numbers(df_Wards, 'A', beds=True)

    # initialise to base setup
    df['GIM_R_beds'] = df_A.loc['R', 'Beds']
    df['GIM_A_beds'] = df_A.loc['A', 'Beds']
    df['GIM_G_beds'] = df_A.loc['G', 'Beds']

    # TODO: logic here to calculate no. beds remaining & ward opening
    # for now: no ward changeovers
    df['GIM_R_beds_avail'] = df['GIM_R_beds'] - df['GIM_R_gen']
    df['GIM_A_beds_avail'] = df['GIM_A_beds'] - df['GIM_A_gen']

    return df


from cuhvid.wards2 import Wards
def get_ward_change_rank():
    """
    Gets a dataframe summarising the ward changeover order & the corresponding number of beds available after each change.
    """
    w = Wards()
    df_Wards = w.df

    df_AB = w.get_AB_wards()
    df_AB = df_AB[['id', 'AB_change_no', 'A_color', 'B_color', 'A_no_beds', 'B_no_beds']].sort_values(by='AB_change_no')

    df_A = get_color_numbers(df_Wards, 'A', beds=True)

    # ..... temporary sorting .....
    rank_order = {
        'GR': 0,
        'AR': 1,
        'GA': 2,
    }
    df_AB['rank'] = df_AB['A_color'] + df_AB['B_color']
    df_AB['rank'] = df_AB['rank'].map(rank_order)

    df_AB = df_AB.sort_values(by=['rank', 'B_no_beds'], ascending=[True, False])
    df_AB['AB_change_no'] = range(0, len(df_AB['AB_change_no']), 1)
    # ..... end temporary sorting .....

    all_colors = ['R', 'A', 'G', 'excl.']
    for color in all_colors:
        df_AB[f'delta_{color}'] = (
            df_AB.apply(lambda s : -s.A_no_beds if color == s.A_color else 0, axis='columns') 
            + df_AB.apply(lambda s : s.B_no_beds if color == s.B_color else 0, axis='columns')
        )
        df_AB[f'{color}_tot'] = df_AB[f'delta_{color}'].cumsum() + df_A.loc[color, 'Beds']

    df_summary = df_AB[['AB_change_no', 'id', 'A_color', 'B_color', 'R_tot', 'A_tot', 'G_tot', 'rank', 'B_no_beds']]

    df_summary = df_summary.append({
        'AB_change_no': -1,
        'id': 'start',
        'A_color': '-',
        'B_color': '-',
        'R_tot': df_A.loc['R', 'Beds'],
        'A_tot': df_A.loc['A', 'Beds'],
        'G_tot': df_A.loc['G', 'Beds'],
        'rank': -1,
        'B_no_beds': 0
    }, ignore_index=True)

    df_summary = df_summary.sort_values(by='AB_change_no')
    df_summary.loc[:, 'B_no_beds'] = df_summary.loc[:, 'B_no_beds'].shift(-1, fill_value=0)

    return df_summary