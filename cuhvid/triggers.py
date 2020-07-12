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
    df['no_wards_up_in_prog'] = 0
    df['no_wards_down_in_prog'] = 0

    # init no. wards opening in prog
    # df['wards_up_in_prog_id'] = [[] for _ in range(len(df))]
    df['wards_up_in_prog_id'] = ''
    # df['wards_down_in_prog_id'] = [[] for _ in range(len(df))]
    df['wards_down_in_prog_id'] = ''

    # init no. beds opening in prog
    df['no_beds_up_in_prog'] = 0
    df['no_beds_down_in_prog'] = 0

    # init index list
    idx_list = df.index[df['trigger_up']] # starting at AB base so don't check trig down here
    
    while idx_list.any():
        change_flag = False
        idx = idx_list[0]

        if df.loc[idx, 'trigger_up']:
            # increment ward config no. on days
            new_AB_change_no = df.loc[idx, 'config_AB_change_no'] + df.loc[idx, 'no_wards_up_in_prog'] + 1
            
            change_flag = (
                (new_AB_change_no <= df_ward_rank.index.max()) & # wards left to open
                (df.loc[idx, 'GIM_R_beds_avail'] + df.loc[idx, 'no_beds_up_in_prog'] <= free_beds_min) # need beds after staged are changed
            )
            if change_flag:
                # mark ward opening duration
                idx_end = int(min(idx + ward_changeup_time, df.index.max()))

                df.loc[idx:idx_end-1, 'no_wards_up_in_prog'] += 1

                new_ID = df_ward_rank.loc[new_AB_change_no, 'id']
                df.loc[idx:idx_end-1, 'wards_up_in_prog_id'] += f'{new_ID}, '

                df.loc[idx:idx_end-1, 'no_beds_up_in_prog'] += df_ward_rank.loc[new_AB_change_no, 'B_no_beds']

                df.loc[idx_end:, 'config_AB_change_no'] = new_AB_change_no
            
        elif df.loc[idx, 'trigger_down']:
            # increment ward config no. on days
            new_AB_change_no = df.loc[idx, 'config_AB_change_no'] - df.loc[idx, 'no_wards_down_in_prog'] - 1

            change_flag = (
                (new_AB_change_no >= df_ward_rank.index.min()) & # wards left to close
                (df.loc[idx, 'GIM_R_beds_avail'] - df.loc[idx, 'no_beds_down_in_prog'] >= free_beds_max) # need beds after staged are changed
            )
            if change_flag:
                # mark ward closing duration
                idx_end = int(min(idx + ward_changedown_time, df.index.max()))
                
                df.loc[idx:idx_end-1, 'no_wards_down_in_prog'] += 1

                new_ID = df_ward_rank.loc[new_AB_change_no, 'id']
                df.loc[idx:idx_end-1, 'wards_down_in_prog_id'] += f'{new_ID}, '

                df.loc[idx:idx_end-1, 'no_beds_down_in_prog'] += df_ward_rank.loc[new_AB_change_no, 'B_no_beds']
                df.loc[idx_end:, 'config_AB_change_no'] = new_AB_change_no

        if change_flag:
            # update bed totals
            new_R_tot = df_ward_rank.loc[new_AB_change_no, 'R_tot']
            df.loc[idx_end:, 'GIM_R_beds'] = new_R_tot

            new_A_tot = df_ward_rank.loc[new_AB_change_no, 'A_tot']
            df.loc[idx_end:, 'GIM_A_beds'] = new_A_tot

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