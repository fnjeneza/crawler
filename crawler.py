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
from math import log10, sqrt
from urllib import robotparser
from urllib.parse import urlparse
import treetaggerwrapper


class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);
        
        self.data=""
        self.MAX=5 #Max pages
        self.memory = {} #uri, vector and tf.idf
        self.urls=[] #urls list
        self.pages={}
        self.citations=[]

        self.is_script=False
        self.is_style=False
        self.factor=1 #for duplicating data
        self.ignore=False
        self.stopwords=[] #stop words list
        
        self.tag = {"title":12, "h1":10, "h2":8, "h3":6, "h4":4}

        #loading stop words
        with open("stopwords.txt") as stopwords:
            for word in stopwords:
                self.stopwords.append(word.strip())
    
    def iscrawlallowed(self,url):
        """
        check robots.txt
        """
        parser=urlparse(url)
        path = parser.scheme+"://"+parser.hostname+"/robots.txt"
        robot = robotparser.RobotFileParser()
        robot.set_url(path)
        robot.read()
        return robot.can_fetch('*', url)

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

    
    def pagerank(self):
        """
        compute pagerank
        """
        for url in self.pages:
            d = 0.85
            PR_N=0
            for u in self.pages[url]["urls"]:
                PR = self.pages[u]["pagerank"]
                N = self.pages[u]["urls"]
                PR_N=PR_N+PR/N
            self.pages[url]["pagerank"]=(1-d)+d*PR_N


    def tf(self, text):
        """
        calculate a tf of a text or vector
        returns a dict {word:tf}
        """
        if type(text)==str:
            vector = text.split() #convert str to list
        
            
        vector_tf={} # word:tf dict
        nk = len(vector) #length of the doccument
        
        for word in vector:
            if word not in vector_tf:
                vector_tf[word]=vector.count(word)/nk

        return vector_tf
        
    def idf(self, vector):
        """
        compute idf of text
        return a dict {word:idf}
        """

        vector_idf={}

        D = len(self.memory) #total number of documents in the corpus
        for word in vector:
            di=0 #number of documents where the word appears
            for uri in self.memory:
                if word in self.memory[uri]:
                    di+=1
            if di==0:
                di=1    
            idf = log10(D/di)
            vector_idf[word] = idf

        return vector_idf

    def tfidf(self, vector_tf, vector_idf):
        """
        compute tf.idf
        length of vector_tf and vector_idf must be the same
        return a dict {word:tf.idf}
        """
        if len(vector_tf)!=len(vector_idf):
            return 

        vector_tfidf={} #word:tf_idf dict

        for word in vector_tf:
            vector_tfidf[word] = vector_tf[word]*vector_idf[word]

        return vector_tfidf
    
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
                '-','=','_','|','[',']','"',"\\","/","&","@","#"];
        for symbol in symbols:
            text = text.replace(symbol,' ');
        return text;
    
    def remove_stopwords(self,text):
        """
        Remove stopwords from text
        """
        words = text.split();
        index = []
        
        purged = False
        i = 0
        while not purged:
            if i>=len(words):
                purged = True
                continue
            try:
                if words[i] in self.stopwords:
                    words.remove(words[i])
                else:
                    i=i+1
            except IndexError as e:
                error = ""

        return ' '.join(words)
    
    def handle_starttag(self, tag, attrs):
        #Recherche des liens
        if tag=="script":
            self.is_script=True

        elif tag=="style":
            self.is_style=True

        elif tag in self.tag:
            self.factor=self.tag[tag]

        elif tag == "footer":
            self.ignore=True

        elif(tag == "a"):
            for attr in attrs:
                if(attr[0] == "href"):
                    href = attr[1];
                    if href.find("http")>=0 and href.find("ubuntu.com")>=0:
                        if href not in self.urls:
                            self.urls.append(href)
                            self.citations.append(href)
  
    def handle_endtag(self, tag):
        if tag=="script":
            self.is_script=False

        elif tag=="style":
            self.is_style=False

        elif tag in self.tag:
            self.factor = 1

        elif tag == "footer":
            self.ignore=False

    def handle_data(self, data):
        if not self.is_script and not self.is_style and not self.ignore:
            for f in range(self.factor):
                self.data = self.data+' '+data.strip();


    def crawl(self):
        """
        crawl a site
        """
    
        #analyzer = htmlAnalyzer();
        self.urls.append("http://www.ubuntu.com/")
        
        i=0
        while len(self.memory)<=self.MAX:
            try:
                if not self.iscrawlallowed(self.urls[i]):
                    continue

                html = urlopen(self.urls[i]);
                print("...\t"+self.urls[i])
                self.data='' # clear data
                self.ignore=False 
                self.feed(html.read().decode());
                text = self.data.lower();
                text = self.remove_symbols(text);
                text = self.remove_stopwords(text);
                text = text.replace("'", ' ')
                text = self.lemmatise(text)
                vector_tf = self.tf(text) #compute word:tf 
                self.memory[self.urls[i]] = vector_tf

                self.pages[self.urls[i]]={"pagerank":1, 
                        "urls":list(self.citations)}
                self.citations.clear()
                
            except HTTPError as e:
                print(e);
            except URLError as ee:
                print(ee);
            except UnicodeDecodeError as eee:
                print(eee)
            except UnicodeEncodeError as uee:
                print(uee)
            #except:
            #    print("unknown error");
            i=i+1
        print(len(self.memory))

        #compute tf_idf
        for uri in self.memory:
            print("tf.idf\t"+uri)
            vector_idf = self.idf(self.memory[uri])
            tfidf = self.tfidf(self.memory[uri], vector_idf)
            self.memory[uri]=tfidf
        
        #compute pagerank
        for i in range(90):
            self.pagerank()

        f = open("db", "w")
        f.write(str(self.memory))
        f.close()
        
        f = open("pr", "w")
        f.write(str(self.pages))
        f.close()


    def handle_request(self, request):
        """
        Handle a user request
        : request: list
        : links: list 
        """
        #responses=[] # list  [salton cosinus, url]
        first_links=[] # links ordered by salton cosine
        second_links=[] # links ordered by pagerank

        #read file
        f = open("db", "r")
        self.memory=eval(f.read())
        f.close()

        request = request.lower()
        request= self.remove_symbols(request);
        request = self.remove_stopwords(request);
        request = request.replace("'", ' ')
        request = self.lemmatise(request)
        vector_tf = self.tf(request)
        vector_idf = self.idf(vector_tf)
        vector_req = self.tfidf(vector_tf, vector_idf)
        
        tfidf_req = []
        for v in vector_req:
            tfidf_req.append(vector_req[v])

        for url in self.memory:
            words = self.memory[url] #all words of a page
            tfidf=[] #tf.idf returned
            nb_terms = 0
            for term in vector_req:
                if term in words:
                    tfidf.append(words[term])
                    nb_terms+=1
                else:
                    tfidf.append(0)
            if nb_terms==len(vector_req):
                """
                use salton cosine
                """
                first_links.append([self.similarity(tfidf_req, tfidf), url])
            elif nb_terms!=0:
                """
                use pagerank
                """
                second_links.append([self.pages[url]["pagerank"], url])
        
        first_links.sort(reverse=True)
        second_links.sort(reverse=True)
        
        return first_links+second_links
