import numpy as np
import pandas as pd

from os import listdir
from os.path import isfile, join
from datetime import datetime
from collections import Counter
import json

import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt

def tran_cus_list(transcript):
    '''create the lists of customers who make transactions and don't make any transactions

    args:
        transcript(pandas dataframe): processed transcript dataset   

    returns:
        people_offer_tran(list): a list of ids of customer who received offers and make transactions
        people_offer_notran(list): a list of ids of customer who received offers and dont't make transactions
    '''

    transcript_received=transcript[transcript['event']=='offer received']
    transactions=transcript[transcript['event']=='transaction'][['person','time','amount']]

    people_offer_notran=set(transcript_received['person']).difference(set(transactions['person']))
    people_offer_tran=set(transcript_received['person']).union(set(transactions['person']))
    people_nooffer_tran=set(transactions['person']).difference(set(transcript_received['person']))

    return people_offer_tran,people_offer_notran,people_nooffer_tran

def if_make_transactions(user_id,people_offer_notran,people_offer_tran,people_nooffer_tran):
    '''check if the user has made any transactions

    args:
        user_id(str):user id
        people_offer_tran(list): a list of ids of customer who received offers and make transactions
        people_offer_notran(list): a list of ids of customer who received offers and dont't make transactions       
    '''

    if user_id in people_offer_notran:
        return 'notran_rec'
    elif user_id in people_offer_tran:
        return 'tran_rec'
    elif user_id in people_nooffer_tran:
        return 'tran_norec'
    else:
        return None

def create_plot(profile,transcript):
    '''create figures representing distribution of different traits of a customer

    args:
        profile(pandas dataframe): processed profile dataset
        transcript(pandas dataframe): processed transcript dataset
    '''

    
    #create a new column to indicate if the customer makes any transactions
    people_offer_tran,people_offer_notran,people_nooffer_tran=tran_cus_list(transcript)  
    kwargs={'people_offer_tran':people_offer_tran,'people_offer_notran':people_offer_notran,'people_nooffer_tran':people_nooffer_tran}

    profile['if_tran_rec']=profile['id'].apply(if_make_transactions,**kwargs)

    
    #drop rows with missing value in the profile dataset
    profile_clean=profile.dropna()

    #creating subplots
    fig,axs=plt.subplots(nrows=2,ncols=2)
    fig.set_size_inches(12, 8)

    color_palettes=sns.color_palette()
    palette=[color_palettes[0],color_palettes[1]]

    sns.countplot(data=profile_clean,x='gender',hue='if_tran_rec',palette=palette,ax=axs[0,0])
    axs[0,0].set_xlabel('gender')

    sns.histplot(data=profile_clean,x='age',hue='if_tran_rec',palette=palette,ax=axs[0,1])
    axs[0,1].set_xlabel('age')

    sns.histplot(data=profile_clean,x='income',hue='if_tran_rec',palette=palette,ax=axs[1,0])
    axs[1,0].set_xlabel('income')

    sns.countplot(data=profile_clean,x='member_year',hue='if_tran_rec',palette=palette,ax=axs[1,1])
    axs[1,1].set_xlabel('member_year')

    plt.tight_layout()
    plt.savefig('profile.JPEG')

if __name__=='__main__':
    if isfile('preprocessed/profile.csv') and isfile('preprocessed/profile.csv'):
        profile=pd.read_csv('preprocessed/profile.csv')
        transcript=pd.read_csv('preprocessed/transcript.csv')
    else:
        print('please first create the processed files with data_preprocessing.py')

    create_plot(profile,transcript)