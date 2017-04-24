#!/usr/bin/env python

import requests #if not found. type pip install requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit

# Method To Get REST Data In JSON Format
def getResponse(url,choice):

	response = requests.get(url)
	#json_obj = urlopen(url).read()

	if(response.ok):
		jData = json.loads(response.content)
		
		
		if(choice=="deviceInfo"):
			deviceInformation(jData)
		elif(choice=="findSwitchLinks"):
			findSwitchLinks(jData,switch[h2])
			#print "switch:", switch[h2]
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
					#if(temp=="switchDPID"):
					if(temp=="switch"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ip] = switchDPID
						#print '"switch[ip]:"',switch[ip]
					elif(temp=="port"):
						portNumber = j[key]
						#print '"portNumber:"',portNumber	
						switchShort = switchDPID.split(":")[7]
						hostPorts[ip+ "::" + switchShort] = str(portNumber)
						#combination ng host and switch and kung anong port ng switch siya nakaconnect
						#print '"hostports:"',hostPorts[ip+ "::" + switchShort]
	#print "switch:", switch

# Finding Switch Links Of Common Switch Of H3, H4
#show the links connected to switch[h2] or the second host that user entered

def findSwitchLinks(data,s):
	global switchLinks
	global linkPorts
	global G

	links=[]
	#print "links:", links
	#print "s:", s
	for i in data:
		#print data
		src = i['src-switch'].encode('ascii','ignore')
		dst = i['dst-switch'].encode('ascii','ignore')

		srcPort = str(i['src-port'])
		dstPort = str(i['dst-port'])

		srcTemp = src.split(":")[7]
		dstTemp = dst.split(":")[7]
	
		#print '"srcTemp:"',srcTemp
			
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
	#print "links:", links
	#print "linkports:", linkPorts
	#port kung saan nakaconnect yung mga links
	#print '"switchLinks[switchID]:"',switchLinks[switchID]
	#print "switchlinks:", switchLinks

# Finds The Path To A Switch
# Find the paths or nodes from src to dst storing it in a dictionary named path
#so yung laman ng path ngayon ay path[pathKey]= nodeList or combination ng pathkey at yung mga nodes or switches na dadaanan niyan

def findSwitchRoute():
	pathKey = ""
	nodeList = []
	src = int(switch[h2].split(":",7)[7],16)
	dst = int(switch[h1].split(":",7)[7],16)
	#print "pathkey:", pathKey
	#print "nodelist:", nodeList
	for currentPath in nx.all_simple_paths(G, source=src, target=dst, cutoff=None):
		for node in currentPath:
			#currentPath is the available paths form src to dst while node is the nodes conatained in the current path
			#print "currentpath:", currentPath
			#print "node:", node
			#print "pathkey:", pathKey
			#tinatanngal niya yung laman ng tmp for every cycle ng loop
			tmp = ""
			if node < 17:
				#para lang malagyan ng 0x yung single digit number of nodes. 
				#if more than 17 na ata di na kelangan lagyan ng 0 before since two digits na
				pathKey = pathKey + "0" + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:0" + str(hex(node)).split("x",1)[1]
			else:
				pathKey = pathKey + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:" + str(hex(node)).split("x",1)[1]
			nodeList.append(tmp)
			#print "tmp:", tmp
			#print "nodelist:", nodeList

		pathKey=pathKey.strip("::")
		#removes the last two colons at the end of the pathkey
		#print "pathkey:", pathKey
		#portkey = pathKey
		#print '\nportkey:', portKey

		path[pathKey] = nodeList
		pathKey = ""
		nodeList = []

	#print path

# Computes Link TX

def linkTX(data,key):
	global cost
	port = linkPorts[key]
	#print '\ndport for TX:',port
	port = port.split("::")[1]
	#dst port lang kinukuha nito
	#print '\ndport for TX:',port
	for i in data:
		#print '\ndata for linkTX:',data
		if i['port']==port:
			cost = cost + (int)(i['bits-per-second-tx'])


# Method To Compute Link Cost
#computes link cost
def getLinkCost():
	global portKey
	global cost
	#print "linkports:", linkPorts
	for key in path:
		start = switch[h2]
		src = switch[h2]
		srcShortID = src.split(":")[7]
		route = path[key][0].split(":")[7]
		#print "path:", path
		#print "h2:", h2
		#print "src:", src
		#print "pathkey[0]",path[key][0] 
		#print "route:", route
		#print 'mid:', mid
		#route = routesrc + "::"

		for link in path[key]:
			#print "src:", src
			temp = link.split(":")[7]
			#print 'srcShortID:', srcShortID
			#print 'temp:', temp
			
			if srcShortID==temp:
				continue
				#if same yung src at yung unang node sa link skip lang since nakalagay 
				#na siya sa variable na route sa taas
			else:
				route = route + "::" + temp
				#route niya per pair of switch na dinadaanan
				#example path 1:3:2, so yung route ay laging
				#1::3, 3::2 
				#print 'route:', route

				portKey = srcShortID + "::" + temp
				#print 'portkey:', srcShortID + "::" + temp
				commonport = linkPorts[portKey]
				#linkports are the combination of switches and the src and dst ports
				#print 'commonport:', linkPorts[portKey]
				tempport = commonport.split("::")[1]
				#tempport ay yung destination port lang
				#print 'tempport:', commonport.split("::")[1]
				stats = "http://localhost:8080/wm/statistics/bandwidth/" + temp + "/" + tempport + "/json"
				#print 'stats:',stats
				#laman nung stats ay yung speed nung link from switch to dst port 
				#in other words minemeasure niya yung bits per second ng isang link
				getResponse(stats,"linkTX")
				srcShortID = temp
				src = link
				#print 'srcShortID:', srcShortID
				#print "src:", src

		#portKey = start.split(":")[7] + "::" + mid + "::" + switch[h1].split(":")[7]
		#print '\nportkeywithmid:', path[0]
		finalLinkTX[route] = cost
		#final link TX cost ng specific route
		#print "route:", route
		cost = 0
		portKey = ""
	print "finallinktx:", finalLinkTX

#Method for getting hop_count
#not applicable if entered hosts lie on the same switch
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
	src = switch[h2]
	dst = switch[h1]

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

#for calculating route using latency. not applicable if 
#entered hosts lie on the same switch
def get_latency():
	#route = []
	global cost
	cost = 0
	#finalLinkTX = {}
	prevswitch = ""
	swtch = ""
	swtchtmp = ""
	route = ""
	metric = ""
	src = switch[h2]
	dst = switch[h1]

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
		cost = (int)(i['latency'])
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
	print "\n***", terminalOutput, "\n"

def flowRule(currentNode, flowCount, inPort, outPort, staticFlowURL):
	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    "name":"flow" + str(flowCount),
	    "cookie":"0",
	    "priority":"32768",
	    "in_port":inPort,
		"eth_type": "0x0800",
		"ipv4_src": h2,
		"ipv4_dst": h1,
		"eth_src": deviceMAC[h2],
		"eth_dst": deviceMAC[h1],
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
		"ipv4_src": h1,
		"ipv4_dst": h2,
		"eth_src": deviceMAC[h1],
		"eth_dst": deviceMAC[h2],
	    "active":"true",
	    "actions":"output=" + inPort
	}

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

def addFlow():
	print "\nStarting Route Computation..."

	# Deleting Flow
	#cmd = "curl -X DELETE -d \'{\"name\":\"flow1\"}\' http://127.0.0.1:8080/wm/staticflowpusher/json"
	#systemCommand(cmd)

	#cmd = "curl -X DELETE -d \'{\"name\":\"flow2\"}\' http://127.0.0.1:8080/wm/staticflowpusher/json"
	#systemCommand(cmd)

	flowCount = 1
	staticFlowURL = "http://127.0.0.1:8080/wm/staticflowpusher/json"

	#print "key:", finalLinkTX
	print "switch:", switch
	shortestPath = min(finalLinkTX, key=finalLinkTX.get)
	#print "key:", finalLinkTX.get

		 	
	print "\n\nRoutes: ", finalLinkTX
	print "\n\nShortest Path: ",shortestPath


	currentNode = shortestPath.split("::",2)[0]
	#print "currentnode:", currentNode
	nextNode = shortestPath.split("::")[1]
	#print "nextnode:", nextNode

	# Port Computation

	port = linkPorts[currentNode+"::"+nextNode]
	outPort = port.split("::")[0]
	inPort = hostPorts[h2+"::"+switch[h2].split(":")[7]]
	#inport ay yung port nung second host entered
	#print "hosports:", hostPorts
	#print "port:", port
	#print "outport:", outPort
	#print "inport:", inPort

	flowRule(currentNode,flowCount,inPort,outPort,staticFlowURL)

	flowCount = flowCount + 2
	#bakit flowCount +2

	bestPath = path[shortestPath]
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
				outPort = str(hostPorts[h1+"::"+switch[h1].split(":")[7]])

			flowRule(bestPath[currentNode].split(":")[7],flowCount,str(inPort),str(outPort),staticFlowURL)
			flowCount = flowCount + 2
			previousNode = bestPath[currentNode].split(":")[7]

# Method To Perform Load Balancing
def loadbalance():
	linkURL = "http://localhost:8080/wm/topology/links/json"
	getResponse(linkURL,"findSwitchLinks")

	findSwitchRoute()
	#getLinkCost()
	#get_hopcount()
	get_latency()
	addFlow()

# Main

# Stores H1 and H2 from user
global h1,h2,h3

h1 = ""
h2 = ""

print "Enter Host 1"
h1 = int(input())

print "\nEnter Host 2"
h2 = int(input())

#print "\nEnter Host 3 (H2's Neighbour)"
#h3 = int(input())


h1 = "10.0.0." + str(h1)
h2 = "10.0.0." + str(h2)
h3 = "10.0.0.3"# + str(h3)


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

		# Enables Statistics Like B/W, etc
		enableStats = "http://localhost:8080/wm/statistics/config/enable/json"
		requests.put(enableStats)

		# Device Info (Switch To Which The Device Is Connected & The MAC Address Of Each Device)
		deviceInfo = "http://localhost:8080/wm/device/"
		getResponse(deviceInfo,"deviceInfo")

		# Load Balancing

		loadbalance()

		# -------------- PRINT --------------

		print "\n\n############ RESULT ############\n\n"

		# Print Switch To Which H4 is Connected
		print "Switch H4: ",switch[h3], "\tSwitchH3: ", switch[h2]

		print "\n\nSwitch H1: ", switch[h1]

		# IP & MAC
		print "\nIP & MAC\n\n", deviceMAC

		# Host Switch Ports
		print "\nHost::Switch Ports\n\n", hostPorts

		# Link Ports
		print "\nLink Ports (SRC::DST - SRC PORT::DST PORT)\n\n", linkPorts

		# Alternate Paths
		print "\nPaths (SRC TO DST)\n\n",path

		# Final Link Cost
		print "\nFinal Link Cost (First To Second Switch)\n\n",finalLinkTX

		print "\n\n#######################################\n\n"

		time.sleep(60)

	except KeyboardInterrupt:
		break
		exit()
