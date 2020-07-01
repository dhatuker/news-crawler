from Lib.newsparser import newsParserData, newsParsing

def main():
    news = newsParsing()
    news.run()
    del news


if __name__ == '__main__':
    main()