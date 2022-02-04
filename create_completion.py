import numpy as np
import pandas as pd
import glob
import os

from os import listdir
from os.path import isfile, join
from data_preprocessing import read_dataset

def create_completion_df(portfolio,profile,transcript):
    '''determining if a user has completed an offer and the amount of money spent and create a new dataframe

    args:
        portfolio, profile, transcript(dataframe): the preprocessed dataset containing information on offer, user, and transactions

    return:
        offer_profile(dataframe): a new dataframe containing user offer information and if the user accepted the offer
    '''

    #separate the event of receiving an offer and making transactions and merge them
    transcript_received=transcript[transcript['event']=='offer received']
    transcript_received=transcript_received.merge(portfolio,how='left',left_on='offer id',right_on='id')
    transcript_received['offer_del']=transcript_received['time']+transcript_received['duration']*24

    transactions=transcript[transcript['event']=='transaction'][['person','time','amount']]
    transactions.head()

    transcript_received_tran=transcript_received.merge(transactions,how='left',on='person',suffixes=['_rec','_tran'])

    #filter out all the transactions within the receiving offer time and offer deadline
    condition1=(transcript_received_tran['time_tran']>=transcript_received_tran['time_rec'])
    condition2=(transcript_received_tran['time_tran']<=transcript_received_tran['offer_del'])
    transcript_received_filtran=transcript_received_tran[condition1 & condition2]

    #calulate the sum and max value of amounts of the transactions during the offer opening time
    offer_tran=transcript_received_filtran.groupby(['person','offer id','time_rec']).agg({'amount_tran':[sum,max]}).reset_index()
    offer_tran.columns=['person','offer id','time_rec','amount_sum','amount_max']

    #fill the amount_sum and amount_max with 0 when users didn't make transactions during the offer opening time
    offer_tran=transcript_received.rename(columns={'time':'time_rec'})[['person','offer id','time_rec']].\
    merge(offer_tran,how='left',on=['person','offer id','time_rec'])

    offer_tran=offer_tran.fillna(0)

    #include extra information about offers
    offer_tran=offer_tran.merge(portfolio,how='left',left_on='offer id',right_on='id')

    #separate offer_tran into dataframes with bogo and discout offers
    offer_tran_bogo=offer_tran[offer_tran['offer_type']=='bogo']
    offer_tran_dis=offer_tran[offer_tran['offer_type']=='discount']
    offer_tran_info=offer_tran[offer_tran['offer_type']=='informational']

    #determine the completed and not completed offers of different types
    offer_dis_com=offer_tran_dis[offer_tran_dis['amount_sum']>=offer_tran_dis['difficulty']]
    offer_dis_ncom=offer_tran_dis[offer_tran_dis['amount_sum']<offer_tran_dis['difficulty']]

    offer_bogo_com=offer_tran_bogo[offer_tran_bogo['amount_max']>offer_tran_bogo['difficulty']]
    offer_bogo_ncom=offer_tran_bogo[offer_tran_bogo['amount_max']<=offer_tran_bogo['difficulty']]

    #determine the completed and not completed offers
    offer_com=pd.concat([offer_dis_com,offer_bogo_com])
    offer_ncom=pd.concat([offer_dis_ncom,offer_bogo_ncom])

    #add label indicating whether the offer is completed
    offer_com['complete']=np.ones(offer_com.shape[0])
    offer_ncom['complete']=np.zeros(offer_ncom.shape[0])

    User_offer=pd.concat([offer_com,offer_ncom])

    #add the informational offer
    offer_tran_info.loc[:,'complete']=-1*np.ones(offer_tran_info.shape[0])

    User_offer=pd.concat([User_offer,offer_tran_info])

    User_offer=User_offer.merge(profile,how='left',left_on='person',right_on='id')

    User_offer=User_offer.drop(columns=['id_x','id_y'])

    #add information of a user
    offer_profile=transcript_received.merge(profile,how='left',left_on='person',right_on='id')
    offer_profile=offer_profile.drop(columns=['event','value','amount','id_x','id_y']).rename(columns={'time':'time_rec'})

    features_retain=['person','offer id','time_rec','amount_sum','amount_max','complete']
    offer_profile=offer_profile.merge(User_offer[features_retain],how='left',on=['person','offer id','time_rec'])
    
    transcript_com=transcript[transcript['event']=='offer completed']
    offer_completed=offer_profile[offer_profile['complete']==1]

    offer_completed=offer_completed.merge(transcript_com[['person','offer id','time']],how='left',on=['person','offer id'])
    #offer_completed=offer_completed.drop(columns=['offer_reward_x','event','value','amount','offer_reward_y'])

    offer_completed['com_rec_diff']=offer_completed['time']-offer_completed['time_rec']
    offer_completed=offer_completed[offer_completed['com_rec_diff']>=0].drop(columns=['offer_reward','time'])

    offer_completed=offer_completed.groupby(by=['person','time_rec','offer id'])['com_rec_diff'].apply(min).reset_index()

    offer_completed['time_com']=offer_completed['time_rec']+offer_completed['com_rec_diff']

    offer_completed=offer_completed.drop(columns=['com_rec_diff'])

    offer_completed=offer_completed.merge(transactions,how='left',on='person')

    condition_com=(offer_completed['time']<=offer_completed['time_com'])
    condition_rec=offer_completed['time']>=offer_completed['time_rec']

    offer_completed=offer_completed[condition_com & condition_rec]

    offer_completed=offer_completed.groupby(['person','time_rec','offer id']).agg({'amount':[sum,len]}).reset_index()
    offer_completed.columns=['person','time_rec','offer id','sum_till_com','num_till_com']

    offer_profile=offer_profile.merge(offer_completed,how='left',on=['person','time_rec','offer id'])
    offer_profile=offer_profile.drop(columns=['offer_reward'])

    offer_profile=offer_profile[offer_profile['offer_type']!='informational']
    offer_profile['complete']=offer_profile['complete'].astype(np.int32)

    offer_profile=offer_profile.dropna(subset=['gender','income'])

    return offer_profile

def create_viewed_df(transcript,offer_profile):
    '''determine whether an offer is viewed by a customer before or after completion when the offer is completed,
        or whether an offer is viewed when the offer is not completed

    args:
        transcript(pandas dataframe): transactions log
        offer_profile(pandas dataframe): a dataset containing information on customer, offers and whether the offer is completed 
    '''
    #filter out the transcript when event is only 'offer viewed' or 'offer completed'
    transcript_viewed=transcript[transcript['event']=='offer viewed'][['person','time','offer id']]
    transcript_cpl=transcript[transcript['event']=='offer completed'][['person','time','offer id','offer_reward']]

    #filter out orders that is completed and determine the completion time of an offer
    cpl=offer_profile[offer_profile['complete']==1].merge(transcript_cpl,on=['person','offer id'],how='left')
    cpl=cpl[(cpl['time']>=cpl['time_rec']) & (cpl['time']<=cpl['offer_del'])]
    cpl=cpl.groupby(['person','offer id','time_rec']).apply(lambda s:pd.Series({'cpl_time':min(s['time'])})).reset_index()

    #determine which offers are viewed before or after completion by comparing its viewing time with offer receiving time and deadline
    offer_profile_cpl=offer_profile[offer_profile['complete']==1].merge(cpl,on=['person','offer id','time_rec'],how='left')
    cpl_viewed=offer_profile_cpl.merge(transcript_viewed,on=['person','offer id'],how='left')

    cpl_viewed=cpl_viewed[(cpl_viewed['time']>=cpl_viewed['time_rec']) & 
                               (cpl_viewed['time']<=cpl_viewed['cpl_time'])]

    cpl_viewed=cpl_viewed.drop_duplicates(subset=['person','offer id','time_rec'])
    cpl_viewed['viewed']=1

    offer_profile_cpl_vie=offer_profile_cpl.merge(cpl_viewed[['person','offer id','time_rec','viewed']],
                                                on=['person','offer id','time_rec'],how='left')
    offer_profile_cpl_vie=offer_profile_cpl_vie.fillna(value={'viewed':0})

    #filter out the offers that are not completed
    offer_profile_ncpl=offer_profile[offer_profile['complete']==0].merge(transcript_viewed,on=['person','offer id'],how='left')
    
    #deciding which offers are viewed by comparing the viewing time with offer receiving time and deadline
    ncpl_viewed=offer_profile_ncpl[((offer_profile_ncpl['time_rec']<=offer_profile_ncpl['time']) & \
        (offer_profile_ncpl['offer_del']>=offer_profile_ncpl['time']))]

    ncpl_viewed=ncpl_viewed.drop_duplicates(subset=['person','offer id','time_rec'])
    ncpl_viewed['viewed']=1

    offer_profile_ncpl_vie=offer_profile[offer_profile['complete']==0].merge(ncpl_viewed[['person','offer id','time_rec','viewed']],
                                              on=['person','offer id','time_rec'],how='left')    

    offer_profile_ncpl_vie=offer_profile_ncpl_vie.fillna(value={'viewed':0})
    offer_profile_ncpl_vie['cpl_time']=(-1)*np.ones(offer_profile_ncpl_vie.shape[0])

    #concatenate the completed and not completed offers
    offer_profile_vie=pd.concat([offer_profile_cpl_vie,offer_profile_ncpl_vie],axis=0)

    return offer_profile_vie

if __name__=='__main__':

    #read the dataset
    if glob.glob('preprocessed\*.csv'):
        df_list=read_dataset(files_path='preprocessed\*.csv',file_type='csv')
    else:
        print('please create the csv files first')

    transcript=pd.read_csv(glob.glob('preprocessed/transcript.csv')[0])

    offer_profile=create_completion_df(*df_list)
    
    offer_profile_vie=create_viewed_df(transcript,offer_profile)

    offer_profile_vie.to_csv('offer_profile_vie.csv',index=False)

