import numpy as np
import pandas as pd

from os import listdir
from os.path import isfile, join
from datetime import datetime
from collections import Counter

import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split,cross_validate
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score,accuracy_score,roc_auc_score,make_scorer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def create_dataset(offer_profile_vie):
    '''create the dataframe for predicting whether user accept offer_type, the dataframe containing
       profile of a user, the type of offer to predict and whether the user accept the offer
    
    args:
        offer_type(str): the type of offer that we creating dataset for
        
    returns:
       customer_offer_df: target and features in the training dataset
    '''
    #offer_profile_vie=offer_profile_vie[~((offer_profile_vie['complete']==0) & (offer_profile_vie['viewed']==0))]
    
    offer_profile_vie['target']=offer_profile_vie['complete']*offer_profile_vie['viewed']
    
    features_num=['age','income','membership_duration(days)','reward',\
                  'difficulty','duration','web', 'email', 'mobile', 'social']
    
    features_cat=['gender','Inc','Age','Dur','offer_type','member_year']
    
    customer_offer_df=pd.concat([offer_profile_vie[features_num],
                 pd.get_dummies(offer_profile_vie[features_cat])],axis=1)
    customer_offer_df['target']=offer_profile_vie['target'].astype('int32')
    
    return customer_offer_df

def optimize_classifier(X,y):
    '''tuning the hyperparameters of the Random forest classifier
    
    args:
        X,y(array): features and target array
        
    returns:
        classifiers with tuned hyperparameters
    '''
    
    pipeline=Pipeline([('scaler',StandardScaler()),('classifier',DecisionTreeClassifier())])    
    param_grid = dict(classifier__max_depth=[1,2,4,8],classifier__min_samples_split=[2,6,8,15],
                      classifier__min_samples_leaf=[2,4,8])
    grid_search = GridSearchCV(pipeline, param_grid=param_grid,scoring='f1',verbose=3)

    
    grid_search.fit(X,y)
    
    return grid_search.best_estimator_, grid_search.cv_results_

def plot_feature_importance(features,importances):

    '''plot the feature importances

    args:
        features(list): a list of all feature names
        importances(ndarray): an array of all the feature importances 
    '''    
    indices = np.argsort(importances)
    
    plt.figure(figsize=(12,8))
    plt.title('Feature Importances')
    plt.barh(range(len(indices)), importances[indices], color='b', align='center')
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel('Relative Importance')
    plt.savefig('feat_im.JPEG',bbox_inches='tight')

if __name__=='__main__':

    if isfile('offer_profile_vie.csv'):
        offer_profile_vie=pd.read_csv('offer_profile_vie.csv')
    else:
        print('please create the dataset with create_completion.py')

    #read the dataset containing features and target
    customer_offer_df=create_dataset(offer_profile_vie)

    #splite the dataset into training and test set    
    X=customer_offer_df.iloc[:,:-1]
    y=customer_offer_df.iloc[:,-1]
    indices=list(customer_offer_df.index)

    X_train, X_test, y_train, y_test, ind_train, ind_test = train_test_split(X,y,indices,random_state=0,stratify=y)

    #optimize the decision tree classifier, and the decision tree is selected by com
    best_estimator,cv_results_acc=optimize_classifier(X_train,y_train)

    #get the feature importances and names
    features = customer_offer_df.drop(columns=['target']).columns
    importances = best_estimator['classifier'].feature_importances_

    plot_feature_importance(importances)

    #calculate the f1_score, accuracy, roc_auc on the test dataset.
    y_pre = best_estimator.predict(X_test)

    print('f1_score',f1_score(y_test,y_pre))
    print('accuracy',accuracy_score(y_test,y_pre))
    print('roc_auc',roc_auc_score(y_test,y_pre))
