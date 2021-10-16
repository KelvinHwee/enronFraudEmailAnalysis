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
import os

# - import packages for NLP
'''
- for the installation of "en_core_web_sm", we use the following command in terminal
- pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.1.0/en_core_web_sm-3.1.0.tar.gz
- the file was then downloaded to this folder: /home/kelvinhwee/.cache/pip/wheels/62/79/40/648305f0a2cd1fdab236bd6764ba467437c5fae2a925768153
- we copied the zipped file, and extracted the "en_core_web_sm" folder (containing the "config.cfg" file) into the 
- current directory /home/kelvinhwee
'''


import spacy
nlp = spacy.load('en_core_web_sm-3.1.0')
doc = nlp("the drawdown process is governed by astm standard d823")



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

#=== make a copy of the dataframe
print(emails_df.head())

