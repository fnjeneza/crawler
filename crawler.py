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
import treetaggerwrapper


class htmlAnalyzer(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self);
        
        self.data=""
        self.MAX=100 #Max pages
        self.memory = {} #uri, vector and tf.idf
        self.urls=[] #urls list

        self.is_script=False
        self.is_style=False
        self.stopwords=[] #stop words list
        
        #loading stop words
        with open("stopwords.txt") as stopwords:
            for word in stopwords:
                self.stopwords.append(word.strip())

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
    """
    def handle_request(self, request):
        """
        Handle a user request
        : request: list
        : links: list 
        """
        incr=0
        cond=""
        responses=[] # list  [salton cosinus, url]
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
                todo = "todo"
        
        first_links.sort(reverse=True)
        
        return first_links
    """
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

        if tag=="style":
            self.is_style=True

        if(tag == "a"):
            for attr in attrs:
                if(attr[0] == "href"):
                    href = attr[1];
                    if href.find("http")>=0 and href.find("ubuntu.com")>=0:
                        if href not in self.urls:
                            self.urls.append(href)
  
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
    
        #analyzer = htmlAnalyzer();
        self.urls.append(url)
    
        #for url in self.urls:
        i=0
        while len(self.memory)<=self.MAX:
            try:
                html = urlopen(self.urls[i]);
                print(str(i)+"\t"+self.urls[i])
                self.data='' # clear data
                self.feed(html.read().decode());
                text = self.data.lower();
                text = self.remove_symbols(text);
                text = self.remove_stopwords(text);
                text = text.replace("'", ' ')
                text = self.lemmatise(text)
                vector_tf = self.tf(text) #compute word:tf 
                self.memory[self.urls[i]] = vector_tf
                
            except HTTPError as e:
                print(e);
            except URLError as ee:
                print(ee);
            except UnicodeDecodeError as eee:
                print(eee)
                #self.urls.remove(self.urls[i])
            except UnicodeEncodeError as uee:
                print(uee)
                #self.urls.remove(self.urls[i])
            except IndexError as ie:
                i = 10*self.MAX
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
        
        f = open("db", "w")
        f.write(str(self.memory))
        f.close()

    def handle_request(self, request):
        """
        Handle a user request
        : request: list
        : links: list 
        """
        responses=[] # list  [salton cosinus, url]
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
                todo = "todo"
        
        first_links.sort(reverse=True)
        
        return first_links
