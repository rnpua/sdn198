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

src_ip="192.168.123.10"
dst_ip="192.168.123.13"

src_ip_switch = "00:00:00:00:00:00:00:01"
dst_ip_switch = "00:00:00:00:00:00:00:03"

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
	src = int(switch[src_ip].split(":",7)[7],16)
	dst = int(switch[dst_ip].split(":",7)[7],16)

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
		start = switch[src_ip]
		src = switch[src_ip]
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

def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()
	#print cmd
	print "\n***", terminalOutput, "\n"

def flowRule(currentNode, flowCount, inPort, outPort, staticFlowURL):

	global count
	global bestPath

	outPortTemp = outPort
	inPortTemp = inPort
	if (count+1<len(bestPath)):

		nextNode = "00:00:00:00:00:"+bestPath[count+1].split(":")[7]


		if (count==0): #First node
			prevNode = deviceMAC[src_ip]
			#print "first node"

		else: # Subsequent nodes
			prevNode = "00:00:00:00:00:"+bestPath[count-1].split(":")[7]
			outPortTemp = "in_port"
			inPortTemp = outPortTemp
			#print "sub node"		
			

	elif (count+1==len(bestPath)):#last node:
		prevNode = "00:00:00:00:00:"+bestPath[count-1].split(":")[7]
		nextNode = deviceMAC[dst_ip]		
		#print "last node"

	
	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    "name":"flow" + str(flowCount),
	    "cookie":"0",
	    "priority":"32766",
	    "in_port":inPort,
		"eth_src": deviceMAC[src_ip],
	    "active":"true",
	    "actions":"set_field=eth_dst->"+nextNode+",output=" + outPortTemp
	}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

	flowCount = flowCount + 1


	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    "name":"flow" + str(flowCount),
	    "cookie":"0",
	    "priority":"32766",
	    "in_port":outPort,
		"eth_src": deviceMAC[dst_ip],
	    "active":"true",
	    "actions":"set_field=eth_dst->"+prevNode+",output=" + inPortTemp
	}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)
	
	count = count + 1

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

	shortestPath = min(finalLinkTX, key=finalLinkTX.get)

		 	
	print "\n\nRoutes: ", finalLinkTX
	print "\n\nShortest Path: ",shortestPath


	currentNode = shortestPath.split("::",2)[0]
	nextNode = shortestPath.split("::")[1]

	port = linkPorts[currentNode+"::"+nextNode]
	outPort = port.split("::")[0]
	inPort = hostPorts[src_ip+"::"+switch[src_ip].split(":")[7]]


	bestPath = path[shortestPath]
	flowRule(currentNode,flowCount,inPort,outPort,staticFlowURL)
	flowCount = flowCount + 2
	
	previousNode = currentNode

	for currentNode in range(0,len(bestPath)):
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
			
			flowRule(bestPath[currentNode].split(":")[7],flowCount,str(inPort),str(outPort),staticFlowURL)
			flowCount = flowCount + 2
			previousNode = bestPath[currentNode].split(":")[7]

			
def loadbalance():

	linkURL = "http://localhost:8080/wm/topology/links/json"
	getResponse(linkURL,"findSwitchLinks")
	

	findSwitchRoute()
	getLinkCost()

	print "\n\nBefore Loadbalancing Routes: ", finalLinkTX
	addFlow()
	
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
		deviceInfo = "http://localhost:8080/wm/device/"
		getResponse(deviceInfo,"deviceInfo")
		loadbalance()


		time.sleep(60)
	except KeyboardInterrupt:
		break
		exit()
