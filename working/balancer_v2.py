#!/usr/bin/env python

import requests #if not found. type pip install requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit
#from subprocess import Popen, PIPE
# Always enable statistics in controller


#src_ip="192.168.123.10"
#dst_ip="192.168.123.13"
dst_ip ="10.0.0.3"
#src_ip_switch = "00:00:00:00:00:00:00:01"
dst_ip_switch = "00:00:00:00:00:00:00:02"

def getResponse(url,choice):

	response = requests.get(url)
	

	if(response.ok):
		jData = json.loads(response.content)
		
		
		if(choice=="deviceInfo"):
			deviceInformation(jData)
		elif(choice=="findSwitchLinks"):
			findSwitchLinks(jData,switch[dst_ip])
		elif(choice=="linkTX"):		
			linkTX(jData,portKey)

	else:
		response.raise_for_status()

# Parses JSON Data To Find Switch Connected To H4
def deviceInformation(data):
	global switch
	global deviceMAC
	global hostPorts
	switchDPID = ""
	for i in data['devices']:	
		if(i['ipv4']):
			ip = i['ipv4'][0].encode('ascii','ignore')
			mac = i['mac'][0].encode('ascii','ignore')
			deviceMAC[ip] = mac
			for j in i['attachmentPoint']:
				for key in j:
					temp = key.encode('ascii','ignore')
					
					if(temp=="switch"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ip] = switchDPID
						
					elif(temp=="port"):
						portNumber = j[key]
						switchShort = switchDPID.split(":")[7]
						hostPorts[ip+ "::" + switchShort] = str(portNumber)
						
def findSwitchLinks(data,s):
	global switchLinks
	global linkPorts
	global G

	links=[]
	for i in data:
		src = i['src-switch'].encode('ascii','ignore')
		dst = i['dst-switch'].encode('ascii','ignore')

		srcPort = str(i['src-port'])
		dstPort = str(i['dst-port'])

		srcTemp = src.split(":")[7]
		dstTemp = dst.split(":")[7]
			
		G.add_edge(int(srcTemp,16), int(dstTemp,16))

		tempSrcToDst = srcTemp + "::" + dstTemp
		tempDstToSrc = dstTemp + "::" + srcTemp

		portSrcToDst = str(srcPort) + "::" + str(dstPort)
		portDstToSrc = str(dstPort) + "::" + str(srcPort)

		linkPorts[tempSrcToDst] = portSrcToDst
		linkPorts[tempDstToSrc] = portDstToSrc

		if (src==s):
			links.append(dst)
		elif (dst==s):
			links.append(src)
		else:
			continue

	switchID = s.split(":")[7]
	switchLinks[switchID]=links
	

def findSwitchRoute():
	pathKey = ""
	nodeList = []
	switch[src_ip] = src_ip_switch
	switch[dst_ip] = dst_ip_switch
	src = int(switch[dst_ip].split(":",7)[7],16)
	dst = int(switch[src_ip].split(":",7)[7],16)
	#print "src_ip:", src_ip

	for currentPath in nx.all_simple_paths(G, source=src, target=dst, cutoff=None):
		for node in currentPath:

			tmp = ""
			if node < 17:
				pathKey = pathKey + "0" + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:0" + str(hex(node)).split("x",1)[1]
			else:
				pathKey = pathKey + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:" + str(hex(node)).split("x",1)[1]
			nodeList.append(tmp)

		pathKey=pathKey.strip("::")

		path[pathKey] = nodeList
		#print "path:", path
		pathKey = ""
		nodeList = []

def linkTX(data,key):
	global cost
	port = linkPorts[key]
	port = port.split("::")[1]
	for i in data:
		if i['port']==port:#If this part gets error, just enable statistics in controller UI
			cost = cost + (int)(i['bits-per-second-tx'])
			print cost

def getLinkCost():
	global portKey
	global cost

	for key in path:
		start = switch[dst_ip]
		src = switch[dst_ip]
		srcShortID = src.split(":")[7]
		route = path[key][0].split(":")[7]

		for link in path[key]:
			temp = link.split(":")[7]
			
			if srcShortID==temp:
				continue
			else:
				route = route + "::" + temp
				

				portKey = srcShortID + "::" + temp

				commonport = linkPorts[portKey]

				tempport = commonport.split("::")[1]

				stats = "http://localhost:8080/wm/statistics/bandwidth/" + temp + "/" + tempport + "/json"

				getResponse(stats,"linkTX")
				srcShortID = temp
				src = link
				


		finalLinkTX[route] = cost
		cost = 0
		portKey = ""

def get_hopcount():
	#route = []
	global cost
	cost = 0
	#finalLinkTX = {}
	prevswitch = ""
	swtch = ""
	swtchtmp = ""
	route = ""
	metric = ""
	src = switch[dst_ip]
	dst = switch[src_ip]

	metric = "http://localhost:8080/wm/routing/paths/slow/" + src + "/" + dst + "/10/json"
	data = requests.get(metric)
	jdata = json.loads(data.content)
	
	#dst = jdata ['src_dpid']
	srcShortID = src.split(":")[7]
	content = data.content

	#print data.content
	#print jdata[0]
	#print content
	#print jdata
	for i in jdata['results']:
		src = i['src_dpid'].encode('ascii','ignore')
		route = i['src_dpid'].split(":")[7]
		cost = (int)(i['hop_count'])
		prevswtch = src
		#print cost
		for j in i['path']:
			#switch = j
			swtch = j['dpid']
			if swtch == prevswtch:
				continue
			elif swtch == src:
				continue
			else:
				swtchtmp = swtch.split(":")[7]
				route = route + "::" + swtchtmp
				prevswtch = swtch
		#print route
		finalLinkTX[route] = cost

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	#print cmd
	print "\n***", terminalOutput, "\n"

def flowRule(currentNode, flowCount, inPort, outPort, staticFlowURL):
	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	   	"name":"flow" + str(flowCount),
	   	"cookie":"0",
	   	"priority":"32768",
	    	"in_port":inPort,
		"eth_type": "0x0800",
		"ipv4_src": dst_ip,
		"ipv4_dst": src_ip,
		"eth_src": deviceMAC[dst_ip],
		"eth_dst": deviceMAC[src_ip],
	    	"active":"true",
	    	"actions":"output=" + outPort
		}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

	flowCount = flowCount + 1

	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    	"name":"flow" + str(flowCount),
	    	"cookie":"0",
	    	"priority":"32768",
	    	"in_port":outPort,
		"eth_type": "0x0800",
		"ipv4_src": src_ip,
		"ipv4_dst": dst_ip,
		"eth_src": deviceMAC[src_ip],
		"eth_dst": deviceMAC[dst_ip],
	    	"active":"true",
	    	"actions":"output=" + inPort
		}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

def addFlow():

	global count
	global bestPath

	print "\nStarting Route Computation..."

	# Deleting Flow
	#cmd = "curl -X DELETE -d \'{\"name\"??"flow1\"}\' http://127.0.0.1:8080/wm/staticflowpusher/json"
	#systemCommand(cmd)

	#cmd = "curl -X DELETE -d \'{\"name\"??"flow2\"}\' http://127.0.0.1:8080/wm/staticflowpusher/json"
	#systemCommand(cmd)

	flowCount = 1
	count =  0
	#staticFlowURL = "http://localhost:8080/wm/staticflowpusher/json"
	staticFlowURL = "http://localhost:8080/wm/staticentrypusher/json"

	if src_ip == "10.0.0.1":
		shortestPath = max(finalLinkTX, key=finalLinkTX.get)		
					
	elif src_ip == "10.0.0.2":
		shortestPath = min(finalLinkTX, key=finalLinkTX.get)

		 	
	print "\n\nRoutes: ", finalLinkTX
	print "\n\nShortest Path: ",shortestPath


	currentNode = shortestPath.split("::",2)[0]
	nextNode = shortestPath.split("::")[1]

	port = linkPorts[currentNode+"::"+nextNode]
	outPort = port.split("::")[0]
	inPort = hostPorts[dst_ip+"::"+switch[dst_ip].split(":")[7]]


	bestPath = path[shortestPath]
	flowRule(currentNode,flowCount,inPort,outPort,staticFlowURL)
	flowCount = flowCount + 2
	#print "bestpath:", bestPath
	#print "current node:", currentNode
	previousNode = currentNode

	for currentNode in range(0,len(bestPath)):
		#print "current node:", currentNode
		#print "current node:", bestPath[currentNode]
		if previousNode == bestPath[currentNode].split(":")[7]:
			continue
		else:
			port = linkPorts[bestPath[currentNode].split(":")[7]+"::"+previousNode]
			inPort = port.split("::")[0]
			outPort = ""
			if(currentNode+1<len(bestPath) and bestPath[currentNode]==bestPath[currentNode+1]):
				currentNode = currentNode + 1
				continue
			elif(currentNode+1<len(bestPath)):
				port = linkPorts[bestPath[currentNode].split(":")[7]+"::"+bestPath[currentNode+1].split(":")[7]]
				outPort = port.split("::")[0]
			elif(bestPath[currentNode]==bestPath[-1]):
				outPort = str(hostPorts[src_ip+"::"+switch[src_ip].split(":")[7]])
			
			#print "besthpath[-1]", bestPath[-1]
			flowRule(bestPath[currentNode].split(":")[7],flowCount,str(inPort),str(outPort),staticFlowURL)
			flowCount = flowCount + 2
			previousNode = bestPath[currentNode].split(":")[7]
	#finalLinkTX.clear()
	#print "finalLinkTX after clear:", finalLinkTX
			
def loadbalance():

	linkURL = "http://localhost:8080/wm/topology/links/json"
	getResponse(linkURL,"findSwitchLinks")
	

	findSwitchRoute()
	getLinkCost()
	#get_hopcount()
	
	print "\n\nBefore Loadbalancing Routes: ", finalLinkTX
	addFlow()
	#print "finalLinkTX before clear:", finalLinkTX
	#finalLinkTX.clear()
	#print "finalLinkTX after clear:", finalLinkTX
	#print "path:", path
	#path.clear()

while True:

	# Stores Info About H3 And H4's Switch
	switch = {}

	# Mac of H3 And H4
	deviceMAC = {}

	# Stores Host Switch Ports
	hostPorts = {}
	
	# Stores Switch To Switch Path
	path = {}

	# Switch Links

	switchLinks = {}

	# Stores Link Ports
	linkPorts = {}

	# Stores Final Link Rates
	finalLinkTX = {}

	# Store Port Key For Finding Link Rates
	portKey = ""

	# Stores Link Cost
	cost = 0
	# Graph
	G = nx.Graph()

	try:
		#deviceInfo = "http://localhost:8080/wm/device/"
		#getResponse(deviceInfo,"deviceInfo")
		#enableStats = "http://localhost:8080/wm/statistics/config/enable/json"
		#requests.put(enableStats)
		i = 1
		while (i < 3):
			if i == 1:
				src_ip="10.0.0.1"
				src_ip_switch = "00:00:00:00:00:00:00:01"
				src_name = "1"
			elif i == 2:
				src_ip="10.0.0.2"
				src_ip_switch = "00:00:00:00:00:00:00:03"
				src_name = "2"
			deviceInfo = "http://localhost:8080/wm/device/"
			getResponse(deviceInfo,"deviceInfo")
			loadbalance()
			#path = {}
			#print "finalLinkTX after clear:", finalLinkTX
			finalLinkTX.clear()
			path.clear()
			time.sleep(30)
			i = i+1

		#loadbalance()
		#addFlow()
		#time.sleep(60)
	except KeyboardInterrupt:
		break
		exit()
