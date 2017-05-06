#!/usr/bin/env python

import requests #if not found. type pip install requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit

global finalLinkTX

def get_hopcount():
	#route = []
	global cost
	global finalLinkTX
	cost = 0
	finalLinkTX = {}
	prevswitch = ""
	switch = ""
	switchtmp = ""
	route = ""
	#src = "00:00:00:00:00:00:00:02"
	#dst = "00:00:00:00:00:00:00:01"
	src = ""
	dst= ""

	metric = "http://localhost:8080/wm/routing/paths/slow/00:00:00:00:00:00:00:02/00:00:00:00:00:00:00:01/10/json"
	data = requests.get(metric)
	jdata = json.loads(data.content)
	
	#dst = jdata ['src_dpid']
	#srcShortID = src.split(":")[7]
	content = data.content

	#print data.content
	#print jdata['results'][0]
	#print type(content)
	#print type(jdata)
	for i in jdata['results']:
		src = i['src_dpid'].encode('ascii','ignore')
		route = i['src_dpid'].split(":")[7]
		cost = (int)(i['hop_count'])
		#print cost
		#print i
		for j in i['path']:
		#switch = j
			switch = j['dpid']
			if switch == prevswitch:
				continue
			elif switch == src:
				continue
			else:
				switchtmp = switch.split(":")[7]
				route = route + "::" + switchtmp
				prevswitch = switch
#	print route
		finalLinkTX[route] = cost
		
	
get_hopcount()
shortestPath = min(finalLinkTX, key=finalLinkTX.get)
print shortestPath
