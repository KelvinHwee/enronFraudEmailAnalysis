#######################################################################################################################
#   Background of code
#######################################################################################################################
'''
We attempt to use multiple linear regression models to model the insurance premium prediction problem
'''

#######################################################################################################################
#   Basic configuration steps
#######################################################################################################################

# - import basic python packages
import warnings
import tkinter  # to show plot in Pycharm
warnings.simplefilter(action='ignore', category=FutureWarning)

# - import packages for data manipulations
import numpy as np
import pandas as pd

# - import packages for visualizations


# - other configurations
pd.set_option("display.max_column", None)
source_filepath = '/home/kelvinhwee/PycharmProjects/sourceFiles'


################################################################################
#   Read CSV data file
################################################################################
'''
- the email file is large
'''


#=== reading in of data
emails_df = pd.read_csv(source_filepath + '/emails.csv')
emails_df2 = emails_df.copy()

#=== make a copy of the dataframe
print(emails_df.head())

import os
os.getcwd()