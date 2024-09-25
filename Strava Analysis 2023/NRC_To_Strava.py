#!/usr/bin/env python
# coding: utf-8

# ## Collecting Strava Data 
# ### Manny Lazalde
# ### August 7th, 2022

# Wanted to analyze Strava Run Data, and automate nike run club conversion straight to Strava, instead of having to do it manually every so often. This way I can do it automatically in Python. Inspired by https://towardsdatascience.com/using-the-strava-api-and-pandas-to-explore-your-activity-data-d94901d9bfde

# #### Imports

# In[46]:


#web url libraries
import requests
import urllib3
import json
from urllib.request import urlopen
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#for getting info from lat/long
#from geopy.geocoders import Nominatim

import pandas as pd
#Datetime will allow Python to recognize dates as dates, not strings.
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

#import sys, os; os.system(sys.executable + ' -m pip install --user webdriver_manager')

from webdriver_manager.chrome import ChromeDriverManager
import time

#code to ensure correct driver is made
#driver = webdriver.Chrome(ChromeDriverManager().install())


# #### Code for Grabbing Strava Data

# In[100]:


#Taken from https://github.com/fpolignano/Code_From_Tutorials/blob/master/Strava_Api/strava_api.py
#Code to grab current Strava data

auth_url = "https://www.strava.com/oauth/token"
activites_url = "https://www.strava.com/api/v3/athlete/activities"

payload = {
    'client_id': "91559",
    'client_secret': '0b4ba39eb19596b212db839859d53038ee0ef8cb',
    'refresh_token': 'fa0ed46c3baec8feeac22cf4c3819a3758439b4a',
    'grant_type': "refresh_token",
    'f': 'json'
}

print("Requesting Token...\n")
res = requests.post(auth_url, data=payload, verify=False)
access_token = res.json()['access_token']
print("Access Token = {}\n".format(access_token))

header = {'Authorization': 'Bearer ' + access_token}

## Updating this portion to grab all of the runs from Strava in total, instead of just the last 200

#param = {'per_page': 200, 'page': 1}
#my_dataset = requests.get(activites_url, headers=header, params=param).json()
#print(my_dataset[0]["name"])
#print(my_dataset[0]["map"]["summary_polyline"])

param = {'per_page': 200, 'page': 1}
#store strava data in list, cause too complicated to merge in while loop
df_list = []

while True:
    
    #grab the data from strava through an http request
    r = requests.get(activites_url, headers=header, params=param).json()
    
    # if no results then exit loop
    if (not r):
        break
    
    #store dataframes in list
    df_list.append(pd.json_normalize(r))
    
    #keep iterating till all data is collected
    param['page'] = param['page'] + 1

print("Success! Got it all without error!")


# #### Code for performing data analysis on Strava Data

# In[101]:


# First move is to take list of all dataframes and merge to single dataframe. Do so below
activities = df_list[0]

for i in range(len(df_list)):
    if i == 0:
        continue
    activities = pd.concat([activities,df_list[i]])

#export to csv for visualization
activities.to_csv("Activies.csv")

#lets drop the useless columns
activities = activities[['resource_state', 'name', 'distance','elapsed_time',
       'total_elevation_gain', 'type', 'workout_type', 'id',
       'start_date_local', 'timezone',
        'start_latlng', 'end_latlng', 'average_speed',
       'max_speed', 'elev_high', 'elev_low', 'athlete.id']]


#Perform data manipulation
activities['start_date_local'] = pd.to_datetime(activities['start_date_local'])
activities['start_time'] = activities['start_date_local'].dt.time
activities['start_date_local'] = activities['start_date_local'].dt.date
activities['distance_miles'] = round(activities['distance'] / 1609.34,2)
activities['time_minutes'] = round(activities['elapsed_time'] / 60)

#grab city from start_lat/long - Have to be careful with this if desired
# https://operations.osmfoundation.org/policies/nominatim/
#geolocator = Nominatim(user_agent="test")
#location = geolocator.reverse("42.3513587, -83.0653791")

#export to excel for visualization
activities.to_excel("Activies.xlsx")

#activities


# Good first effort to grab all running data from strava. Next part is to compare this data against what we have on Nike run club via https://nexporter.bullrox.net/en/account/activities, and look to upload anything that isn't the same. This requires clicking a button in Python, and to do that need to use another library called Selenium. Also need to figure out how to run a Python Script daily, but can use windows scheduler, I believe.

# In[98]:


#PATH = "C:\Program Files (x86)\chromedriver.exe"

#code to ensure correct driver is made

driver = webdriver.Chrome(ChromeDriverManager().install(),#,,service=Service(PATH), 
                          options=webdriver.ChromeOptions())

#log onto the website
driver.get("https://nexporter.bullrox.net/en/account/activities")

#find the text boxes and enter in magic key & email 
#need to find the web elements and then enter in the text
search = driver.find_element(By.CLASS_NAME,"form-control")
keys = "h6QQ9"
search.send_keys(keys)
search = driver.find_element(By.CSS_SELECTOR,"input[type='email']")
search.send_keys("mannylazalde@gmail.com")
# now find the button to click and log in with info
search = driver.find_element(By.CSS_SELECTOR,
                "button.btn.btn-outline-secondary")
search.click()


#delay to allow time for webpage to load
print('Logging onto website. (https://nexporter.bullrox.net/en/account/activities)')
print('Wait 3 seconds for login')
time.sleep(3)
print("Ok, go!")

#now we are logged into our account
#now we need to find the list of runs and determine which ones to upload

run_dates = driver.find_elements(By.CSS_SELECTOR, 
                   "div.col-12.col-sm-12.col-md-4.col-lg-3.col-xl-2")

buttons = driver.find_elements(By.CSS_SELECTOR, 
        "button.btn.btn-primary.btn-sm.activityActions_strava__2FClU")


#run_dates is now a list of all the dates appearing on the webpage in order
#buttons is list of the corresponding upload to strava buttons

#iterate through all dates from NRC website runs. 
#compare to Strava runs, and if not on strava, upload
print("Checking all runs from Nike Run Club!")
for item,item2 in zip(run_dates,buttons):
    
    #convert dates from NRC from string to datetime
    date = datetime.strptime(item.text.strip(), 
                                          '%m/%d/%Y %H:%M %p')
    #check to see if in Strava runs. If not, need to upload
    if not date.date() in activities['start_date_local'].values:
        print()
        print(str(date.date()) +" doesn't exists in Strava Data")
        item2.click()
        print("Clicked button and uploading now. Should now exist in Strava!")
        time.sleep(8)

print('Strava now up to date!')

driver.close()


# In[ ]:




