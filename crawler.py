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
from math import log10, sqrt, pow
import sqlite3
import treetaggerwrapper


class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);
        
        #print("Init...",end="\r");
        #count URIs
        self.counter = 0;
        self.data=""
        self.MAX=5 #Max pages

        #create database
        self.db = sqlite3.connect("crawler.db");
        self.cursor = self.db.cursor();
        self.is_script=False
        self.is_style=False
        self.stopwords=[] #stop words list
        
        #loading stop words
        with open("stopwords.txt") as stopwords:
            for word in stopwords:
                self.stopwords.append(word.strip())

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
        
    
    def addUri(self, uri):
        """
        add Uri in the db
        """
        if not self.isUrlOK(uri):
            return
        try:
            self.cursor.execute("INSERT INTO crawl_tb(uri) VALUES(?)",[uri]);
            self.counter+=1;
            #print("link\t"+str(self.counter)+"\t"+uri);
        except sqlite3.IntegrityError:
            error ="already added";
    
    def lemmatise(self, text):
        """
        lemmatise a text
        """
        tagger = treetaggerwrapper.TreeTagger(TAGLANG='en')
        tags = tagger.tag_text(text)
        mytags = treetaggerwrapper.make_tags(tags)
        lemma_list=[]
        for tag in mytags:
            lemma_list.append(tag.lemma)
        return ' '.join(lemma_list)

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

    def tf(self, text):
        """
        calculate a tf of a text or vector
        """
        if type(text)==str:
            text = text.split() #convert str to list
        
        tf=[] # tf list
        words_len = len(text)
        words = self.remove_duplicated(text)
        for word in words:
            tf.append(text.count(word)/words_len)

        return (words, tf)
        
    def tfidf(self, pk):
        """ 
       tf_idf
       primary key(id)
        """
        self.cursor.execute("SELECT vector, uri FROM crawl_tb WHERE id=?",[pk]);
        results = self.cursor.fetchone()
        data = results[0]
        print("Calcul du tf_idf: "+str(pk)+"\t"+results[1])
        
        words_tfs = self.tf(data) # words and tfs
        
        words = words_tfs[0] # only words non-duplicated
        tfs = words_tfs[1] # only tfs

        data = data.split()
        length = len(data);

	#word's tfidf
        vector_tfidf = []
        for word in words:
            index = words.index(word)
            tf= tfs[index]
            self.cursor.execute("SELECT COUNT(vector) FROM crawl_tb "
                                 "WHERE vector LIKE '%"+word+"%'")
            occurence = self.cursor.fetchone()[0];
            idf = log10(self.MAX/occurence)
            tf_idf = tf*idf
            vector_tfidf.append(str(tf_idf))
            
        
        vector_tfidf = ' '.join(vector_tfidf)
        words = ' '.join(words)
        self.cursor.execute("UPDATE crawl_tb SET vector=?, tfidf=? WHERE id=?",[words, vector_tfidf, pk]);
    
    def handle_request(self, request, tfidf_request):
        """
        Handle a user request
        : request: list
        : links: list 
        """
        incr=0
        cond=""
        responses=[] # list  [salton cosinus, url]
        links=[] # list of urls to return 
        for value in request:
            if incr==0:
                cond = "'%"+value+"%'"
            else:
                cond =cond+" OR vector LIKE '%"+value+"%'"
            incr+=1

        self.cursor.execute("SELECT uri,vector, tfidf FROM crawl_tb WHERE vector LIKE "+cond)
        results = self.cursor.fetchall()
        tfidf_vector=[] #tfidf of the returned vector
        for result in results:
            url = result[0]
            vector = result[1].split();
            tfidf = result[2].split();
            for word in request:
                try:
                    index = vector.index(word)
                    tfidf_vector.append(float(tfidf[index]))
                except ValueError:
                    tfidf_vector.append(0)
            #calculate similarity
            similarity = self.similarity(tfidf_request, tfidf_vector)
            responses.append([similarity,url]) # append an url
            tfidf_vector.clear()
        
        responses.sort(reverse=True) #sort result by salton cosine
        
        for response in responses:
            links.append(response[1]) # links to return

        return links

    def similarity(self, vector1, vector2):
        """
        cosinus de salton
        """
        pos = 0;
        num = 0;
        norm_a = 0;
        norm_b = 0;
        vector_size = len(vector1)
        while pos < vector_size:
            num = num+(vector1[pos]*vector2[pos]) 
            norm_a = norm_a+pow(vector1[pos],2)
            norm_b = norm_b+pow(vector2[pos],2)
            pos+=1
        
        norm_a = sqrt(norm_a)
        norm_b = sqrt(norm_b)

        return num/(norm_a*norm_b)

    def remove_symbols(self, text):
        """
        Remove symbols in text
        """
        symbols = ['.',',',';',':','!','?','~','(',')','{','}',
                '-','=','_','|','[',']','"',"'","\\","/","&"];
        for symbol in symbols:
            text = text.replace(symbol,' ');
        return text;
    
    def remove_duplicated(self, text):
        """
        remove all duplicated word
        return list
        """
        optimised=[]
        if type(text)==str:
            text = text.split()

        for word in text:
            if word not in optimised:
                optimised.append(word)

        return optimised

    def remove_stopwords(self,text):
        """
        Remove stopwords from text
        """
        words = text.split();
        index = []
        
        for word in words:
            if word in self.stopwords:
                index.append(words.index(word))

        index.reverse()
        for i in index:
            words.pop(i)

        return ' '.join(words)

    
    def isUrlOK(self, url):
        """Check if url is alive"""
        try:
            response = urlopen(url)
            if response.geturl().find("softpedia.com") <0 :
                    return False
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
            if tag=="script":
                self.is_script=True

            if tag=="style":
                self.is_style=True

            if(tag == "a"):
                for attr in attrs:
                    if(attr[0] == "href"):
                        href = attr[1];
                        if(href.find("http")>=0):
                            self.addUri(href);
  
    def handle_endtag(self, tag):
        if tag=="script":
            self.is_script=False

        if tag=="style":
            self.is_style=False

    def handle_data(self, data):
        if not self.is_script and not self.is_style:
            self.data = self.data+' '+data.strip();


    def crawl(self, url):
        """
        crawl a site
        """
    
        url = "http://news.softpedia.com/cat/Linux/";
        #analyzer = htmlAnalyzer();

    
        self.reset_db()

        self.addUri(url);

        iterator=1;
        while (iterator<=self.MAX):
            url = self.getUri(iterator);

            #Retrieve an html page
            print("Crawl:\t"+str(iterator)+"\t"+url)
            try:
                html = urlopen(url);
                self.data='' # reinit data
                self.feed(html.read().decode());
                text = self.data.lower();
                text = self.remove_symbols(text);
                text = self.remove_stopwords(text);
                text = ' '.join(self.lemmatise(text))
                self.vector(text, iterator) #save vector in db

                #commit changes to the db
                self.db.commit()
            except HTTPError as e:
                print(e);
            except URLError as ee:
                print(ee);
            #except:
            #    print("unknown error");

            iterator+=1;

        #tf_idf
        for index in range(1,self.MAX+1):
            self.tfidf(index)
            self.db.commit()


        #close all opened db or cursor
        self.cursor.close();

############################################################
"""
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
    print("Crawl:\t"+str(iterator)+"\t"+url)
    try:
        html = urlopen(url);
        analyzer.data='' # reinit data
        analyzer.feed(html.read().decode());
        text = analyzer.data.lower();
        text = analyzer.remove_symbols(text);
        text = analyzer.remove_stopwords(text);
        text = ' '.join(analyzer.lemmatise(text))
        analyzer.vector(text, iterator) #save vector in db

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
for index in range(1,analyzer.MAX+1):
    analyzer.tfidf(index)
    analyzer.db.commit()


#close all opened db or cursor
analyzer.cursor.close();
analyzer.db.close();
"""
######################################################
