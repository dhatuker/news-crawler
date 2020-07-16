import logbook
import time
import re
import sys
import argparse
import configparser
import os
import socket

from db.newsparserDatabaseHandler import newsparserDatabaseHandler
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption


class newsParserData(object):
    # URL = "https://www.krjogja.com/berita-terkini/"
    # URL = "https://www.todayonline.com/singapore"
    logger = None
    config = None
    driver = None
    cookies = None

    def __init__(self, db, path_to_webdriver, config=None, logger=None, cookies=None):
        self.logger = logger
        self.logger.info("webdriver path: ".format(path_to_webdriver))

        self.config = config

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

    def openLink(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(30)
        time.sleep(20)
        self.scroll_down()
        time.sleep(5)
        self.logger.info("start get link")
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        return soup

    def scroll_down(self):
        a = 0
        b = 2000

        for i in range(3):
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo({}, {});".format(a, b))
            a = b
            b += 2000

            # implicity
            self.driver.implicitly_wait(10)
            # Wait to load page
            time.sleep(10)

    def convertMonth(self, month, news_id):
        month = month.lower()
        months = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober',
                  'november', 'desember']
        months_en = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
                     'november', 'december']

        if months.count(month) > 0:
            return months.index(month) + 1
        elif months_en.count(month) > 0:
            return months_en.index(month) + 1

    def toDate(self, input, news_id):
        re_date = r"(\d{1,2}) ([A-Za-z]+).? (\d{4})"
        output = re.search(re_date, input)
        date = output.group(1)
        month = output.group(2)
        month_ = self.convertMonth(month, news_id)
        year = output.group(3)
        return str(year) + "-" + str(month_) + "-" + str(date)

    def getElement(self, input):

        news = self.db.get_sumber(input)

        # Get ID, URL, and REGEX
        news_id = news[0][0]
        url = news[0][1]
        recompile = news[0][2]

        soup = self.openLink(url)

        if 'krjogja' in url:
            link = soup.find_all(lambda tag: tag.name == 'h4' and tag['class'] == ['post-list__title'])

        elif 'todayonline' in url:
            regex = re.compile('article-listing_.\sfeatured')
            link = soup.find_all('div', class_=regex)

        for i in link:
            news_link = i.find('a', attrs={'href': re.compile(recompile)})
            if news_link is not None:
                if news_id == 1:
                    url = news_link.get('href')
                elif news_id == 2:
                    url = "https://www.todayonline.com" + news_link.get('href')
                soup = self.openNewsLink(url)
                self.findData(url, soup, news_id, news)

    def openNewsLink(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(5)
        time.sleep(3)
        self.scroll_down()
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        return soup

    def findData(self, url, soup, news_id, news):
        self.logger.info("news_id : {}".format(news_id))

        # Get any Parameter for Parsing
        title_tag = news[0][3]
        title_class = news[0][4]
        date_tag = news[0][5]
        date_class = news[0][6]
        editor_tag = news[0][7]
        editor_class = news[0][8]
        newscontent_tag = news[0][9]
        newscontent_class = news[0][10]
        page_tag = news[0][11]
        page_class = news[0][12]
        share_tag = news[0][13]
        share_class = news[0][14]
        iframe_comment = news[0][15]

        # title
        try:
            title = soup.find(title_tag, class_=title_class).text
        except:
            title = None

        self.logger.info("title : {}".format(title))

        # editor
        try:
            editor = soup.find(editor_tag, class_=editor_class)
            if editor is not None:
                editor_name = editor.text
                self.logger.info("editor : {}".format(editor_name))
            else:
                editor_name = None
                self.logger.info("there is no editor at all")
        except:
            editor_name = None
            self.logger.info("error, editor is not loading yet")

        # tanggal
        try:
            tanggal = soup.find(date_tag, class_=date_class).text
            tanggal_ = self.toDate(tanggal, news_id)
            self.logger.info("tanggal : {}".format(tanggal_))
        except:
            tanggal_ = None
            self.logger.info("error, tanggal is not loading yet")

        # share
        try:
            if share_tag is not None:
                share = soup.find(share_tag, class_=share_class).text
                self.logger.info("share : {}".format(share))
            else:
                share = None
                self.logger.info("there is no share at all")
        except:
            share = None
            self.logger.info("error, share is not loading yet")

        # content
        try:
            news_content = soup.find(newscontent_tag, class_=newscontent_class)
            p = news_content.find_all('p')
            content = ' '.join(item.text for item in p)
        except:
            content = None

        # comment
        try:
            if iframe_comment is not None:
                iframe = self.driver.find_elements_by_xpath(iframe_comment)
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(iframe[5])
                iframe = self.driver.find_element_by_xpath('.//iframe[1]')
                self.driver.switch_to.frame(iframe)
                comment = self.driver.find_element_by_xpath('.//span[@class=" _50f7"]')
                if comment is not None:
                    comment_ = comment.text
                    self.logger.info("comment found : {}".format(comment_))
                else:
                    comment_ = None
                    self.logger.info("comment not found")
            else:
                comment_ = None
                self.logger.info("no comment in this website")
        except:
            comment_ = None
            self.logger.info("error, comment does not load normally")

        # page
        page = soup.find(page_tag, class_=page_class)
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

        # self.db.insert_news(news_id, title, content, tanggal_, comment_, share, editor_name, url)


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
        self.config = configparser.ConfigParser(strict=False, allow_no_value=True)
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
        start_time = time.time()
        self.init()
        self.hostname = socket.gethostname()
        self.hostip = socket.gethostbyname(self.hostname)
        self.logger.info("Starting {} on {}".format(type(self).__name__, self.hostname))
        self.newsParserData = newsParserData(db=self.db,
                                             path_to_webdriver=self.config.get('Selenium', 'chromedriver_path'),
                                             config=self.config, logger=self.logger)
        self.newsParserData.getElement('2')
        self.logger.info("Finish %s" % self.filename)
        print("--- %s seconds ---" % (time.time() - start_time))
