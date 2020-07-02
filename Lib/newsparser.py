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

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOption
from selenium.common.exceptions import NoSuchElementException


class newsParserData(object):
    URL = "https://www.krjogja.com/berita-terkini/"
    xcontainer = ""
    logger = None
    config = None
    driver = None
    cookies = None

    def __init__(self, path_to_webdriver, logger=None, cookies=None):
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

    def __del__(self):
        self.driver.quit()

    def getRequest(self):
        web_r = requests.get(self.URL)
        #urlpage = urllib.request.urlopen(self.URL
        req = Request(self.URL)
        urlpage = urlopen(req).read()

        #self.driver.get(self.URL)
        self.driver.implicitly_wait(40)
        time.sleep(10)
        #html = self.driver.execute_script("return document.documentElement.outerHTML")
        sel_soup = BeautifulSoup(urlpage, 'html.parser')
        #images = []
        #for i in sel_soup.findAll("img"):
         #   print(i)
        #    src = i["src"]
         #   images.append(src)

        print(sel_soup)

    def getElement(self):
        return self


class newsParsing(object):
    config = None
    logger = None
    filename = ""
    iphelper = None
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


    def run(self):
        self.init()
        self.hostname = socket.gethostname()
        self.hostip = socket.gethostbyname(self.hostname)
        self.logger.info("Starting {} on {}".format(type(self).__name__, self.hostname))
        self.newsParserData = newsParserData(logger=self.logger, path_to_webdriver=self.config.get('Selenium', 'chromedriver_path'))
        self.newsParserData.getRequest()
        #self.shopeeParser.getElement()
        self.logger.info("Finish %s" % self.filename)