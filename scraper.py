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

class web_scraper:
    def __init__(self):
        self.url = 'https://www.gofundme.com/discover'
        self.campaign_columns = ['category','name','href','location','start_date','goal','raised',
                               'text','likes','shares','photos','donation_count','duration',
                                 'recent_donation_time','goal_reaeched_time','script_run_time']

    def get_categories(self):
        soup = requests.get(self.url)
        soup = bs(soup.text,'html.parser')
        category = soup.findAll(class_='text-black')
        categories = [i.text for i in category]  
        return categories[:16]

    def details_parser(self,url):
        soup=bs(requests.get(url).text,'html.parser')

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
         
        #start_date = 0
        raised = 0
        goal = 0
        try: 
          donation = soup.findAll(class_='campaign-status text-small')[0].text.strip()
          recent_donation_time = soup.findAll(class_='supporter-time')[0].text.strip()
          donation = donation.split(' ')
          donation_count = donation[2]
          duration = ' '.join(donation[-2:])
          funds  = soup.findAll('h2',class_='goal')[0].text
          raised = re.findall('\$\d+.*',funds)[0]
          goal = re.findall('\$\d+.*',funds)[1].split(' ')[0]
          
          print(url[25:],raised,'/',donation_count,' ',end='')
          if int(re.sub('[^\d]','',raised)) >= int(re.sub('[^\d]','',goal)):
            min_completion_time = self.get_min_goal_time(url,goal)
          else:
            min_completion_time = 0
        except IndexError:
          donation_count = duration = recent_donation_time = raised = goal = min_completion_time = 0

        return({'text':text, 'likes':likes, 'photos':photos, 'shares':shares,
                'donation_count':donation_count, 'duration':duration
                ,'recent_donation_time':recent_donation_time,'raised':raised,
                'goal':goal, 'min_completion_time':min_completion_time,'start_date':start_date})

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
            if idx%100==0:print('.',end='')
        print('\n')
        l=[int(re.sub('[^\d]','',i)) for i in donation[::-1]]
        d=list(accumulate(l))
        for i in range(len(d)):
          if d[i]>goal:
            return time_gap[-i-1]

    def get_campaigns(self,categories = 'all'):
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
            print(page)
            url = 'https://www.gofundme.com/mvc.php?route=categorypages/load_more&page='+str(page)+'&term=&cid='+cid
            soup = requests.get(url)
            soup = bs(soup.text, 'html.parser')
            if len(soup) <1: break
            name = [ hit.text  for hit in soup.findAll(attrs={'class' : 'fund-title truncate-single-line show-for-medium'})]
            href = [i['href'] for i in soup.findAll('a',attrs={'class':'campaign-tile-img--contain'})]
            location = [i.text[1:-1] for i in soup.findAll(class_='fund-item fund-location truncate-single-line')]
            details =defaultdict(list)
            for link in soup.findAll('a',attrs={'class':'campaign-tile-img--contain'}):
              for key, value in self.details_parser(link['href']).items():
                details[key].append(value)
            
            df = df.append(pd.DataFrame({'category':[i]*len(name),
                                         'name':name,
                                         'href':href,
                                         'location':location,
                                         'start_date':details['start_date'],
                                         'raised':details['raised'],
                                         'goal':details['goal'],
                                         'text':details['text'],
                                         'likes':details['likes'],
                                         'shares':details['shares'],
                                         'photos':details['photos'],
                                         'donation_count':details['donation_count'],
                                         'duration':details['duration'],
                                         'recent_donation_time': details['recent_donation_time'],
                                         'goal_reaeched_time':details['min_completion_time'],
                                         'script_run_time':[datetime.today().strftime("%Y-%m-%d")]*len(name) }))
            
            if (page%1==0): break
            page+=1
          print('\n')
        clear_output()
        print('campaigns scrape time', time()-start_time)
        return df[self.campaign_columns]

    def scrape(self,path):
        os.chdir(path)
        if 'campaigns.csv' not in os.listdir():
            campaign_data = pd.DataFrame({i:[] for i in self.campaign_columns})
            campaign_data = campaign_data[self.campaign_columns]
            existing_categories = []
            campaign_data.to_csv('campaigns.csv',index=False)
        else:
            campaign_data = pd.read_csv('campaigns.csv')
            existing_categories = campaign_data.category.unique()
            
        for i in self.get_categories():
            if i not in existing_categories:
                campaigns = self.get_campaigns([i])
                campaigns.to_csv('campaigns.csv',mode='a',index=False,header=False)


if __name__ == '__main__':
    path = 'G:\\My Drive\\codelab\\gofundme'
    #path = os.getcwd()
    web_scraper().scrape(path)
