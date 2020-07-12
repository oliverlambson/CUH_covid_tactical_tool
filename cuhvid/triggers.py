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

def evaluate_triggers(df, df_ward_rank, admissions, net_intake, free_beds_min, free_beds_max, ward_changeup_time, ward_changedown_time):
    # this should be moved to original ward function
    df_ward_rank = df_ward_rank.set_index('AB_change_no')
    # df_ward_rank.loc[-1] = {
    #     'id': 'start', 
    #     'A_color': '-', 
    #     'B_color': '-', 
    #     'R_tot': , 
    #     'A_tot': , 
    #     'G_tot': , 
    #     'rank': -1, 
    #     'B_no_beds': 0
    # }

    # init triggers
    df['trigger_admissions'] = df['y_gen_rm'] >= admissions
    df['trigger_net_intake'] = df['net_intake_gen_rm'] <= net_intake
    # df['trigger_free_beds_min'] = (df['GIM_R_beds_avail'] <= free_beds_min) | (df['GIM_A_beds_avail'] <= free_beds_min)
    df['trigger_free_beds_min'] = (df['GIM_R_beds_avail'] <= free_beds_min) # only red
    df['trigger_free_beds_max'] = False

    # for now only use no. free beds as trigger
    df['trigger_up'] = df['trigger_free_beds_min']
    df['trigger_down'] = df['trigger_free_beds_max']

    # init ward config no. on days
    df['config_AB_change_no'] = -1

    # init no. wards opening in prog
    df['no_up_in_prog'] = 0
    df['no_down_in_prog'] = 0

    # init index list
    idx_list = df.index[df['trigger_up']] # starting at AB base so don't check trig down here
    
    while idx_list.any():
        change_flag = False
        idx = idx_list[0]

        if df.loc[idx, 'trigger_up']:
            # increment ward config no. on days
            new_AB_change_no = df.loc[idx+ward_changeup_time, 'config_AB_change_no'] + 1

            if new_AB_change_no <= (df_ward_rank.index.max() - df.loc[idx, 'no_up_in_prog']):
                change_flag = True
        # mark ward opening duration
        df.loc[idx:idx+ward_changeup_time, 'no_up_in_prog'] += 1
                df.loc[idx+ward_changeup_time:, 'config_AB_change_no'] = new_AB_change_no

        elif df.loc[idx, 'trigger_down']:
        # increment ward config no. on days
            new_AB_change_no = df.loc[idx+ward_changeup_time, 'config_AB_change_no'] - 1

            if new_AB_change_no >= (df_ward_rank.index.min() - 1 + df.loc[idx, 'no_down_in_prog']):
                change_flag = True
                # mark ward closing duration
                df.loc[idx:idx+ward_changedown_time, 'no_down_in_prog'] += 1
                df.loc[idx+ward_changedown_time:, 'config_AB_change_no'] = new_AB_change_no

        if change_flag:
        # update bed totals
        new_R_tot = df_ward_rank.loc[new_AB_change_no, 'R_tot']
        df.loc[idx+ward_changeup_time:, 'GIM_R_beds'] = new_R_tot

        new_A_tot = df_ward_rank.loc[new_AB_change_no, 'A_tot']
        df.loc[idx+ward_changeup_time:, 'GIM_A_beds'] = new_A_tot

        # update available beds
        df.loc[idx:, 'GIM_R_beds_avail'] = df.loc[idx:, 'GIM_R_beds'] - df.loc[idx:, 'GIM_R_gen']
        df.loc[idx:, 'GIM_A_beds_avail'] = df.loc[idx:, 'GIM_A_beds'] - df.loc[idx:, 'GIM_A_gen']

        # re-evaluate triggers
            # df.loc[idx:, 'trigger_free_beds_min'] = (df.loc[idx:, 'GIM_R_beds_avail'] <= free_beds_min) | (df.loc[idx:, 'GIM_A_beds_avail'] <= free_beds_min)
            df.loc[idx:, 'trigger_free_beds_min'] = (df.loc[idx:, 'GIM_R_beds_avail'] <= free_beds_min) # only red
        df.loc[idx:, 'trigger_up'] = df.loc[idx:, 'trigger_free_beds_min']
            # df.loc[idx:, 'trigger_free_beds_max'] = (df.loc[idx:, 'GIM_R_beds_avail'] >= free_beds_max) | (df.loc[idx:, 'GIM_A_beds_avail'] >= free_beds_max)
            df.loc[idx:, 'trigger_free_beds_max'] = (df.loc[idx:, 'GIM_R_beds_avail'] >= free_beds_max) # only red
            df.loc[idx:, 'trigger_down'] = df.loc[idx:, 'trigger_free_beds_max']

        # update index list
        idx_list = df.index[(df['trigger_up'] | df['trigger_down']) & (df.index > idx)]


    return df