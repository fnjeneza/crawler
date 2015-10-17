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
from math import log10
import sqlite3


class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);
        
        print("Init...",end="\r");
        #count URIs
        self.counter = 0;
        self.data=""
        self.MAX=3 #Max pages

        #create database
        self.db = sqlite3.connect("crawler.db");
        self.cursor = self.db.cursor();

        #init table
        self.cursor.execute("DROP TABLE IF ExISTS crawl_tb");
        self.cursor.execute('''CREATE TABLE crawl_tb (id integer primary key autoincrement,
                                                    uri text unique,
                                                    vector text,
                                                    tfidf text)''');
        
        self.cursor.execute("DROP TABLE IF EXISTS stopword_tb");
        self.cursor.execute('''CREATE TABLE stopword_tb(id integer primary key autoincrement, 
                                                    stopword text unique)''');
        #init stopword table
        with open("stopwords.txt") as stopwords:
            for word in stopwords:
                word = word.strip()
                self.cursor.execute("INSERT INTO stopword_tb(stopword) VALUES(?)",[word]);
        
        print("Init... OK")
        
    def addUri(self, uri):
        """
        add Uri in the db
        """
        if not self.isUrlOK(uri):
            return
        try:
            self.cursor.execute("INSERT INTO crawl_tb(uri) VALUES(?)",[uri]);
            self.counter+=1;
            print("link\t"+str(self.counter)+"\t"+uri);
        except sqlite3.IntegrityError:
            error ="already added";

    def getUri(self, iterator):
        """
        return Uri where id=iterator
        """
        self.cursor.execute("SELECT uri FROM crawl_tb WHERE id=?",[iterator]);
        return self.cursor.fetchone()[0];
        
    
    def getTotal(self):
        """
        Total links in db
        """
        self.cursor.execute("SELECT COUNT(uri) FROM crawl_tb");
        return self.cursor.fetchone()[0];

    def isStopword(self, word):
        """
        Check if "word" is a stopword
        """
        self.cursor.execute("SELECT stopword FROM stopword_tb WHERE stopword=?",[word])
        
        if self.cursor.fetchone()==None:
            return False;
        return True;

    def vector(self, text, pk_id):
        """
        save vector in db.
        The vector must be without punctuations and each word separate 
        by space
        The vector is a simple text, which will be split before use
        pk_id is the primary key id
        """
        self.cursor.execute("UPDATE crawl_tb SET vector=? WHERE id=?",[text, pk_id]);

        
    def tf(self, data):
        """ 
       calcul de la fréquence des mots 
        """
        
	#liste de mots
        words_list = data.split();
        
        length = len(words_list);

	#occurence des mots
        words_occurence = {}
        
        for word in words_list:
            if not words_occurence.__contains__(word):
                 #check if word is already in the list
                 words_occurence[word]=words_list.count(word)/length;

        return words_occurence;
    
    def remove_symbols(self, text):
        """
        Remove symbols in text
        """
        symbols = ['.',',',';',':','!','?','~','(',')','{','}',
                '-','=','_','|','[',']','"',"'"];
        for symbol in symbols:
            text = text.replace(symbol,' ');
        return text;
    
    def remove_stopwords(self,text):
        """
        Remove stopwords from text
        an empty list is given by default
        """
        words = text.split();
        for word in words:
            if self.isStopword(word):
               words.remove(word); 
        return ' '.join(words);
    
    def isUrlOK(self, url):
        """Check if url is alive"""
        try:
            response = urlopen(url)
        except URLError as e:
            return False;
        code = response.getcode()
        codes = {200,301,302}
        if code not in codes:
            return False;
        return True;

    def idf(self, word):
        """ Calcul de l'idf"""
        D = self.getTotal()  # total pages
        self.cursor.execute("SELECT COUNT(id) FROM crawl_tb WHERE vector LIKE '%?%'", [word])
        di = self.cursor.fetchone();
        idfi = log10(D/di)  # idf
        return idfi;

    def handle_starttag(self, tag, attrs):
        #Recherche des liens
        if self.counter<self.MAX:
            if(tag == "a"):
                for attr in attrs:
                    if(attr[0] == "href"):
                        href = attr[1];
                        if(href.find("http")>=0):
                            self.addUri(href);

    def handle_data(self, data):
        self.data = self.data+' '+data.strip();

#text="ceci est un text, un text actually";
url = "http://news.softpedia.com/cat/Linux/";
analyzer = htmlAnalyzer();
analyzer.addUri(url);

## Test
"""
print(text)
text = analyzer.remove_punctuations(text)
print(analyzer.remove_stopwords(text))
exit();
#text = analyzer.remove_punctuations(text);
#print(analyzer.tf(text))

html = urlopen(url);
analyzer.feed(html.read().decode());
text = analyzer.data.lower();
#print(text)
#exit()
#text = ' '.join(text);
text = analyzer.remove_punctuations(text);
text = analyzer.remove_stopwords(text);
#tf = text.split();
#r = analyzer.idf("launches")
#print(r)
## End of test
"""

iterator=1;
while (iterator<analyzer.MAX):
    url = analyzer.getUri(iterator);

    #Retrieve an html page
    print("Crawling:\t"+str(iterator)+"\t"+url)
    try:
        html = urlopen(url);
        analyzer.data='' # reinit data
        analyzer.feed(html.read().decode());
        text = analyzer.data.lower();
        text = analyzer.remove_symbols(text);
        text = analyzer.remove_stopwords(text);
        print(text)
        text = ' '.join(text.split())
        analyzer.vector(text, iterator)
        
        #analyzer.addUri(url);
    except HTTPError as e:
        print(e);
    except URLError as ee:
        print(ee);
    #except:
    #    print("unknown error");

    iterator+=1;

#commit changes to the db
analyzer.db.commit();
analyzer.cursor.close();
analyzer.db.close();

#print(analyzer.counter);
