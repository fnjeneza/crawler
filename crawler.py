#!/usr/bin/python3

# Crawler
# 1.	Base d'URI (une entrée au moins)
# 2.	Extraction de liens dans la base
# 3.	vérifier l'existance du lien dans la base
# 3bis.	Ajouter le lien dans la base 
# 4.	Boucle.
#	base >=1000 pages(URI)

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
import sqlite3

class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);

        print("Init...");
        #count URIs
        self.counter = 0;

        #create database
        self.db = sqlite3.connect("crawler.db");
        self.cursor = self.db.cursor();

        #init table
        self.cursor.execute("DROP TABLE IF ExISTS crawl_tb");
        self.cursor.execute('''CREATE TABLE crawl_tb (id integer primary key autoincrement,
                                                    uri text unique)''');

    def addUri(self, uri):
        try:
            self.cursor.execute("INSERT INTO crawl_tb(uri) VALUES(?)",[uri]);
            self.counter+=1;
        except sqlite3.IntegrityError:
            error ="already added";

    def getUri(self, iterator):
        self.cursor.execute("SELECT uri FROM crawl_tb WHERE id=?",[iterator]);
        return self.cursor.fetchone()[0];
        

    def getTotal(self):
        self.cursor.execute("SELECT COUNT DISTINCT uri FROM crawl_tb");
        return self.cursor.fetchone()[0];

    def handle_starttag(self, tag, attrs):
        #Recherche des liens
        
        if(tag == "a"):
            for attr in attrs:
                if(attr[0] == "href"):
                    href = attr[1];
                    if(href.find("http")>=0):
                        #print(self.counter);
                        #print(href);
                        self.addUri(href);



url = "http://www.planet-libre.org";
analyzer = htmlAnalyzer();
analyzer.addUri(url);

iterator=1;
while (analyzer.counter<1000):
    url = analyzer.getUri(iterator);

    #Retrieve an html page
    print(url);
    try:
        html = urlopen(url);
        analyzer.feed(str(html.read()));
    except HTTPError as e:
        print(e);
    except URLError as ee:
        print(ee);
    except:
        print("unknown error");

    iterator+=1;


print(analyzer.counter);
