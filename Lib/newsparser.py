import requests
import logbook
import time
import re
import sys
import argparse
import configparser
import os
import socket
import requests
from urllib.request import Request, urlopen
from db.newsparserDatabaseHandler import newsparserDatabaseHandler

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption
from selenium.common.exceptions import NoSuchElementException


class newsParserData(object):
    URL = "https://www.krjogja.com/berita-terkini/"
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

    def getElement(self):
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
        self.openNewsLink(newsLink)


    def openNewsLink(self, newsLink):
        for link in newsLink:
            self.driver.get(link)
            self.driver.implicitly_wait(20)
            #self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(20)
            self.findData(link)

    def convertMonth(self, month):
        months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        return months.index(month) + 1

    def toDate(self, input):
        re_date = r"(\d{1,2}) ([A-Za-z]+) (\d{4})"
        output = re.search(re_date, input)
        date = output.group(1)
        month = output.group(2)
        month_ = self.convertMonth(month)
        year = output.group(3)
        return str(year)+"-"+str(month_)+"-"+str(date)

    def findData(self, link):
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
            for i in range(len(paging_link)-1):
                link_ = link + str(i+2) + "/"
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
        tanggal_ = self.toDate(tanggal)
        editor = soup.find('div', class_='editor')
        editor_name = editor.find('a', attrs={'href': re.compile("^https://")}).text
        #comment = soup.find('span', class_=' _50f7')
        #comment = './/div[@class=" _50f7"]'
        #com = self.driver.find_elements_by_xpath(comment)
        self.db.insert_news(news_id, title, content, tanggal_, share, comment, editor_name, link)

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
        self.newsParserData.getElement()
        self.logger.info("Finish %s" % self.filename)