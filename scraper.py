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
import os

class web_scraper:
    def __init__(self):
        self.url = 'https://www.gofundme.com/discover'
        self.campaign_columns = ['category','name','href','location','goal','raised',
                   'text','likes','shares','photos','donation_count','duration','recent_donation_time']

    def get_categories(self):
        soup = requests.get(self.url)
        soup = bs(soup.text,'html.parser')
        category = soup.findAll(class_='text-black')
        categories = [i.text for i in category]  
        return categories[:16]

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
          recent_donation_time = soup.findAll(class_='supporter-time')[0].text.strip()
          donation = donation.split(' ')
          donation_count = donation[2]
          duration = ' '.join(donation[-2:])
        except:
          donation_count = duration = recent_donation_time = 0

        return({'text':text, 'likes':likes, 'photos':photos, 'shares':shares,
                'donation_count':donation_count, 'duration':duration
                ,'recent_donation_time':recent_donation_time})

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
                                         'duration':details['duration'],
                                         'recent_donation_time': details['recent_donation_time']}))
            if (page%10==0):
                print(page,end=' ')
                #break
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
