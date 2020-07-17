import sys

from Lib.newsparser import newsParserData, newsParsing

def main():
    news = newsParsing()
    news.run(sys.argv[1])
    del news

if __name__ == '__main__':
    main()