import pandas as pd
import numpy as np


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

# REFACTORED BELOW

def _delta_beds(s, color):
    if s.i_color == color:
        return -s.i_no_beds
    elif s.ii_color == color:
        return s.ii_no_beds
    else:
        return 0


def get_ward_change_rank2(bed_size_ascending = False):
    # --------------------------------------------
    # --------------- Read-in data ---------------
    # --------------------------------------------
    path = '/Users/oliverlambson/GitHub/ISMM/CUH_covid_tactical_tool/Data/bed_plan.xlsx'
    df = pd.read_excel(path, sheet_name='v13')

    # fill NaNs in important columns
    df.loc[:, df.columns.str.contains('_priority')] = df.loc[:, df.columns.str.contains('_priority')].fillna(0)
    df.loc[:, df.columns.str.contains('_no_beds')] = df.loc[:, df.columns.str.contains('_no_beds')].fillna(0)

    # drop unnecessary columns
    df = df.drop(columns=df.columns[df.columns.str.contains('no_beds_')])
    df = df.drop(columns=['division'])

    # raise error if ward changes A->B and B->C
    if len(df[df.AB_change & df.BC_change]) != 0:
        raise Exception('Cannot handle changing same ward twice (from scenario A to B and scenario B to C)')

    # -----------------------------------------------------------
    # --------------- Get configuration summaries ---------------
    # -----------------------------------------------------------
    all_colors = ['R', 'A', 'G']
    scenarios = ['A', 'B', 'C']

    multi_index = pd.MultiIndex.from_product([scenarios, all_colors], names=['scenario', 'color'])
    df_summary = pd.DataFrame(
        np.zeros((len(scenarios)*len(all_colors),2)).astype(int), 
        index=multi_index, 
        columns=['Wards', 'Beds']
    )

    for scenario in scenarios:
        agg_cols = {}
        agg_cols['Wards'] = (f'{scenario}_no_beds', 'count')
        agg_cols['Beds'] = (f'{scenario}_no_beds', 'sum')

        dfr = (
            df.groupby(by=f'{scenario}_color')
                .agg(**agg_cols)
                .reindex(all_colors, fill_value=0)
                .rename_axis(None)
        )
        
        df_summary.loc[scenario, :] = dfr.values.astype(int)

    # --------------------------------------------------------
    # --------------- Generate ward rank table ---------------
    # --------------------------------------------------------
    df_AB = df.loc[df.AB_change, ['block', 'ID',
                                'A_color', 'A_no_beds', 'AB_priority',
                                'B_color', 'B_no_beds']]
    df_AB = df_AB.rename(columns={
        'A_color': 'i_color',
        'A_no_beds': 'i_no_beds',
        'AB_priority': 'priority',
        'B_color': 'ii_color',
        'B_no_beds': 'ii_no_beds',
    })
    df_AB['scenario'] = 'B'

    df_BC = df.loc[df.BC_change, ['block', 'ID',
                                'B_color', 'B_no_beds', 'BC_priority',
                                'C_color', 'C_no_beds']]
    df_BC = df_BC.rename(columns={
        'B_color': 'i_color',
        'B_no_beds': 'i_no_beds',
        'BC_priority': 'priority',
        'C_color': 'ii_color',
        'C_no_beds': 'ii_no_beds',
    })
    df_BC['scenario'] = 'C'

    df_rank = pd.concat([df_AB, df_BC])

    # --------------- Add bed deltas ---------------
    df_rank['dR_no_beds'] = df_rank.apply(_delta_beds, axis='columns', color='R')
    df_rank['dA_no_beds'] = df_rank.apply(_delta_beds, axis='columns', color='A')
    df_rank['dG_no_beds'] = df_rank.apply(_delta_beds, axis='columns', color='G')

    # --------------- Add changeover type rank ---------------
    color_rank = {
        'GR': 0,
        'AR': 1,
        'GA': 2,
    }
    df_rank['color_rank'] = df_rank['i_color'] + df_rank['ii_color']
    df_rank['color_rank'] = df_rank['color_rank'].map(color_rank)

    df_rank = df_rank.sort_values(by=['scenario', 'priority', 'color_rank', 'dR_no_beds', 'dA_no_beds'], 
                            ascending=[True, True, True, bed_size_ascending, bed_size_ascending])
    df_rank['rank'] = range(1, len(df_rank)+1)

    # --------------- Reorder columns ---------------
    df_rank = df_rank[[
        'rank', 'block', 'ID', 'scenario', 'priority', 'color_rank',
        'i_color', 'ii_color', 'i_no_beds', 'ii_no_beds',
        'dR_no_beds', 'dA_no_beds', 'dG_no_beds'
    ]]

    # --------------- Add initial state ---------------
    df_rank = df_rank.append({
        'rank': 0,
        'scenario': 'A',
        'priority': 0,
        'color_rank': 0,
        'dR_no_beds': 0,
        'dA_no_beds': 0,
        'dG_no_beds': 0
    }, ignore_index=True).fillna('').sort_values(by='rank').set_index('rank')

    # --------------- Add no beds column ---------------
    for c in ['R', 'A', 'G']:
        df_rank[f'{c}_no_beds'] = df_summary.loc[('A', c),'Beds'] + df_rank[f'd{c}_no_beds'].cumsum()

    # --------------- Add total no beds column ---------------
    df_rank['total_no_beds'] = df_rank['R_no_beds'] + df_rank['A_no_beds'] + df_rank['G_no_beds']

    # --------------- Convert data types ---------------
    df_rank = df_rank.astype({
        'priority': int,
        'color_rank': int,
        'dR_no_beds': int,
        'dA_no_beds': int,
        'dG_no_beds': int,
        'R_no_beds': int,
        'A_no_beds': int,
        'G_no_beds': int
    })

    # --------------------------------------
    # --------------- Return ---------------
    # --------------------------------------
    return df_rank