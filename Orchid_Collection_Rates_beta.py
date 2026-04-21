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

'''
Set directory, input data
'''

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
#print(data['Date_Acquired_clean'].unique())

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

#print(data['DeathDate_clean'].unique())

#Importantly, how many living orchids do I have in my collection as of April 9th, 2026?
len(data[~data["Status"].str.contains('deceased', case=False, na=False)])
#72

#%%
#Calculate "years grown"
data['Days Grown'] = None
for i in range(len(data)): 
    clean_death = str(data.loc[i, 'DeathDate_clean'])
    if clean_death == 'NaT':
        data.loc[i, 'Days Grown'] = (pd.to_datetime('April 9, 2026') - data.loc[i, 'Date_Acquired_clean']).days
    else:    
       data.loc[i, 'Days Grown'] = (data.loc[i, 'DeathDate_clean'] - data.loc[i, 'Date_Acquired_clean']).days
data['Years Grown'] = data['Days Grown']/365.25

#%%
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
#There was a real uptick in new plant acquisitions ~2023, when I joined a local orchid society
#%%
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
#Likewise, there are entries which have a deceased status, but no further date information,
#The few entries like this will inflate the collection size in the chronology
chrono_data = chrono_data[chrono_data["Status"] != "deceased"]

len(chrono_data[~chrono_data["Status"].str.contains('deceased', case=False, na=False)])

acquisitions = pd.DataFrame({
    'Genus': chrono_data['Genus'],
    'Species or Hybrid': chrono_data["species or hybrid name"],
    'Date': chrono_data['Date_Acquired_clean'],
    'Event': 'Acquisition',
    'Change': 1
})

#Be sure to remove the NaTs from the Mortalities list that came from plants that are
#still alive
mortalities = pd.DataFrame({
    'Genus': chrono_data['Genus'],
    'Species or Hybrid': chrono_data["species or hybrid name"],
    'Date': chrono_data['DeathDate_clean'],
    'Event': 'Mortality',
    'Change':-1
    }).dropna(subset=["Date"])

#Concatonate and rearrange by date
event_data = pd.concat([acquisitions,mortalities], axis=0, ignore_index=True)
event_data = event_data.sort_values(by=['Date'], axis = 0)
event_data['Size_of_Collection'] = event_data['Change'].cumsum()


import matplotlib.pyplot as plt
#A plot of my collection size over time
p1 = "2023-12-14"
p2 = "2023-12-28"
plt.scatter(event_data['Date'],event_data['Size_of_Collection'],
        s=0.5)
plt.axvspan(p1, p2, color="firebrick", alpha=0.2)
plt.show()

#The red line indicates when I joined the local orchid society. My collection really 
#started to grow in 2022, and the size of my collection vacillated only 
#after joinging. Importantly, I moved from Southern California to New Hampshire the same year,
#and started growing my orchids in a grow tent. Perhaps some mortality can be attributed to
#the move and change in growing conditions.

#%%
'''
Has the frequecny of mortalities incrased or decreased over time?
'''
mortalities = mortalities.sort_values(by=['Date'], axis = 0)
#Lets flip the sign on 'change' so it makes a little more sense
mortalities['Change'] = -1 * mortalities['Change'] 
mortalities["Total_Mortalities"] = mortalities['Change'].cumsum()

p1 = "2022-07-30"
p2 = "2024-01-01"
p3 = "2025-07-01"
p4 = "2026-03-22"

plt.scatter(mortalities['Date'],mortalities['Total_Mortalities'],
            color = "firebrick",
        s=1)
plt.axvspan(p1, p2, color="limegreen", alpha=0.2)
plt.axvspan(p2, p3, color="dodgerblue", alpha=0.2)
plt.axvspan(p3, p4, color="gold", alpha=0.2)
plt.title("Cumulative Mortality \nEvents by Time",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Date", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Cumulative Mortality Sum", family = "Georgia", 
                     fontsize = 12)
plt.show()

'''
There are clearly three distinct detectable mortality rates in my collection,
a fairly mild rate from the start of record keeping until Jan 2024 (green),
a dramatic increase in mortality rate through all of 2024 and most of 2025 (blue),
a moderate mortality rate in the second half of 2025 until now.
At first blush, the increase we see in the blue region could just be a function of 
having a larger collection. Did my collection see a concomitant increase? 
'''
acquisitions = acquisitions.sort_values(by=['Date'], axis = 0)
acquisitions["Total_Acquisitions"] = acquisitions['Change'].cumsum()

p1 = "2022-07-30"
p2 = "2024-01-01"
p3 = "2025-07-01"
p4 = "2026-03-22"
plt.scatter(acquisitions['Date'],acquisitions['Total_Acquisitions'],
            color = "firebrick",
        s=1)
plt.axvspan(p1, p2, color="limegreen", alpha=0.2)
plt.axvspan(p2, p3, color="dodgerblue", alpha=0.2)
plt.axvspan(p3, p4, color="gold", alpha=0.2)
plt.title("Cumulative Acquisitions \n by Time",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Date", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Cumulative Acquisitions", family = "Georgia", 
                     fontsize = 12)
plt.show()

'''
Interesting! The blue region, which had the highest orchid mortality rate, qualitatively has a similar
acquisition rate to the other highlighted regions.
'''
#%%
'''
Each mortality event, the death of a single orchid, can also be expressed as a rate.
Put another way, for a given mortality event, what percent of my collection just died?
If I kill ~10% of my orchids, that was only 1 plant when I had 10, but 10 plants when I have 100. 
If I was improving as a grower, I would hope this mortality rate would decrease over time.
'''
event_data["Previous_Value"] = event_data["Size_of_Collection"].shift(1) 
event_data["PctChange"] = (1 / event_data["Previous_Value"]) * 100

pct_mortality = event_data[event_data["Change"] == -1] 
p1 = "2022-07-30"
p2 = "2024-01-01"
p3 = "2025-07-01"
p4 = "2026-03-22"
plt.scatter(pct_mortality['Date'],pct_mortality['PctChange'],
            color = "black",
        s=1)
plt.axvspan(p1, p2, color="limegreen", alpha=0.2)
plt.axvspan(p2, p3, color="dodgerblue", alpha=0.2)
plt.axvspan(p3, p4, color="gold", alpha=0.2)
plt.title("Percent Mortality Rate \n by Time",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Date", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("CMortality Rate \n(%)", family = "Georgia", 
                     fontsize = 12)
plt.show()

#Broadly, it looks as though I have improved as a grower, as the mortality rate among
#my collection has decreased. But I still need to quantify these trends.
#%%
'''
Let's start by looking at my rate of acquisition
'''

p1 = "2022-07-30"
p2 = "2024-01-01"
p3 = "2025-07-01"
p4 = "2026-03-22"
plt.scatter(acquisitions['Date'],acquisitions['Total_Acquisitions'],
            color = "firebrick",
        s=1)
plt.axvspan(p1, p2, color="limegreen", alpha=0.2)
plt.axvspan(p2, p3, color="dodgerblue", alpha=0.2)
plt.axvspan(p3, p4, color="gold", alpha=0.2)
plt.title("Cumulative Acquisitions \n by Time",
          fontsize=20,
          family="Georgia",
          fontweight = "bold")
plt.xlabel("Date", family = "Georgia", 
                     fontsize = 12)
plt.ylabel("Cumulative Acquisitions", family = "Georgia", 
                     fontsize = 12)
plt.show()

'''
Starting at ~2022, the number of plants in my collection really increased. 
We know that mortality rates vary across the different colored regions, so let's
see if the rate of acquisition is steady or variable. 
'''
duration_1 = acquisitions[acquisitions["Date"].between('2022-1-1','2024-1-1')]
duration_2 = acquisitions[acquisitions["Date"].between('2024-1-2','2025-07-01')]
duration_3 = acquisitions[acquisitions["Date"].between('2024-7-01','2026-04-09')]



