import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt

from os.path import isfile, join


def bin_inc_age(offer_profile_vie):
    '''binning of age and income columns

    args:
        offer_profile_vie(pandas dataframe): a dataframe containing info on customer, offer and 
        whether an offer is completed or viewed by a customer.
    '''
    #define the quantiles and ranges based which to segment ages and incomes; for income and membership duaration, quantiles
    #are used so that the resulting bins end up to be more uniform.
    quantile_list = [0, .25, .5, .75, 1.]
    bin_ranges = [17, 40, 60, 80, 102]


    offer_profile_vie['Inc'] = pd.qcut(offer_profile_vie['income'], q=quantile_list)

    offer_profile_vie['Dur'] = pd.qcut(offer_profile_vie['membership_duration(days)'], q=quantile_list)

    offer_profile_vie['Age'] = pd.cut(np.array(offer_profile_vie['age']), bins=bin_ranges)

    traits_name=['inc','age','dur']
    traits_quantile=['Inc','Age','Dur']

    for name,quantile in zip(traits_name,traits_quantile):
        labels=[name+'_'+g for g in ['g1','g2','g3','g4']]
        mapper=dict(zip(list(set(offer_profile_vie[quantile])),labels))
        print(mapper)
        offer_profile_vie[quantile]=offer_profile_vie[quantile].map(mapper)
    
    return offer_profile_vie

def create_viewed_vis(offer_profile_vie):
    '''create visualizations of all the customers who viewed offers

    args:
        offer_profile_vie(pandas dataframe): a dataframe containing info on customer, offer and 
        whether an offer is completed or viewed by a customer.
    '''

    fig,axs=plt.subplots(nrows=2,ncols=2)
    fig.set_size_inches(12, 8)

    color_palettes=sns.color_palette()
    palette=[color_palettes[0],color_palettes[1]]

    data=offer_profile_vie[offer_profile_vie['viewed']==1].reset_index()

    sns.countplot(data=data,x='gender',hue='complete',palette=palette,ax=axs[0,0])
    axs[0,0].legend(['no','yes'])
    axs[0,0].set_xlabel('gender')

    sns.histplot(data=data,x='age',hue='complete',palette=palette,ax=axs[0,1])
    axs[0,1].legend(['yes','no'])
    axs[0,1].set_xlabel('age')

    # sns.histplot(data=profile_clean,x='membership_duration(days)',hue='if_tran_rec',bins=50,ax=axs[2])
    # axs[2].set_xlabel('membership_duration(days)')

    sns.histplot(data=data,x='income',hue='complete',palette=palette,ax=axs[1,0])
    axs[1,0].legend(['yes','no'])
    axs[1,0].set_xlabel('income')

    sns.countplot(data=data,x='member_year',hue='complete',palette=palette,ax=axs[1,1])
    axs[1,1].legend(['no','yes'])
    axs[1,1].set_xlabel('member_year')

    # sns.countplot(data=profile_clean,x='member_month',hue='if_tran_rec',ax=axs[5])
    # axs[5].set_xlabel('member_month')

    plt.tight_layout()
    #plt.subplots_adjust(bottom=0.5)
    plt.savefig('view_cpl_ncpl.JPEG')

def create_ocr_offer(offer_profile):
    '''create a visualization of offer completion ratio of different offers names, difficulty, duration and reward

    args:
        offer_profile_vie(pandas dataframe): a dataframe containing info on customer, offer and 
        whether an offer is completed or viewed by a customer.
    '''
    fig,axs=plt.subplots(nrows=2,ncols=2)
    fig.set_size_inches(12,8)

    palette=sns.color_palette()

    data=offer_profile[offer_profile['offer_type']!='informational']
    offer_traits=['offer name','difficulty','duration','reward']

    for ax,trait in zip(axs.flatten(),offer_traits):
        
        sns.barplot(data=data,x=trait,y='complete',color=palette[0],ax=ax)

        ax.set_xlabel(trait)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

        ax.set_title('completion rate of offers with different {}'.format(trait))
        
    plt.tight_layout()
    plt.savefig('offer_profile.JPEG')

def create_ocr(offer_profile):
    '''create a visualization of offer completion ratio of different offers for customers in different group of income and age

    args:
        offer_profile_vie(pandas dataframe): a dataframe containing info on customer, offer and 
        whether an offer is completed or viewed by a customer.
    '''
    #binning the age and income columns
    offer_profile=bin_inc_age(offer_profile)

    plt.figure(figsize=(18,18))
    palette=sns.color_palette()

    row_order=['inc_g1','inc_g2','inc_g3','inc_g4']
    col_order=['age_g1','age_g2','age_g3','age_g4']

    data=offer_profile[offer_profile['gender']!='O'].sort_values(['Inc','Age'])
    g=sns.FacetGrid(data,col='Age',row='Inc',row_order=row_order,col_order=col_order)
    g.map(sns.barplot,'offer name','complete','gender',palette=palette,ci=None)
    for i in range(g.axes.shape[0]):
        g.axes[i,0].set_ylabel('offer completion ratio')

    g.add_legend(loc='lower left')

    for axes in g.axes.flat:
        _ = axes.set_xticklabels(axes.get_xticklabels(), rotation=90)
        
    plt.tight_layout()
    plt.savefig('age_income.JPEG')


def create_ocr_groups(offer_profile):
    '''comparing the ocr of customers belonging to different age, membership duration and income groups

    args:
        offer_profile_vie(pandas dataframe): a dataframe containing info on customer, offer and 
        whether an offer is completed or viewed by a customer.
    '''
    
    #binning the age and income columns
    offer_profile=bin_inc_age(offer_profile)

    font = {'size'   : 15}
    matplotlib.rc('font', **font)

    f,axs=plt.subplots(3,2)
    f.set_size_inches(12, 12)
    users_profile=['age','income']
    users_profile_bin=['Age','Inc',
                    'Dur','member_year']

    for i,ax in enumerate(axs[0].flatten()):
        data=offer_profile.groupby(users_profile[i]).mean()['complete'].reset_index()
        sns.scatterplot(x=data[users_profile[i]],y=data['complete'],ax=ax)
        ax.set_title(' as a function of {}'.format(users_profile[i]))
        ax.set_ylim(0,1)

    for i,ax in enumerate(axs[1:,:].flatten()):
        
        data_sorted=offer_profile.sort_values(users_profile_bin[i])
        sns.barplot(data=data_sorted,x=users_profile_bin[i],y='complete',ax=ax)

        ax.set_title('OCR in different groups of {}'.format(users_profile_bin[i]))
        xticklabels=ax.get_xticklabels()
        ax.set_xticklabels(xticklabels, rotation = 30, va="center", position=(0,-0.28))
        ax.set_ylim(0,1)
        
    plt.tight_layout()
    plt.savefig('user_profile_ocr.JPEG',dpi=300)

if __name__=='__main__':
    
    if isfile('offer_profile_vie.csv'):
        offer_profile_vie=pd.read_csv('offer_profile_vie.csv')
    else:
        print('please create the dataset with create_completion.py')

    #create visualizations
    
    create_viewed_vis(offer_profile_vie)
    create_ocr_offer(offer_profile_vie)
    create_ocr(offer_profile_vie)
    create_ocr_groups(offer_profile_vie)







