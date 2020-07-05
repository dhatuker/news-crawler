import requests
import logbook
import time
import re
import sys
import argparse
import configparser
import os
import socket
from urllib.request import Request, urlopen
from db.newsparserDatabaseHandler import newsparserDatabaseHandler

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption
from selenium.common.exceptions import NoSuchElementException


class newsParserData(object):
    #URL = "https://www.krjogja.com/berita-terkini/"
    URL = "https://www.todayonline.com/singapore"
    logger = None
    config = None
    driver = None
    cookies = None

    def __init__(self, db, path_to_webdriver, logger=None, cookies=None):
        self.logger = logger
        self.logger.info("webdriver path: ".format(path_to_webdriver))

        chrome_options = ChromeOption()

        prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        # automatically dismiss prompt
        chrome_options.set_capability('unhandledPromptBehavior', 'dismiss')

        self.driver = webdriver.Chrome(path_to_webdriver, chrome_options=chrome_options)

        if cookies is None:
            self.cookies = self.driver.get_cookies()
        else:
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.cookies = cookies
        self.db = db

    def __del__(self):
        self.driver.quit()

    def openLink(self):
        self.driver.get(self.URL)

    def scroll_down(self):
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:

            # Wait to load the page.
            time.sleep(5)

            # Scroll down to the bottom.
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

    def getElementKR(self):
        self.openLink()
        self.driver.implicitly_wait(40)
        time.sleep(10)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        newsLink = []
        link = soup.find_all(lambda tag: tag.name == 'h4' and tag['class'] == ['post-list__title'])

        for i in link:
            news_link = i.find('a', attrs={'href': re.compile("^https://")})
            if news_link is not None:
                newsLink.append(news_link.get('href'))
        print(newsLink)
        self.openNewsLinkKR(newsLink)


    def openNewsLinkKR(self, newsLink):
        for link in newsLink:
            self.driver.get(link)
            self.driver.implicitly_wait(20)
            # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(20)
            self.findDataTO(link)

    def convertMonth(self, month, news_id):
        month = month.lower()
        months = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember']
        months2 = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
        if news_id == 1:
            return months.index(month) + 1
        elif news_id == 2:
            return months2.index(month) + 1

    def toDate(self, input, news_id):
        re_date = r"(\d{1,2}) ([A-Za-z]+).? (\d{4})"
        output = re.search(re_date, input)
        date = output.group(1)
        month = output.group(2)
        month_ = self.convertMonth(month, news_id)
        year = output.group(3)
        return str(year)+"-"+str(month_)+"-"+str(date)

    def findDataKR(self, link):
        page_source = self.driver.page_source

        share = "-"
        comment = "-"

        soup = BeautifulSoup(page_source, 'lxml')
        news_content = soup.find("div", {'class': 'content'})
        page = soup.find("div", class_='pagination')
        p = news_content.find_all('p')
        content = ' '.join(item.text for item in p)
        if page is not None:
            paging_link = page.find_all(lambda tag: tag.name == 'a' and tag['class'] == ['post-page-numbers'])
            for i in range(len(paging_link) - 1):
                link_ = link + str(i + 2) + "/"
                self.driver.get(link_)
                self.driver.implicitly_wait(20)
                time.sleep(20)
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')
                news_content = soup.find("div", {'class': 'content'})
                page = soup.find("div", class_='pagination')
                p = news_content.find_all('p')
                content_ = ' '.join(item.text for item in p)
                content = content + " " + content_

        title = soup.find('h1', class_='single-header__title').text
        if "krjogja" in link :
            news_id=1
        tanggal = soup.find('div', class_='post-date').text
        tanggal_ = self.toDate(tanggal, news_id)
        editor = soup.find('div', class_='editor')
        editor_name = editor.find('a', attrs={'href': re.compile("^https://")}).text
        #comment = soup.find('span', class_=' _50f7')
        #comment = './/div[@class=" _50f7"]'
        #com = self.driver.find_elements_by_xpath(comment)
        self.db.insert_news(news_id, title, content, tanggal_, share, comment, editor_name, link)

    def getElementTO(self):
        self.openLink()
        self.driver.implicitly_wait(40)
        self.scroll_down()
        time.sleep(15)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        newsLink = []

        regex = re.compile('article-listing_.\sfeatured')

        link = soup.find_all('div', class_=regex)

        for i in link:
            news_link = i.find('a', attrs={'href': re.compile("^/singapore/")})
            if news_link is not None:
                newsLink.append("https://www.todayonline.com" + news_link.get('href'))
        self.openNewsLinkTO(newsLink)

    def openNewsLinkTO(self, newsLink):
        for link in newsLink:
            self.driver.get(link)
            #r = requests.get(link)
            #soup = BeautifulSoup(r.text, 'lxml')
            self.driver.implicitly_wait(40)
            #self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(15)
            #print(soup)
            self.findDataTO(link)
            #r.text

    #def findDataTO(self, link):

    def findDataTO(self, link):
        page_source = self.driver.page_source


        comment = "-"

        soup = BeautifulSoup(page_source, 'lxml')
        news_content = soup.find("div", {'class': 'article-detail_body'})
        p = news_content.find_all('p')
        content = ' '.join(item.text for item in p)

        title = soup.find('h1', class_='article-detail_title').text

        if "todayonline" in link :
            news_id=2

        tanggal = soup.find('div', class_='article-detail_bylinepublish').text
        tanggal_ = self.toDate(tanggal, news_id)

        share = soup.find('p', class_='share-count-common share-count').text

        editor = soup.find('span', class_='today-author')
        editor_name = editor.find('a', attrs={'href': re.compile("^mailto:")}).text

        print(news_id, link,  title, editor_name, tanggal_, share, "\n", content)
        #self.db.insert_news(news_id, title, content, tanggal_, share, comment, editor_name, link)


class newsParsing(object):
    config = None
    logger = None
    filename = ""
    iphelper = None
    db = None
    solrAccountHandler = None
    hostname = ''
    hostip = ''
    shopeeParser = None

    def init(self):

        self.filename, file_extension = os.path.splitext(os.path.basename(__file__))

        # parse argument
        parser = argparse.ArgumentParser()
        parser.add_argument("--configdir", help="your config.ini directory", type=str)
        parser.add_argument("--logdir", help="your log directory", type=str)
        args = parser.parse_args()

        # determine config directory
        if args.configdir:
            config_file = os.path.join(args.configdir, 'config.ini')
        else:
            config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../config', 'config.ini')

        if args.logdir:
            log_file = os.path.join(args.logdir, '%s.log' % self.filename)
        else:
            log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../logs', '%s.log' % self.filename)

        # load config
        self.config = configparser.ConfigParser(strict=False)
        self.config.read(config_file)

        # init logger
        # init logger
        logbook.set_datetime_format("local")
        self.logger = logbook.Logger(name=self.filename)
        # format_string = '%s %s' % ('[{record.time:%Y-%m-%d %H:%M:%S.%f%z}]',
        #                               # '{record.level_name} on {record.filename}:{record.lineno}:',
        #                               '{record.channel}:{record.lineno}: {record.message}')
        format_string = '%s %s' % ('[{record.time:%Y-%m-%d %H:%M:%S.%f%z}] {record.level_name}',
                                   '{record.channel}:{record.lineno}: {record.message}')
        if self.config.has_option('handler_stream_handler', 'verbose'):
            loghandler = logbook.StreamHandler(sys.stdout, level=self.config.get('Logger', 'level'), bubble=True,
                                               format_string=format_string)
            self.logger.handlers.append(loghandler)
            loghandler = logbook.TimedRotatingFileHandler(log_file, level=self.config.get('Logger', 'level'),
                                                          date_format='%Y%m%d', backup_count=5, bubble=True,
                                                          format_string=format_string)
            self.logger.handlers.append(loghandler)
        else:
            loghandler = logbook.TimedRotatingFileHandler(log_file, level=self.config.get('Logger', 'level'),
                                                          date_format='%Y%m%d', backup_count=5, bubble=True,
                                                          format_string=format_string)
            self.logger.handlers.append(loghandler)
        self.db = newsparserDatabaseHandler.instantiate_from_configparser(self.config, self.logger)

    def run(self):
        self.init()
        self.hostname = socket.gethostname()
        self.hostip = socket.gethostbyname(self.hostname)
        self.logger.info("Starting {} on {}".format(type(self).__name__, self.hostname))
        self.newsParserData = newsParserData(db=self.db, logger=self.logger, path_to_webdriver=self.config.get('Selenium', 'chromedriver_path'))
        self.newsParserData.getElementTO()
        #self.newsParserData.getElementKR()
        self.logger.info("Finish %s" % self.filename)
