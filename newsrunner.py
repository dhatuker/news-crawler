from Lib.newsparser import newsParserData, newsParsing
import sys

def main():
    input = sys.argv[1]
    news = newsParsing()
    news.run(input)
    del news


if __name__ == '__main__':
    main()