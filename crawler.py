#!/usr/bin/python3

# Crawler
# 1.	Base d'URI (une entrée au moins)
# 2.	Extraction de liens dans la base
# 3.	vérifier l'existance du lien dans la base
# 3bis.	Ajouter le lien dans la base 
# 4.	Boucle.
#	base >=1000 pages(URI)

from urllib.request import urlopen
from html.parser import HTMLParser

class htmlAnalyzer(HTMLParser):
    def handle_starttag(self, tag, attrs):
        """ Recherche des liens """
        
        if(tag == "a"):
            for attr in attrs:
                if(attr[0] == "href"):
                    href = attr[1];
                    if(href.find("http")>=0):
                        print(href);



url = "http://www.planet-libre.org";

""" Retrieve an html page"""
html = urlopen(url);

analyzer = htmlAnalyzer();
analyzer.feed(str(html.read()));


