from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BS4
import time
import os
import pickle

USERNAME = ''
PASSWORD = ''

class Glassdoor(object):
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.page_source = ''
        self.login()

    def restart(self):
        self.__init__()

    def login(self):
        try:
            self.driver.get('https://www.glassdoor.com/profile/joinNow_input.htm?hs=true&userOriginHook=GIVETOGET_HARDSELL')
            if os.path.exists('cookies.pkl'):
                cookies = pickle.load(open("cookies.pkl", "rb"))
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            else:
                time.sleep(5)
                self.driver.find_element_by_class_name('login-signin').click()
                time.sleep(1)
                self.driver.find_element_by_name('username').send_keys(USERNAME+Keys.TAB+PASSWORD+Keys.ENTER)
                pickle.dump( self.driver.get_cookies() , open("cookies.pkl","wb"))
            time.sleep(1)
        except WebDriverException:
            print 'An error occured, Rebooting Driver.'
            self.restart()
            return self.login()


    def get_review_page_source(self, url):
        try:
            self.driver.get(url)
            while not self.driver.current_url.split('glassdoor.com')[1:] == url.split('glassdoor.com')[1:]:
                time.sleep(1)
            while not self.driver.find_elements_by_class_name('next'):
                print 'waiting for page to load..'
                time.sleep(2)
            time.sleep(1)
            self.page_source = self.driver.page_source
            return self.driver.page_source
        except WebDriverException:
            print 'An error occured, Rebooting Driver.'
            self.restart()
            return self.get_review_page_source(url)

    def parse_reviews_page(self):
        reviews = []
        soup = BS4(self.page_source)
        review_divs = soup.find_all('div', {'class':'hreview'})

        for div in review_divs:
            date = div.find('tt', {'class':'SL_date margBot5'}).text.strip()
            title = div.find('span', {'class':'summary'}).text.strip()
            rating = div.find('span', {'class':'value-title'}).get('title').strip()

            position_status = div.find('span', {'class':'authorJobTitle'})
            if position_status:
                position_status = position_status.contents

                status_text = position_status[0].split()[0].strip()
            
                position_text = position_status[1].text.strip()
                
                location = div.find('span', {'class':'authorLocation'})
                location_text = location.text.strip() if location else ''
            
            else:
                status_text, position_text, location_text = '', '', ''

            content_body = div.find('div', {'class':'cell reviewBodyCell'})
            misc = content_body.contents[1]
            misc_text = misc.text.strip() if str(misc).strip().startswith('<p>') else ''

            pros = content_body.find('p', {'class':'pros noMargVert notranslate '})
            pros_text = pros.text.strip() if pros else ''


            cons = content_body.find('p', {'class':'cons noMargVert notranslate '})
            cons_text = cons.text.strip() if cons else ''

            management_advice = content_body.find('p', {'class':'adviceMgmt noMargVert notranslate '})
            management_advice_text = management_advice.text.strip() if management_advice else ''

            outlook_div = div.find('div', {'class':'tbl fill outlookEmpReview'})
            outlook = {'recommends':None, 'approves':None, 'outlook':None}
            for item in outlook_div.find_all('div', {'class':'middle'}):
                if 'Recommends' in item.text:
                    if 'green' in item.find('i').get('class'):
                        outlook['recommends'] = "1"
                    elif 'yellow' in item.find('i').get('class'):
                        outlook['recommends'] = "0"
                    elif 'red' in item.find('i').get('class'):
                        outlook['recommends'] = "-1"
                
                elif 'Outlook' in item.text:
                    if 'green' in item.find('i').get('class'):
                        outlook['outlook'] = "1"
                    elif 'yellow' in item.find('i').get('class'):
                        outlook['outlook'] = "0"
                    elif 'red' in item.find('i').get('class'):
                        outlook['outlook'] = "-1"
            
            for item in outlook_div.find_all('div', {'class':'cell'}):
                if item.find('i') and item.find('span', {'class':'showDesk'}):
                    if 'green' in item.find('i').get('class'):
                        outlook['approves'] = "1"
                    elif 'yellow' in item.find('i').get('class'):
                        outlook['approves'] = "0"
                    elif 'red' in item.find('i').get('class'):
                        outlook['approves'] = "-1"
            
            review = {  
                        'date':date,
                        'headline':title,
                        'rating':rating,
                        'position':position_text,
                        'status':status_text,
                        'location':location_text,
                        'misc':misc_text,
                        'pros':pros_text,
                        'cons':cons_text,
                        'management_advice': management_advice_text,
                        'recommends':outlook['recommends'],
                        'outlook':outlook['outlook'],
                        'approves_ceo':outlook['approves']     
                    }
            reviews.append(review)
        return reviews


    def get_next_page(self):
        time.sleep(3)
        soup = BS4(self.page_source)
        nextpage = soup.find('li', {'class':'next'})
        if nextpage.find('a'):
            next_page_url = 'http://glassdoor.com'+nextpage.find('a').get('href')
            return next_page_url
        else:
            return None
