#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 10:48:52 2026

@author: dr.carlisles.bascomjr
"""


import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import math
import scipy as sp
import statsmodels as sm

os.chdir("/Users/dr.carlisles.bascomjr/Desktop/PythonTestCode/OrchidMortality")
#This spreadsheet was downloaded from a Google Sheet on April 9th, 2026
data = pd.read_csv("Orchid_Collection.csv", header =2)
#print(data)

'''
To start cleaning the Status and Date Acquired columns, we need to see what the
data look like
'''
print(data['Status'].unique())
print(data['Date Acquired'].unique())

'''
The Date Acquired column is more organized, tackle first
'''
import datetime
#Remove day suffixes in column
data['Date_Acquired_clean'] = data['Date Acquired'].str.replace(r'(\d+)(st|nd|rd|th)', repl = r'\1', regex=True)
#Add month/day values for incomplete dates
for i in range(len(data)): 
    value = str(data.loc[i, 'Date_Acquired_clean'])
    if 'ca' in value or 'Pre' in value:
       year = value[-4:]
       data.loc[i, 'Date_Acquired_clean'] = "July 2, " + year
    elif len(value) == 9:
        year = value[-4:]
        month = value[:3]
        data.loc[i, 'Date_Acquired_clean'] = month + " 1, " + year
#Convert to data so Python knows  
data['Date_Acquired_clean'] = pd.to_datetime(data['Date_Acquired_clean'], format='mixed')    
#Check to make sure everything works (we can handle NAs later)
print(data['Date_Acquired_clean'].unique())

'''
Clean up the Status column, which contains deathdate information
'''    
print(data['Status'].unique())
#Easily remove the suffixes in column
data['Status'] = data['Status'].str.lower()
data['DeathDate_clean'] = data['Status'].str.replace(r'(\d+)(st|nd|rd|th)', repl = r'\1', regex=True)
#loop through rest
for i in range(len(data)):
    value = str(data.loc[i, 'Status'])
    if 'deceased' in value and '.' in value:
        data.loc[i, 'DeathDate_clean'] = data.loc[i, 'Status'].split()[-1]
    elif 'deceased' in value and ',' in value and '.' not in value:
        data.loc[i, 'DeathDate_clean'] = " ".join(data.loc[i, 'DeathDate_clean'].split()[1:4])
    elif 'deceased' in value and '.' not in value and ',' not in value:
        data.loc[i, 'DeathDate_clean'] = pd.NaT
    elif 'deceased' not in value:
        data.loc[i, 'DeathDate_clean'] = pd.NaT
data['DeathDate_clean'] = pd.to_datetime(data['DeathDate_clean'], format='mixed')    

#Importantly, how many living orchids do I have in my collection as of April 9th, 2026?
len(data[~data["Status"].str.contains('deceased', case=False, na=False)])
#72

#Calculate "years grown"
data['Days Grown'] = None
for i in range(len(data)): 
    clean_death = str(data.loc[i, 'DeathDate_clean'])
    if clean_death == 'NaT':
        data.loc[i, 'Days Grown'] = (pd.to_datetime('April 9, 2026') - data.loc[i, 'Date_Acquired_clean']).days
    else:    
       data.loc[i, 'Days Grown'] = (data.loc[i, 'DeathDate_clean'] - data.loc[i, 'Date_Acquired_clean']).days
data['Years Grown'] = data['Days Grown']/365.25

#Make some quick histograms as a first pass of the data
import matplotlib.pyplot as plt

'''
What is the distribution profile of how long I have grown orchids?
'''
mean_duration = np.nanmean(data['Years Grown'])
stdev = np.nanstd(data['Years Grown'])
plt.hist(data['Years Grown'], 
         color = "firebrick",
         edgecolor='black',
         bins = 10)
plt.title("Number of Years Growing Orchids",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.axvline(mean_duration, color='black', linestyle='solid', linewidth=2)
plt.axvline((mean_duration+stdev), color='black', linewidth=1)
plt.axvline((mean_duration-stdev), color='black', linewidth=1)
plt.xlabel("Years", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Frequency", family = "Georgia", 
                     fontsize = 12)
plt.show()

#Looks like, on average, an orchid in my collect is 2.76 +/- 3 years old. Quite the range!

'''
Is the distribution of orchid acquisitions random or skewed?
'''

plt.hist(data['Date_Acquired_clean'], 
         color = "forestgreen",
         edgecolor='black',
         bins = 16)
plt.title("Distruibtion of New Orchid Acquisitions",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Date of Acquisition", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Frequency", family = "Georgia", 
                     fontsize = 12)
plt.show()
#There was a real uptick in new plant acquisitions ~2023, when I joined a local orchid society!
'''
Is the distribution of orchid deaths random or skewed?
'''
plt.hist(data['DeathDate_clean'], 
         color = "darkgrey",
         edgecolor='black',
         bins = 16)
plt.title("Distruibtion of Mortality",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Recorded Date of Death", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Frequency", family = "Georgia", 
                     fontsize = 12)
plt.show()
#The bins are not directly comparable to the acquisitions graph, but 
#it looks like 2024 was a bad year for my collection. We will have to explore
#this further as we dig into comparable rates of acquisition and mortality below.

'''
Combining acquisitions and mortalities, what does my collection look like
over time?
'''
#Sort data by acquisition date in a new dataframe to work with
chrono_data = data.sort_values(by=['Date_Acquired_clean'], axis = 0)
#There are a few entries for which we do not have any acquisition data, 
#and we can't do anythig about that, so drop them for now
chrono_data = chrono_data.dropna(subset=["Date_Acquired_clean"])

acquisitions = pd.DataFrame({
    'Date': chrono_data['Date_Acquired_clean'],
    'Event': 'Acquisition',
    'Change': 1
})

#Be sure to remove the NaTs from the Mortalities list that came from plants that are
#still alive
mortalities = pd.DataFrame({
    'Date': chrono_data['DeathDate_clean'],
    'Event': 'Mortality',
    'Change':-1
    }).dropna(subset=["Date"])

#Concatonate and rearrange by date
event_data = pd.concat([acquisitions,mortalities], axis=0, ignore_index=True)
event_data = event_data.sort_values(by=['Date'], axis = 0)
event_data['Size_of_Collection'] = event_data['Change'].cumsum()


import matplotlib.pyplot as plt
plt.scatter(event_data['Date'],event_data['Size_of_Collection'],
        s=0.5)

plt.show()

data.to_csv('output.csv', index=False)       
