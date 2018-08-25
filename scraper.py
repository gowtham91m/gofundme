# -*- coding: utf-8 -*-
"""Scraper.ipynb
author: Gowtham Mallikarjuna

%%capture
!pip install "requests[security]"
"""

from bs4 import BeautifulSoup as bs
import requests
from IPython.display import display, clear_output
import re
import pandas as pd
from time import time
from collections import defaultdict
#from google.colab import files
from collections import OrderedDict
import os

path = 'G:\\My Drive\\codelab\\gofundme'
os.chdir(path)

class web_scraper:
    def __init__(self):
        self.url = 'https://www.gofundme.com/discover'

    def get_categories(self):
        soup = requests.get(url)
        soup = bs(soup.text,'html.parser')
        category = soup.findAll(class_='text-black')
        categories = [i.text for i in category]  
        return categories[:8]

    def details_parser(self,url):

        soup=bs(requests.get(url).text,'html.parser')

        try: text = soup.findAll(class_="co-story truncate-text truncate-text--description js-truncate")[0].text.strip()
        except: text = 'exception occured for' + url
          
        try: likes =  soup.findAll(class_='roundedNum')[0].text
        except IndexError: likes = 0
          
        try: photos = soup.findAll(class_='open-media-viewer')[0].text.strip()
        except IndexError: photos = 0

        try: shares = soup.findAll(class_='js-share-count-text')[0].text.strip()
        except IndexError: shares = 0
          
        try: 
          donation = soup.findAll(class_='campaign-status text-small')[0].text.strip()
          donation = donation.split(' ')
          donation_count = donation[2]
          duration = ' '.join(donation[-2:])
        except:
          donation_count = duration = 0

        return({'text':text, 'likes':likes, 'photos':photos, 'shares':shares, 'donation_count':donation_count, 'duration':duration})

    def scrape(self,categories = 'all'):
        start_time = time()
        df = pd.DataFrame({})
        if categories == 'all':
          categories = self.get_categories()
        for i in categories:
          print(i,end='  ')
          i='-'.join(i.split(' '))
          i = 'animal' if i == 'Animals' else i
          url = 'https://www.gofundme.com/discover/'+i+'-fundraiser'
          soup = bs(requests.get(url).text,'html.parser')
          cid = re.findall('\d+',re.findall('cid=\'\s\+\s\'\d+', soup.find_all('script')[13].text)[0])[0]
          page = 1
          while True:
            url = 'https://www.gofundme.com/mvc.php?route=categorypages/load_more&page='+str(page)+'&term=&cid='+cid
            soup = requests.get(url)
            soup = bs(soup.text, 'html.parser')
            if len(soup) <1: break
            name = [ hit.text  for hit in soup.findAll(attrs={'class' : 'fund-title truncate-single-line show-for-medium'})]
            href = [i['href'] for i in soup.findAll('a',attrs={'class':'campaign-tile-img--contain'})]
            location = [i.text[1:-1] for i in soup.findAll(class_='fund-item fund-location truncate-single-line')]

            raised=[]
            goal=[]
            for k in soup.findAll(class_="fund-item truncate-single-line"):
              if len(re.findall('\$\d+.*',k.text))>0:
                raised.append(re.findall('\$\d+.*',k.text)[0].split(' ')[0])
                goal.append(re.findall('\$\d+.*',k.text)[0].split(' ')[3])
              else:
                raised.append(0)
                goal.append(0)

            details =defaultdict(list)
            for link in soup.findAll('a',attrs={'class':'campaign-tile-img--contain'}):
              for key, value in self.details_parser(link['href']).items():
                details[key].append(value)
            
            df = df.append(pd.DataFrame({'category':[i]*len(name),
                                         'name':name,
                                         'href':href,
                                         'location':location, 
                                         'goal':goal,
                                         'raised':raised,
                                         'text':details['text'],
                                         'likes':details['likes'],
                                         'shares':details['shares'],
                                         'photos':details['photos'],
                                         'donation_count':details['donation_count'],
                                         'duration':details['duration']}))
            if (page%10==0):print(page,end=' ')
            page+=1
          print('\n')
        clear_output()
        columns = ['category','name','href','location','goal','raised','text','likes','shares','photos','donation_count','duration']
        print('campaigns scrape time', time()-start_time)
        return df[columns]

    def get_donation_amount(self,href):
    #start_time = time()
        donation_data = pd.DataFrame({})
        campaign = href[25:]
        idx = 0
        count = 0
        print(href)
        while True:
            url = 'https://www.gofundme.com/mvc.php?route=donate/pagingDonationsFoundation&url='+campaign+'&idx='+str(idx)+'&type=recent'
            soup = requests.get(url)
            soup=bs(soup.text,'html.parser')
            donation = [i.text for i in soup.findAll(class_='supporter-amount')]
            if len(donation)<1:break
            time_gap = [i.text[:-4] for i in soup.findAll(class_='supporter-time')]
            donation_data = donation_data.append(pd.DataFrame({'href':[href]*len(donation),
                                                               'donation_amount':donation,
                                                               'time':time_gap}))
            idx+=10
            if ((count-10)%100==0):print(donation_data.shape[0],end=' ')
            count+=1
        #clear_output()
        #print('donation amount scrape time', time()-start_time)
        columns = ['href','donation_amount','time']
        return donation_data[columns]

    def update_donations(self,df):
        donation_href_unique = []
        donations = pd.DataFrame({'href':[],'donation_amount':[],'time':[]})
        donations = donations[['href','donation_amount','time']]
        if 'donations.csv' not in os.listdir():
            donations.to_csv('donations.csv')
        else:
            count = 1
            for i in  pd.read_csv('donations.csv',chunksize=1000000):
                print('reading chunk ',count)
                for k in i.href.unique():
                    if k not in donation_href_unique:
                        donation_href_unique.append(k)

        count = 0
        for a in df.href:
            start_time = time()
            if a not in donation_href_unique:
                donations = donations.append(self.get_donation_amount(a))
                donations.to_csv('donations.csv',mode='a',index=False,header=False)
            count +=1
            print(count,' ',round(time()-start_time))

    
scraper = web_scraper()
#scraper.get_categories()
#campaign = scraper.scrape(['Medical'])
#campaign.to_csv('campaign.csv',mode='a',index=False,header=False)

campaign = pd.read_csv('campaign.csv')
scraper.update_donations(campaign)

# Merge campaign_data and donation_data on name




    
