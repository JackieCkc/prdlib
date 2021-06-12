import requests
import urllib.request as urllib2

from bs4 import BeautifulSoup as bs
from os import listdir
from os.path import isfile, join

START = 'startWithMe.html'
ROOT = 'http://prdlib.convoy.com.hk/prdportal/'
URL = ROOT + 'Default.aspx?menuid=11'
DEFAULT = '../Default_files'
FILE = '../File'
HTML = '../html'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded",
    "Upgrade-Insecure-Requests": "1"
}


def transformAndDownloadHTML(href):
    # transform stuff like `javascript:__doPostBack('repeater3$ctl01$repeater4$ctl06$btnMenu4','')`
    # to `repeater3%24ctl01%24repeater4%24ctl06$btnMenu4` so we can get the actual HTML file via curl
    href = href[25:]
    href = href[:href.find("'")]
    href.replace('$', '%24')

    body = open('curl.txt').readlines()[0].replace('"replace"', href)
    print(f"downloading HTML {href}...")
    r = requests.post(URL, data=body, headers=HEADERS)
    with open(f"{HTML}/{href}.html", 'w') as fd:
        fd.write(r.text)


def downloadAllHTML():
    f = open(START, 'r+')
    soup = bs(f.read(), features="html.parser")

    for link in soup.findAll('a'):
        href = link.attrs['href']
        if (href.startswith('javascript:__doPostBack')):
            transformAndDownloadHTML(href)


def processAllHTML():
    for file in listdir(HTML):
        if isfile(join(HTML, file)):
            processHTML(join(HTML, file))


def renameCSSAndJS(soup):
    for link in soup.findAll('link'):
        name = link.attrs['href']
        name = DEFAULT + name[name.rfind('/'):]
        link.attrs['href'] = name

    for link in soup.findAll('script', {"src": True}):
        name = link['src']
        name = DEFAULT + name[name.rfind('/'):]
        link['src'] = name


def renameNavigationLinks(soup):
    for link in soup.findAll('a'):
        name = link.attrs['href']
        if name.startswith("javascript:__doPostBack('repeater"):
            href = link.get('href')
            href = href[25:href.find("'")].replace('$', '%24')
            link.attrs['href'] = href + '.html'


def downloadAndRenamePDFPaths(soup):
    for link in soup.findAll('a'):
        name = link.attrs['href']
        if not name.endswith('.pdf'):
            continue

        r = requests.get(ROOT + name, stream=True)
        print(f"downloading PDF to '{name}'")
        with open(FILE + name[name.rfind('/'):], 'wb') as fd:
            for chunk in r.iter_content(2000):
                fd.write(chunk)

            link.attrs['href'] = FILE + name[name.rfind('/'):]


def processHTML(filename):
    print(f'processing {filename}...')
    f = open(filename, 'r+')
    soup = bs(f.read(), features="html.parser")

    renameCSSAndJS(soup)
    renameNavigationLinks(soup)
    downloadAndRenamePDFPaths(soup)

    f.seek(0)
    f.write(str(soup))
    f.truncate()
    f.close()


downloadAllHTML()
processAllHTML()
print("DONE!")
