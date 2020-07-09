import pandas as pd
import numpy as np

def _shuffled_range(n):
    """
    Generates a randomly shuffled range from 0 to n-1
    """
    shuffled_range = np.arange(n)
    # np.random.shuffle(shuffled_range)
    return shuffled_range

class Wards():
    def __init__(self):
        path = '/Users/oliverlambson/GitHub/ISMM/CUH_covid_tactical_tool/Data/RAWDATA_Ward_Scenarios.xlsx'
        self.df = pd.read_excel(path)

        # Create columns to mark which wards change color A<->B and B<->C
        self.df['AB_change'] = self.df.A_color != self.df.B_color
        self.df['BC_change'] = self.df.B_color != self.df.C_color

        # Create column for ward change number A<->B
        self.df['AB_change_no'] = None
        change_no = _shuffled_range(len(self.df[self.df.AB_change]))
        self.df.loc[self.df.AB_change, 'AB_change_no'] = change_no
        
        # Create column for ward change number B<->C
        self.df['BC_change_no'] = None
        change_no = _shuffled_range(len(self.df[self.df.BC_change])) + len(self.df[self.df.AB_change])
        self.df.loc[self.df.BC_change, 'BC_change_no'] = change_no

        return

    def get_AB_wards(self):
        return self.df[self.df['AB_change']]

    def get_BC_wards(self):
        return self.df[self.df['BC_change']]

if __name__=='__main__':
    w = Wards()
    print(w.get_AB_wards())
    print(w.get_BC_wards())