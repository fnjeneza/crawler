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
import treetaggerwrapper


class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);
        
        #print("Init...",end="\r");
        #count URIs
        self.counter = 0;
        self.data=""
        self.MAX=1000 #Max pages

        #create database
        self.db = sqlite3.connect("crawler.db");
        self.cursor = self.db.cursor();
    
    def reset_db(self):
        """
        reset db
        """
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
        
        #print("Init... OK")
        
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
    
    def lemmatise(self, text):
        tagger = treetaggerwrapper.TreeTagger(TAGLANG='fr')
        tags = tagger.tag_text(text)
        mytags = treetaggerwrapper.make_tags(tags)
        lemma_list=[]
        for tag in mytags:
            lemma_list.append(tag.lemma)
        return lemma_list

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
        text_unique = []
        #remove duplicated word
        for word in text.split():
            if not word in text_unique:
                text_unique.append(word)
        
        text = ' '.join(text_unique)
        self.cursor.execute("UPDATE crawl_tb SET vector=? WHERE id=?",[text, pk_id]);

        
    def tfidf(self, pk):
        """ 
       tf_idf
       primary key(id)
        """
        self.cursor.execute("SELECT vector FROM crawl_tb WHERE id=?",[pk]);
        data = self.cursor.fetchone()[0]

	#liste de mots
        words_list = data.split();
        
        length = len(words_list);

	#word's tfidf
        vector_tfidf = []
        for word in words_list:
            #check if word is already in the list
            tf = words_list.count(word)/length;
            self.cursor.execute("SELECT COUNT(vector) FROM crawl_tb "
                                 "WHERE vector LIKE '%"+word+"%'")
            occurence = self.cursor.fetchone()[0];
            idf = log10(self.MAX/occurence)
            tf_idf = tf*idf
            vector_tfidf.append(str(tf_idf))
        
        vector_text = ' '.join(vector_tfidf)
        self.cursor.execute("UPDATE crawl_tb SET tfidf=? WHERE id=?",[vector_text, pk]);
    
    def remove_symbols(self, text):
        """
        Remove symbols in text
        """
        symbols = ['.',',',';',':','!','?','~','(',')','{','}',
                '-','=','_','|','[',']','"',"'","\\","/","&"];
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
reset_db = False

url = "http://news.softpedia.com/cat/Linux/";
analyzer = htmlAnalyzer();

if reset_db:
    analyzer.reset_db()

analyzer.addUri(url);


iterator=1;
while (iterator<=analyzer.MAX):
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
        text = ' '.join(analyzer.lemmatise(text))
        analyzer.vector(text, iterator)

        #commit changes to the db
        analyzer.db.commit()
    except HTTPError as e:
        print(e);
    except URLError as ee:
        print(ee);
    #except:
    #    print("unknown error");

    iterator+=1;

#tf_idf
for index in range(1,analyzer.MAX):
    analyzer.tfidf(index)
    analyzer.db.commit()


#close all opened db or cursor
analyzer.cursor.close();
analyzer.db.close();

