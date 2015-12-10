from bs4 import BeautifulSoup as bs
import os, sys, logging, string, glob
import json
import re

from pyspark import SparkContext

def clean_text(text_as_list):
    text_as_string = " ".join(text_as_list)
    text_as_string = text_as_string.encode("utf8").translate(None,'=@&$/%?<>,[]{}()*.0123456789:;-\n\'"_').lower()
    text_as_string = re.sub(' +',' ',text_as_string)

    return text_as_string

def parse_page(input_page_as_tuple):
    filename,page = input_page_as_tuple
    soup = bs(page)

    filenameDetails = filename.split("/")
    urlid = filenameDetails[-1].split('_')[0]

    doc = {
            "id":urlid,
            "text":parse_text(soup),
            "title":parse_title(soup ),
            "links":parse_links(soup),
            "images":parse_images(soup),
           }

    return doc

def parse_text(soup):
    """ parameters:
            - soup: beautifulSoup4 parsed html page
        out:
            - textdata: a list of parsed text output by looping over html paragraph tags
        note:
            - could soup.get_text() instead but the output is more noisy """
    textdata = ['']

    for tag in soup.find_all("div", {"class":"text"}):
        try:
           textdata.append(tag.text.encode('ascii','ignore').strip())
        except Exception:
           continue

    for text in soup.find_all('p'):
        try:
            textdata.append(text.text.encode('ascii','ignore').strip())
        except Exception:
            continue

    textdata = filter(None,textdata)
    return clean_text(textdata)


def parse_title(soup):
    """ parameters:
            - soup: beautifulSoup4 parsed html page
        out:
            - title: parsed title """

    title = ['']

    try:
        title.append(soup.title.string.encode('ascii','ignore').strip())
    except Exception:
        return title

    return filter(None,title)

def parse_links(soup):
    """ parameters:
            - soup: beautifulSoup4 parsed html page
        out:
            - linkdata: a list of parsed links by looping over html link tags
        note:
            - some bad links in here, this could use more processing """

    linkdata = ['']

    for link in soup.find_all('a'):
        try:
            linkdata.append(str(link.get('href').encode('ascii','ignore')))
        except Exception:
            continue

    return filter(None,linkdata)


def parse_images(soup):
    """ parameters:
            - soup: beautifulSoup4 parsed html page
        out:
            - imagesdata: a list of parsed image names by looping over html img tags """
    imagesdata = ['']

    for image in soup.findAll("img"):
        try:
            imagesdata.append("%(src)s"%image)
        except Exception:
            continue

    return filter(None,imagesdata)


def main(argv):
    sc = SparkContext(appName="WebScraper")
    fIn_rdd = sc.wholeTextFiles("/user/alexeys/BigDataCourse/web_dataset/2/").map(parse_page).map(lambda x: json.dumps(x))
    fIn_rdd.repartition(1).saveAsTextFile('/user/alexeys/BigDataCourse/web_dataset_preprocessed/')

if __name__ == "__main__":
   import time
   start = time.time()
   main(sys.argv)
   end = time.time()
   print "Elapsed time: ", end-start 