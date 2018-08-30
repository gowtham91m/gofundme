# -*- coding: utf-8 -*-

#author: Gowtham Mallikarjuna

from bs4 import BeautifulSoup as bs
import requests
from IPython.display import display, clear_output
import re
import pandas as pd
from time import time
from collections import defaultdict
#from google.colab import files
from collections import OrderedDict
from datetime import datetime
from itertools import accumulate
import os
import logging
import subprocess
import getpass

class web_scraper:
    def __init__(self):
        self.url = 'https://www.gofundme.com/discover'
        self.campaign_columns = ['category','page','title','href','location','start_date','goal','raised',
                                 'text','likes','shares','photos','donation_count','duration',
                                 'recent_donation_time','goal_reaeched_time','script_run_time']

    def read_data(self,path):
      os.chdir(path)
      if 'campaigns.csv' not in os.listdir():
            campaign_data = pd.DataFrame(OrderedDict({i:[] for i in self.campaign_columns}))
            campaign_data.to_csv('campaigns.csv',index=False)
      else:
            campaign_data = pd.read_csv('campaigns.csv')
      return campaign_data
      
    def git_clone(self):
      
      if 'gofindme' not in os.listdir(os.getcwd()):
        os.chdir('/content')
        username = input('username:')
        password = getpass.getpass('Password:')
        gt = 'https://'+username+':'+password+'@github.com/gowtham91m/gofundme.git'
        subprocess.Popen(['git', 'clone', str(gt)])
        os.chdir('gofundme/data/')
      else:
        os.chdir('data')
        subprocess(['git','pull'])
        
    def git_push(self):
      subprocess.Popen(['git','add','campaigns.csv'])
      subprocess.Popen(['git','commit','-m','commit'])
      subprocess.Popen(['git','push','-u','origin','master'])
        
    def get_categories(self):
        soup = requests.get(self.url)
        soup = bs(soup.text,'html.parser')
        category = soup.findAll(class_='text-black')
        categories = [i.text for i in category]  
        return categories[:16]

    def details_parser(self,url,category,page):
        soup=bs(requests.get(url).text,'html.parser')
        title  = soup.findAll(class_='campaign-title')[0].text
        location  = soup.findAll(class_='icon-link location-name js-location-link')[0].text[3:].strip()

        try: text = soup.findAll(class_="co-story truncate-text truncate-text--description js-truncate")[0].text.strip()
        except IndexError: text = 'exception occured for' + url
          
        try: likes =  soup.findAll(class_='roundedNum')[0].text
        except IndexError: likes = 0
          
        try: photos = soup.findAll(class_='open-media-viewer')[0].text.strip()
        except IndexError: photos = 0

        try: shares = soup.findAll(class_='js-share-count-text')[0].text.strip()
        except IndexError: shares = 0
           
        try: start_date = soup.findAll(class_='created-date')[0].text[8:]
        except Exception as e:
          print('error getting start date:',e)
          start_date = e
        try: 
          donation = soup.findAll(class_='campaign-status text-small')[0].text.strip()
          recent_donation_time = soup.findAll(class_='supporter-time')[0].text.strip()
          donation = donation.split(' ')
          donation_count = donation[2]
          duration = ' '.join(donation[-2:])
          funds  = soup.findAll('h2',class_='goal')[0].text
          raised = re.findall('\$\d+.*',funds)[0]
          goal = re.findall('\$\d+.*',funds)[1].split(' ')[0]
          
          print('\n',url[25:],raised,'/',goal,'-',donation_count,' ',end='')
          if int(re.sub('[^\d]','',raised)) >= int(re.sub('[^\d]','',goal)):
            min_completion_time = self.get_min_goal_time(url,goal)
          else:
            min_completion_time = -1
        except IndexError:
          donation_count = duration = recent_donation_time = raised = goal = min_completion_time = 0
          
        return OrderedDict({'category':category,'page':page,'title':title, 'href':url, 'location':location,'start_date':start_date ,'goal':goal 
                            ,'raised':raised, 'text':text ,'likes':likes,'shares':shares, 'photos':photos,  'donation_count':donation_count
                            ,'duration':duration, 'recent_donation_time':recent_donation_time , 'goal_reaeched_time':min_completion_time
                            ,'script_run_time':datetime.today().strftime("%Y-%m-%d")})

    def get_min_goal_time(self,href,goal):
        goal=int(re.sub('[^\d]','',goal))
        campaign = href[25:]
        idx = 0
        min_completion_time = 0
        donation = []
        time_gap=[]
        while True:
            url = 'https://www.gofundme.com/mvc.php?route=donate/pagingDonationsFoundation&url='+campaign+'&idx='+str(idx)+'&type=recent'
            soup = requests.get(url)
            soup=bs(soup.text,'html.parser')
            dn = [i.text for i in soup.findAll(class_='supporter-amount')]
            if len(dn)<1:break
            donation = donation + dn
            time_gap = time_gap+ [i.text[:-4] for i in soup.findAll(class_='supporter-time')]
            idx+=10
            if idx%100==0:
              print('.',end='')
        l=[int(re.sub('[^\d]','',i)) for i in donation[::-1]]
        d=list(accumulate(l))
        for i in range(len(d)):
          if d[i]>goal:
            return time_gap[-i-1]

    def get_campaigns(self,categories = 'all',path=os.getcwd(),skip = ['']):
        start_time = time()
        df = pd.DataFrame({})
        if categories == 'all':
          categories = self.get_categories()
        campaigns =self.read_data(path)
        for i in categories:
          if i in skip:
            continue
          print(i,end='  ')
          i='-'.join(i.split(' '))
          i = 'animal' if i == 'Animals' else i
          url = 'https://www.gofundme.com/discover/'+i+'-fundraiser'
          soup = bs(requests.get(url).text,'html.parser')
          cid = re.findall('\d+',re.findall('cid=\'\s\+\s\'\d+', soup.find_all('script')[13].text)[0])[0]
          if campaigns.loc[campaigns.category==i].shape[0]>0:
            page = campaigns.loc[campaigns.category ==i,'page'].max()+1
          else:
            page = 1
            
          while True:
            print('\n',page)
            url = 'https://www.gofundme.com/mvc.php?route=categorypages/load_more&page='+str(page)+'&term=&cid='+cid
            soup = requests.get(url)
            soup = bs(soup.text, 'html.parser')
            if len(soup) <1: break
            details =defaultdict(list)
            href = [i['href'] for i in soup.findAll('a',attrs={'class':'campaign-tile-img--contain'})]
            for link in href:
              for key, value in self.details_parser(link,i,page).items():
                details[key].append(value)
            if len(details)>0:   
              df = pd.DataFrame(details)[self.campaign_columns]
              df.to_csv('campaigns.csv',index=False,header=False,mode='a')
            #if (page%50==0):break
            page+=1        
                
          print('\n')
        #clear_output()
        print('campaigns scrape time', time()-start_time)


if __name__ == '__main__':
    path = 'G:\\My Drive\\codelab\\gofundme'
    #path = os.getcwd()
    scraper = web_scraper()
    #scraper.git_clone()
    #scraper.get_campaigns() 
    #scraper.git_push()
