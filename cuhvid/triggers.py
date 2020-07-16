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
    # init beds
    df['GIM_R_beds'] = df_ward_rank.loc[0, 'R_no_beds']
    df['GIM_A_beds'] = df_ward_rank.loc[0, 'A_no_beds']
    df['GIM_G_beds'] = df_ward_rank.loc[0, 'G_no_beds']

    # TODO: logic here to calculate no. beds remaining & ward opening
    # for now: no ward changeovers
    df['GIM_R_beds_avail'] = df['GIM_R_beds'] - df['GIM_R_gen']
    df['GIM_A_beds_avail'] = df['GIM_A_beds'] - df['GIM_A_gen']
    
    # init triggers
    # ..... admissions (up) ......
    # df['trigger_admissions'] = (df['y_gen_rm'] >= admissions) & (df['y_gen_rm'].shift() < admissions) # rolling mean trigger cross detection
    df['trigger_admissions'] = df['y_gen_rm'].rolling(3).apply(lambda s: s.gt(admissions).all()).fillna(0).astype(bool)
    df['trigger_admissions'] = (df['trigger_admissions'] - df['trigger_admissions'].shift()).fillna(0)
    df.loc[df['trigger_admissions'] != 1, 'trigger_admissions'] = 0
    df['trigger_admissions'] = df['trigger_admissions'].astype(bool)
    
    # ..... net intake (down) ......
    df['trigger_net_intake'] = df['net_intake_gen_rm'].rolling(5).apply(lambda s: s.lt(net_intake).all()).fillna(0).astype(bool)
    df['trigger_net_intake'] = (df['trigger_net_intake'] - df['trigger_net_intake'].shift()).fillna(0)
    df.loc[df['trigger_net_intake'] != 1, 'trigger_net_intake'] = 0
    df['trigger_net_intake'] = df['trigger_net_intake'].astype(bool)

    # df['trigger_free_beds_min'] = (df['GIM_R_beds_avail'] <= free_beds_min) | (df['GIM_A_beds_avail'] <= free_beds_min)
    df['trigger_free_beds_min'] = (df['GIM_R_beds_avail'] <= free_beds_min) # only red
    df['trigger_free_beds_max'] = False

    # for now only use no. free beds as trigger
    df['trigger_up'] = df['trigger_free_beds_min'] | df['trigger_admissions'] # use trigger admissions too
    df['trigger_down'] = df['trigger_free_beds_max'] | df['trigger_net_intake'] # use trigger net intake too

    # init ward config no. on days
    df['config_rank'] = 0

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
            new_rank = df.loc[idx, 'config_rank'] + df.loc[idx, 'no_wards_up_in_prog'] + 1
            
            change_flag = (
                (new_rank <= df_ward_rank.index.max()) # wards left to open or trigger up signal
                & (
                    (df.loc[idx, 'GIM_R_beds_avail'] + df.loc[idx, 'no_beds_up_in_prog'] <= free_beds_min) # need beds after staged are changed
                    | (df.loc[idx, 'trigger_admissions'])
                )
            )
            if change_flag:
                # mark ward opening duration
                idx_end = int(min(idx + ward_changeup_time, df.index.max()))

                df.loc[idx:idx_end-1, 'no_wards_up_in_prog'] += 1

                new_ID = df_ward_rank.loc[new_rank, 'ID']
                df.loc[idx:idx_end-1, 'wards_up_in_prog_id'] += f'{new_ID}, '

                df.loc[idx:idx_end-1, 'no_beds_up_in_prog'] += df_ward_rank.loc[new_rank, 'ii_no_beds']

                df.loc[idx_end:, 'config_rank'] = new_rank
            
        elif df.loc[idx, 'trigger_down']:
            # increment ward config no. on days
            new_rank = df.loc[idx, 'config_rank'] - df.loc[idx, 'no_wards_down_in_prog'] - 1

            change_flag = (
                (new_rank >= df_ward_rank.index.min()) # wards left to close
                & (
                    (df.loc[idx, 'GIM_R_beds_avail'] - df.loc[idx, 'no_beds_down_in_prog'] >= free_beds_max) # need beds after staged are changed
                    | (df.loc[idx, 'trigger_net_intake'])
                )
            )
            if change_flag:
                # mark ward closing duration
                idx_end = int(min(idx + ward_changedown_time, df.index.max()))
                
                df.loc[idx:idx_end-1, 'no_wards_down_in_prog'] += 1

                new_ID = df_ward_rank.loc[new_rank+1, 'ID']
                df.loc[idx:idx_end-1, 'wards_down_in_prog_id'] += f'{new_ID}, '

                df.loc[idx:idx_end-1, 'no_beds_down_in_prog'] += df_ward_rank.loc[new_rank+1, 'i_no_beds']
                df.loc[idx_end:, 'config_rank'] = new_rank

        if change_flag:
            # update bed totals
            new_R_no_beds = df_ward_rank.loc[new_rank, 'R_no_beds']
            df.loc[idx_end:, 'GIM_R_beds'] = new_R_no_beds

            new_A_no_beds = df_ward_rank.loc[new_rank, 'A_no_beds']
            df.loc[idx_end:, 'GIM_A_beds'] = new_A_no_beds

            # update available beds
            df.loc[idx:, 'GIM_R_beds_avail'] = df.loc[idx:, 'GIM_R_beds'] - df.loc[idx:, 'GIM_R_gen']
            df.loc[idx:, 'GIM_A_beds_avail'] = df.loc[idx:, 'GIM_A_beds'] - df.loc[idx:, 'GIM_A_gen']

            # re-evaluate triggers
            # df.loc[idx:, 'trigger_free_beds_min'] = (df.loc[idx:, 'GIM_R_beds_avail'] <= free_beds_min) | (df.loc[idx:, 'GIM_A_beds_avail'] <= free_beds_min)
            df.loc[idx:, 'trigger_free_beds_min'] = (df.loc[idx:, 'GIM_R_beds_avail'] <= free_beds_min) # only red
            df.loc[idx:, 'trigger_up'] = df.loc[idx:, 'trigger_free_beds_min']
            # df.loc[idx:, 'trigger_free_beds_max'] = (df.loc[idx:, 'GIM_R_beds_avail'] >= free_beds_max) | (df.loc[idx:, 'GIM_A_beds_avail'] >= free_beds_max)
            df.loc[idx:, 'trigger_free_beds_max'] = (df.loc[idx:, 'GIM_R_beds_avail'] >= free_beds_max) # only red
            df.loc[idx:, 'trigger_down'] = (df.loc[idx:, 'trigger_free_beds_max']) | (df.loc[idx:, 'trigger_net_intake']) # use trigger net intake too

        # update index list
        idx_list = df.index[(df['trigger_up'] | df['trigger_down']) & (df.index > idx)]


    return df