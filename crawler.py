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

        print("Init...",end="");
        #count URIs
        self.counter = 0;

        #create database
        self.db = sqlite3.connect("crawler.db");
        self.cursor = self.db.cursor();

        #init table
        self.cursor.execute("DROP TABLE IF ExISTS crawl_tb");
        self.cursor.execute('''CREATE TABLE crawl_tb (id integer primary key autoincrement,
                                                    uri text unique,
                                                    stopword text unique)''');
        #init stopwords
        with open("stopwords.txt") as stopwords:
            for word in stopwords:
                word = word.strip()
                self.cursor.execute("INSERT INTO crawl_tb(stopword) VALUES(?)",[word]);
        
        print("Init... OK")
        
    def addUri(self, uri):
        """
        add Uri in the db
        """
        try:
            self.cursor.execute("INSERT INTO crawl_tb(uri) VALUES(?)",[uri]);
            self.counter+=1;
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
        self.cursor.execute("SELECT COUNT DISTINCT uri FROM crawl_tb");
        return self.cursor.fetchone()[0];

    def isStopword(self, word):
        """
        Check if "word" is a stopword
        """
        self.cursor.execute("SELECT stopword FROM crawl_tb WHERE stopword=?",[word])
        
        if self.cursor.fetchone()==None:
            return False;
        return True;

    def tf(self, data):
        """ 
        calcul de la fréquence des mots 
        """
        
	#liste de mots
        words_list = data.split(' ');
        
        length = len(words_list);

	#occurence des mots
        words_occurence = {}
        
        for word in words_list:
            if not words_occurence.__contains__(word):
                 #check if word is already in the list
                 words_occurence[word]=words_list.count(word)/length;

        return words_occurence;
    
    def remove_punctuations(self, text):
        """
        Remove punctuations in text
        """
        punctuations = ['.',',',';',':','!','?','~'];
        for punctuation in punctuations:
            text = text.replace(punctuation, '');
        return text;
    
    def remove_stopwords(self,text):
        """
        Remove stopwords from text
        an empty list is given by default
        """
        words = text.split(' ');
        for word in words:
            if self.isStopword(word):
               words.remove(word); 
        return ' '.join(words);

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

text="ceci est un text, un text actually";
url = "http://www.planet-libre.org";
analyzer = htmlAnalyzer();
analyzer.addUri(url);

## Test
#print(analyzer.remove_punctuations(text));
#stopwords=[]
print(text)
print(analyzer.remove_stopwords(text))
exit();
text = analyzer.remove_punctuations(text);
text = analyzer.stopwords(text)
print(analyzer.tf(text))
exit()
## End of test

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

#commit changes to the db
analyzer.db.commit();
analyzer.cursor.close();
analyzer.db.close();
#print(analyzer.counter);
