#!/usr/bin/python3

# Crawler
# 1.	Base d'URI (une entrée au moins)
# 2.	Extraction de liens dans la base
# 3.	vérifier l'existance du lien dans la base
# 3bis.	Ajouter le lien dans la base 
# 4.	Boucle.
#	base >=1000 pages(URI)

from http import client
from html import parser



def crawler(url_):
	print(url_)
	conn  = client.HTTPConnection(url_);
	conn.request("GET", "/")
	response = conn.getresponse()
	print(response)

url = "www.planet-libre.fr";
crawler(url);

