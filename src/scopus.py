from asr.config.settings import *
from urllib import urlencode, quote
import asr.config.secrets
import csv 
import requests 
import json 
import argparse
import sys
import os
import time

API_KEY =asr.config.secrets.scopus_api_key

'''
full article retrieval in xml
url  ='https://api.elsevier.com/content/article/doi/10.1016/j.obhdp.2014.09.011'
headers={'Accept': 'text/xml', 'X-ELS-APIKey': '748740b10dfa173d12fef34e4172b48c'}
query={'httpAccept': 'text/xml', 'view': 'FULL'}
'''

def wait(reset):
	#make a way to control the number of requests per sec 
	time.sleep(reset)
	
def fetch_abstract(doi):
	#passing the api_key as query params
	headers={'Accept': 'application/json'}
	url ='https://api.elsevier.com/content/abstract/doi/' +doi
	#this returns 1553 now
	#query ={'httpAccept': 'application/json', 'apiKey':API_KEY , 'view': 'STANDARD','query': 'CODEN(OBDPF)', 'start': start, 'count':count}
	#using issn instead
	query ={'httpAccept': 'application/json', 'apiKey':API_KEY , 'view': 'FULL'}
	#start is the offset number for the results not the page no
	#if using the standard view 200 results can be fetched in one go
	r = requests.get(url, headers=headers, params=urlencode(query))
	js =r.json()
	return js	

def parse_name(ifile):
	#parse the page range and volume no from the file name
	split =unicode(f, 'utf-8').strip(' \t').split('-')
	vol =split[0]
	pages =split[2]+'-'+split[3]
	return vol, pages

def search_json(vol, pages, js):
	#js[0]['search-results']['entry']
	
	for j in js:
		for entry in j['search-results']['entry']:
			if entry['prism:pageRange'] ==pages and entry['prism:volume'] ==vol:
				try:
					cite_count =entry['citedby-count']
				except KeyError:
					cite_count =''
				try:
					creator =entry['dc:creator']
				except KeyError:
					creator =''
				try:
					scopus_id =entry['dc:identifier']
				except KeyError:
					scopus_id =''
				try:
					title =entry['dc:title']
				except KeyError:
					title =''
				try:
					eid =entry['eid']
				except KeyError:
					eid =''
				try:
					doi =entry['prism:doi']
				except KeyError:
					doi =unicode('')
				return doi, scopus_id, creator, title, cite_count, eid
	print vol, pages
	return 	

def info(start, count, issn):
	issn ='(' + issn+ ')'
	#passing the api_key as query params
	headers={'Accept': 'application/json'}
	url ='https://api.elsevier.com/content/search/scopus?'
	#this returns 1553 now
	#query ={'httpAccept': 'application/json', 'apiKey':API_KEY , 'view': 'STANDARD','query': 'CODEN(OBDPF)', 'start': start, 'count':count}
	#using issn instead
	query ={'httpAccept': 'application/json', 'apiKey':API_KEY , 'view': 'STANDARD','query': issn, 'start': start, 'count':count}
	#start is the offset number for the results not the page no
	#if using the standard view 200 results can be fetched in one go
	r = requests.get(url, headers=headers, params=urlencode(query))
	js =r.json()
	return js

def citation_info(eid, start, count):
	#passing the api_key as query params
	headers={'Accept': 'application/json'}
	url ='https://api.elsevier.com/content/search/scopus?'
	refeid ='refeid(' +eid+')'
	query ={'httpAccept': 'application/json', 'apiKey':API_KEY , 'query': refeid, 'start': start, 'count':count, 'view': 'STANDARD'}
	r = requests.get(url, headers=headers, params=urlencode(query))
	js =r.json()
	return js
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--txt_folder')
	parser.add_argument('--json_file')
	parser.add_argument('--report_file')
	parser.add_argument('--use_api', action='store_true')
	parser.add_argument('--make_excel_names', action='store_true')
	parser.add_argument('--get_citation_meta_data', action='store_true')
	parser.add_argument('--excel_file')
	parser.add_argument('--report_folder')
	parser.add_argument('--citation_meta_create_excel', action='store_true')
	parser.add_argument('--json_folder')
	parser.add_argument('--issn')
	parser.add_argument('--expected_no_articles')#give a slightly higher rounded no like 2000
	parser.add_argument('--get_abstracts', action ='store_true')
	args = parser.parse_args()

	if args.use_api:
		#use api, json_file
		issn =args.issn
		no_articles =int(args.expected_no_articles)
		data =[]
		#07495978 issn for obhdp, expected no of articles 2000
		# 10464964 issn for sgr
		for i in range(0, no_articles, 200):#200 is the max for full search view
			js =info(i, 200, issn)
			data.append(js)

		with open(args.json_file, 'w') as f:
			json.dump(data, f)

	if args.make_excel_names:
		#make_excel_names , json_file, txt_folder, report_file
		data =[]
		with open(args.json_file, 'r') as f:
			js =json.load(f)
		for f in os.listdir(args.txt_folder):
			vol, pages =parse_name(f)
			if search_json(vol, pages, js):
				doi, scopus_id, creator, title, cite_count, eid =search_json(vol, pages, js)
				data.append([unicode(f, 'utf-8'),doi, scopus_id, eid, creator, title, cite_count ])
		header =['filename', 'doi', 'scopus_id','eid', 'creator', 'title', 'cite_count']
		with open(args.report_file, 'w') as f:
			writer =csv.writer(f)
			writer.writerow(header)
			for i in data:
				writer.writerow([j.encode('utf-8') for j in i])

	if args.get_citation_meta_data:
		#get_citation_meta_data, excel_file, report folder
		eids_cites =[]
		with open(args.excel_file, 'r') as f:
			reader =csv.DictReader(f)
			for row in reader:
				eid =row['eid']
				cites =row['cite_count']
				eids_cites.append([eid, cites])
		#count =0
		done =[]
		for f in os.listdir(args.report_folder):
			done.append(f)
		for row in eids_cites:
			#count +=1
			eid =row[0]
			cites =row[1]
			if 'eid_'+ eid +'.json' in done:
				pass
			else:
				js =[]
				for i in range(0, int(cites), 200):
					js.append(citation_info(eid, i, 200))#final identification using the refeid, so that there is one excel
					wait(1)
				with open(args.report_folder+'eid_'+eid+'.json', 'w') as f:
					json.dump(js, f)
				wait(3)
	if args.citation_meta_create_excel:
		#citation_meta_create_excel, report_file, json_folder
		out =[]
		max_affiliations =0
		#iterate over all to find the max no of affiliations
		for t in os.listdir(args.json_folder):
			with open(args.json_folder +t) as f:
				js =json.load(f)
			for j in js:
				try:
					for entry in j[u'search-results'][u'entry']:
						try:
							if len(entry[u'affiliation']) > max_affiliations:
								max_affiliations =len(entry[u'affiliation'])
						except KeyError:
							pass
				except KeyError:
					pass
		header =['doc_name', 'doi', 'source_id', 'eid', 'scopus_id', 'title', 'author', 'citations', 'issn', 'publication', 'cover_date', 'display_date', 
					'subtype_desc', 'subtype', 'aggregation_type','open_access', 'open_access_flag'	]
		#accordingly add the number of affiliations in the header		
		for i in range(max_affiliations):
			header.append('affiliation_city' +str(i+1)	)
			header.append('affiliation_country'+str(i+1))
			header.append('affiliation_name'+str(i+1))

		for t in os.listdir(args.json_folder):
			#print t
			with open(args.json_folder +t) as f:
				js =json.load(f)
			for j in js:
				try:
					doc_name =j[u'search-results'][u'opensearch:Query'][u'@searchTerms'].strip('refeid()')
					for entry in j[u'search-results'][u'entry']:
						tmp =[]
						try:
							doi =entry[u'prism:doi']
						except KeyError:
							doi =u''
						try:	
							source_id =entry[u'source-id']
						except KeyError:
							source_id =u''
						try:
							eid =entry[u'eid']
						except KeyError:
							eid =u''
						try:
							scopus_id =entry[u'dc:identifier']
						except KeyError:
							scopus_id =u''
						try:
							title =entry[u'dc:title']
						except KeyError:
							title =u''
						try:
							author =entry[u'dc:creator']#at most one author is listed
						except KeyError:
							author =u''
						affiliation_city =[]
						affiliation_country =[]
						affiliation_name =[]
						for i in range(max_affiliations):
							try: 
								if entry['affiliation'][i][u'affiliation-city']:
									affiliation_city.append(entry['affiliation'][i][u'affiliation-city'])
								else:
									affiliation_city.append(None)
	
								if entry['affiliation'][i][u'affiliation-country']:
									affiliation_country.append(entry['affiliation'][i][u'affiliation-country'])
								else:
									affiliation_country.append(None)
	
								if entry['affiliation'][i][u'affilname']:
									affiliation_name.append(entry['affiliation'][i][u'affilname'])
								else:
									affiliation_name.append(None)
	
							except (IndexError, KeyError) as e:
								affiliation_city.append(None)
								affiliation_country.append(None)
								affiliation_name.append(None)
						try:	
							citations =entry[u'citedby-count']
						except KeyError:
							citations =u''
						try:
							issn =entry[u'prism:issn']
						except KeyError:
							issn =u''
						try:
							publication =entry[u'prism:publicationName']
						except KeyError:
							publication =u''
						try:
							cover_date =entry[u'prism:coverDate']
						except KeyError:
							cover_date =u''
						try:
							display_date =entry[u'prism:coverDisplayDate']
						except KeyError:
							display_date =u''
						try:
							subtype_desc =entry[u'subtypeDescription']
						except KeyError:
							subtype_desc =u''
						try:
							subtype =entry[u'subtype']
						except KeyError:
							subtype =u''
						try:
							aggregation_type =entry[u'prism:aggregationType']
						except KeyError:
							aggregation_type =u''
						try:
							open_access =entry[u'openaccess']
						except KeyError:
							open_access =u''
						try:
							open_access_flag =entry[u'openaccessFlag']
						except KeyError:
							open_access_flag =u''
						tmp.extend([doc_name, doi, source_id, eid, scopus_id, title, author, citations, issn, publication, cover_date, display_date, subtype_desc, subtype, aggregation_type,open_access, open_access_flag])
						for i, j, k in zip(affiliation_city, affiliation_country, affiliation_name):
							tmp.extend([i, j, k])
						out.append(tmp)
				except KeyError:
					pass		
		with open(args.report_file, 'w') as f:
			writer =csv.writer(f)
			writer.writerow(header)
			for row in out:
				tmp =[]
				for r in row:
					try:
						tmp.append(r.encode('utf-8'))
					except AttributeError:
						tmp.append(r)
				writer.writerow(tmp)
	if args.get_abstracts:
		done =[i.replace('.json', '') for i in os.listdir(args.report_folder+'abstracts+meta_json/')]
		
		with open(args.excel_file, 'r') as f:
			reader =csv.reader(f)
			count =0
			for row in reader:
				if count ==0:
					header =row
					count +=1
					doi_idx =header.index('doi')
					scopus_idx =header.index('scopus_id')
				else:
					doi =row[doi_idx]
					scopus_id =row[scopus_idx]
					if scopus_id not in done:
						js =fetch_abstract(doi)
						#using scopus to name the files since doi contains '/'
						with open(args.report_folder+'abstracts+meta_json/' +scopus_id+ '.json', 'w') as f:
							json.dump(js, f)
						try:
							abstract =js["abstracts-retrieval-response"]['item']['bibrecord']['head']['abstracts']
						except KeyError:
							abstract =''
							print "no abstract for scopus_id  "+ scopus_id
						if abstract: 
							with open(args.report_folder +'abstracts/'+ scopus_id+'.txt', 'w') as f:
								f.write(abstract.encode('utf-8'))
						else:
							print "no abstract for scopus_id, doi  "+ scopus_id, doi
					wait(2)
