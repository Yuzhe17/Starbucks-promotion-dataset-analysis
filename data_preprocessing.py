import numpy as np
import pandas as pd
import glob
import os

from os import listdir
from os.path import isfile, join
from datetime import datetime
from collections import Counter
import json

def read_dataset(files_path='Data/*.json',file_type='json'):
    '''read all the files into pandas dataframe

    args:
        files_path: a list path to all the files

    returns:
        df_list: a list of portfolio, profile, transcript dataframe
    '''

    files=glob.glob(files_path)
    df_list=[]

    for file in files:
        print(file)
        if file_type=='json':
            df=pd.read_json(file,lines=True)

        if file_type=='csv':
            df=pd.read_csv(file)        

        df_list.append(df)
    return df_list

def days_between(d1):
    '''calculate the days from the d1 date to current date

    args:
        d1(str): a string representing d1 date. Example:20170212

    returns:
        int: a number indicating the days from the d1 date to current date
    '''
    d1 = datetime.strptime(d1, "%Y%m%d")
    current_date = datetime.strptime('20211201', "%Y%m%d")
    return abs((current_date - d1).days)


def preprocess_profile(profile):
    '''preprocess the profile dataset

    args:
        profile(pandas dataframe): a dataset describe rewards program users

    returns:
        profile(pandas dataframe): processed profile dataset
    '''
    #add some new columns to profile dataset
    profile['member_date']=pd.to_datetime(profile['became_member_on'],format='%Y%m%d')
    profile['member_year']=profile['member_date'].dt.year.astype(str)
    profile['member_month']=profile['member_date'].dt.month.astype(str)
    profile['member_day']=profile['member_date'].dt.day.astype(str)
    profile['membership_duration(days)']=profile['became_member_on'].astype('str').apply(days_between)

    profile=profile.drop(columns=['became_member_on'])

    return profile

def preprocess_portfolio(portfolio):
    '''preprocess the portfolio dataset
    
    args:
        portfolio(pandas dataframe): a dataset including Offers sent during 30-day test period

    returns:
        portfolio(pandas dataframe): processed portfolio dataset
    '''
    #create web, email, mobile and social columns
    channels=['web', 'email', 'mobile', 'social']
    for channel in channels:
        portfolio[channel]=portfolio['channels'].apply(lambda x: 1 if channel in x else 0)

    portfolio=portfolio.drop(columns=['channels'])

    #create offer name column which can be used to indicate different offers
    offer_name=[]

    for _,row in portfolio.iterrows():
        offer_name.append('r{}/di{}/du{}/t{}'.format(row['reward'],row['difficulty'],row['duration'],row['offer_type'][0]))
        
    portfolio['offer name']=offer_name

    return portfolio

def preprocess_transcript(transcript):
    '''preprocess the transcript dataset
    
    args:
        transcript(pandas dataframe): a dataset including Event logs

    returns:
        portfolio(pandas dataframe): processed transcript dataset   
    '''   
    #extract the offer id for differet offers
    transcript['offer id']=transcript['value'].apply(lambda x:x.get('offer id') if 'offer id' in x else x.get('offer_id'))

    #extract the amount if the event is transactions
    transcript['amount']=transcript['value'].apply(lambda x:x.get('amount'))

    #extract the award if the event is offer completion
    transcript['offer_reward']=transcript['value'].apply(lambda x:x.get('reward'))

    return transcript



if __name__=='__main__':
    #read the dataset
    df_list=read_dataset()

    #preprocessing all the files
    outdir = './preprocessed'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    portfolio=preprocess_portfolio(df_list[0]).to_csv(os.path.join(outdir, 'portfolio.csv'),index=False)
    profile=preprocess_profile(df_list[1]).to_csv(os.path.join(outdir, 'profile.csv'),index=False)
    transcript=preprocess_transcript(df_list[2]).to_csv(os.path.join(outdir, 'transcript.csv'),index=False)

