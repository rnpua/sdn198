#!/usr/bin/env python

import requests #if not found. type pip install requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit

route = {}
cost = 0
finalLinkTX = {}
prevswitch = ""
switch = ""

route = ""

metric = "http://localhost:8080/wm/routing/paths/slow/00:00:00:00:00:00:00:01/00:00:00:00:00:00:00:02/5/json"
data = requests.get(metric)
jdata = json.loads(data.content)
src = '00:00:00:00:00:00:00:02'
#dst = jdata ['src_dpid']
srcShortID = src.split(":")[7]

#print jdata
for i in jdata['results']:
	route = srcShortID
	if (i['hop_count']):
		cost = i['hop_count']
		for key in i['path']:
			switch = key.split(":")[7]
			if (srcShortID == switch):
				continue
			elif(prevswitch == switch):
				continue
			else:
				route = route + "::" + switch 
			prevswitch = switch 
	finalLinkTX[route] = cost
			 
print finalLinkTX
