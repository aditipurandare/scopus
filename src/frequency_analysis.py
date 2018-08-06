from asr.config.settings import *
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from nltk.stem.porter import PorterStemmer
from collections import Counter
from nltk import ngrams
from math import log
import json
import argparse
import csv


""" now this can be modified so that freq and tf.idf can be done
together, n gram is currently added as a separate experiment
class FrequencyAnalysis:
	def __init__(self, json_file, output_file):
		self.json_file= json_file
		self.output_file= output_file
""" 
def stem(tokens):
	stemmer =PorterStemmer()
	stemmed_terms =[stemmer.stem(token) for token in tokens]
	return stemmed_terms

def stop_remove(tokens):
	""" takes in tokenized text, remove stop words and return """
	stop_words =set(stopwords.words('english'))
	#add punctuation to the stop words
	stop_words.update(['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}','*', '&', '^'])
	terms =[word for word in tokens if word not in stop_words]
	return terms
	
def tokenize(doc):
	#now all the characters like . , " " should be removed, no need for update in stop
	#tokens =[word.lower() for word in wordpunct_tokenize(doc) ]
	tokens =[word.lower() for word in wordpunct_tokenize(doc) if word.isalpha() and len(word) >3]
	return tokens



def weak_tokenize(doc):
	#now all the characters like . , " " should be removed, no need for update in stop
	#tokens =[word.lower() for word in wordpunct_tokenize(doc) ]
	tokens =[word.lower() for word in wordpunct_tokenize(doc)]
	return tokens
def idf(word_counts, tokens, no_of_docs):
	#tokens here is a list of lists, meaning each individual list has tokens for a document
	word_tf_idf =[]
	for word, count in word_counts:
		df =0
		idf =0
		tf =[]
		tf_idf=[]
		for one in tokens:
			if one.count(word) >0:
				df +=1
			#normalized tf for this word for all docs
			tf.append(one.count(word)/len(one))
		#idf for one word on log scale
		idf =round(log(no_of_docs/df), 4)
		tf_idf =[round(i*idf,4) for i in tf]
		tmp=[word]
		
		for i in tf_idf:
			tmp.append(i)
		tmp.append(idf)
		word_tf_idf.append(tuple(tmp))
		#one row represents normalized tf.idf for all docs and the idf for one word
		#"alpha",tf_d1, tf_d2, ....., tf_dn, idf 
		#word_tf_idf.append((word, tf_idf, idf))
		
	return word_tf_idf
	
def tf(tokens):
	word_count =Counter(tokens)
	return word_count.most_common()

def n_grams_freq(tokens, n):
	grams =[]
	for gram in ngrams(tokens, n):
		grams.append(gram)
	return Counter(grams)

