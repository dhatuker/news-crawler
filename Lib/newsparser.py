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
    URL = "https://www.krjogja.com/berita-terkini/"
    # URL = "https://www.todayonline.com/singapore"
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
        self.driver.implicitly_wait(30)
        time.sleep(10)

    def scroll_down(self):
        SCROLL_PAUSE_TIME = 10

        for i in range(3):
            # Scroll down to bottom     
            self.driver.execute_script("window.scrollTo(0, 2000);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

    def convertMonth(self, month, news_id):
        month = month.lower()
        months = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober',
                  'november', 'desember']
        months_en = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
                     'november', 'december']
        if news_id == 1:
            return months.index(month) + 1
        elif news_id == 2:
            return months_en.index(month) + 1

    def toDate(self, input, news_id):
        re_date = r"(\d{1,2}) ([A-Za-z]+).? (\d{4})"
        output = re.search(re_date, input)
        date = output.group(1)
        month = output.group(2)
        month_ = self.convertMonth(month, news_id)
        year = output.group(3)
        return str(year) + "-" + str(month_) + "-" + str(date)

    def getElement(self):
        self.openLink()
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        if 'krjogja' in self.URL:
            news_id = 1
            link = soup.find_all(lambda tag: tag.name == 'h4' and tag['class'] == ['post-list__title'])

            for i in link:
                news_link = i.find('a', attrs={'href': re.compile("^https://")})
                if news_link is not None:
                    url = news_link.get('href')
                    soup = self.openNewsLink(url)
                    self.findDataKR(url, soup, news_id)

        elif 'todayonline' in self.URL:
            news_id = 2

            self.scroll_down()
            time.sleep(5)

            regex = re.compile('article-listing_.\sfeatured')

            link = soup.find_all('div', class_=regex)

            for i in link:
                news_link = i.find('a', attrs={'href': re.compile("^/singapore/")})
                if news_link is not None:
                    url = "https://www.todayonline.com" + news_link.get('href')
                    soup = self.openNewsLink(url)
                    self.findDataTO(url, soup, news_id)

    def openNewsLink(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(10)
        time.sleep(5)
        self.scroll_down()
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        return soup

    def findDataKR(self, url, soup, news_id):
        self.logger.info("news_id : {}".format(news_id))

        title = soup.find('h1', class_='single-header__title').text
        self.logger.info("title : {}".format(title))

        tanggal = soup.find('div', class_='post-date').text
        tanggal_ = self.toDate(tanggal, news_id)
        self.logger.info("tanggal : {}".format(tanggal_))

        editor = soup.find('div', class_='editor')
        editor_name = editor.find('a', attrs={'href': re.compile("^https://")}).text
        self.logger.info("editor : {}".format(editor_name))

        share = "-"
        self.logger.info("share : {}".format(share))

        news_content = soup.find('div', class_='content')
        p = news_content.find_all('p')
        content = ' '.join(item.text for item in p)

        iframe = self.driver.find_elements_by_xpath('.//iframe[@class="i-amphtml-fill-content"]')
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(iframe[5])
        iframe = self.driver.find_element_by_xpath('.//iframe[1]')
        self.driver.switch_to.frame(iframe)
        comment = self.driver.find_element_by_xpath('.//span[@class=" _50f7"]')
        if comment is not None:
            comment_ = comment.text
        else:
            comment_ = "-"
        self.logger.info("comment : {}".format(comment_))

        page = soup.find("div", class_='pagination')
        if page is not None:
            paging_link = page.find_all(lambda tag: tag.name == 'a' and tag['class'] == ['post-page-numbers'])
            for i in range(len(paging_link) - 1):
                link_ = url + str(i + 2) + "/"
                soup_ = self.openNewsLink(link_)
                news_content = soup_.find("div", class_='content')
                p = news_content.find_all('p')
                content_ = ' '.join(item.text for item in p)
                content = content + " " + content_
        self.logger.info("content : {}".format(content))

        self.db.insert_news(news_id, title, content, tanggal_, comment_, share, editor_name, url)

    def findDataTO(self, url, soup, news_id):
        self.logger.info("news_id : {}".format(news_id))

        title = soup.find('h1', class_='article-detail_title').text
        self.logger.info("title : {}".format(title))

        editor = soup.find('span', class_='today-author')
        if editor is not None:
            editor_name = editor.text
        else:
            editor_name = "-"
        self.logger.info("editor : {}".format(editor_name))

        tanggal = soup.find('div', class_='article-detail_bylinepublish').text
        tanggal_ = self.toDate(tanggal, news_id)
        self.logger.info("tanggal : {}".format(tanggal_))

        news_content = soup.find("div", class_='article-detail_body')
        p = news_content.find_all('p')
        content = ' '.join(item.text for item in p)
        self.logger.info("content : {}".format(content))

        share = soup.find('p', class_='share-count-common share-count').text
        self.logger.info("share : {}".format(share))

        comment = "-"
        self.logger.info("comment : {}".format(comment))

        self.db.insert_news(news_id, title, content, tanggal_, comment, share, editor_name, url)


class newsParsing(object):
    config = None
    logger = None
    filename = ""
    iphelper = None
    db = None
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
        logbook.set_datetime_format("local")
        self.logger = logbook.Logger(name=self.filename)
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
        self.newsParserData = newsParserData(db=self.db, logger=self.logger,
                                             path_to_webdriver=self.config.get('Selenium', 'chromedriver_path'))
        self.newsParserData.getElement()
        self.logger.info("Finish %s" % self.filename)
