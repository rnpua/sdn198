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

from websocket_server import WebsocketServer
import threading
import re
import time
import argparse
import copy

#src_ip="192.168.123.10"
#dst_ip="192.168.123.13"

#src_ip_switch = "00:00:00:00:00:00:00:01"
#dst_ip_switch = "00:00:00:00:00:00:00:03"

#global variables
deviceMAC = {}
switch = {}
hostPorts = {}
path = {}
switchLinks = {}
linkPorts = {}
finalLinkTX = {}
portKey = ""
cost = 0 
gateway = {}


parser = argparse.ArgumentParser()								#argument parser, takes in interface to listen
parser.add_argument("-s", "--server", default='127.0.0.1', help="host address, default localhost")
parser.add_argument("-p", "--port", default=9001, type=int, help="default 9001")
args = parser.parse_args()

#sample value
#finalLinkTX = {'01::04': 3756, '01::03::02': 40256, '01::03': 3740256, '01::02::03': 7838120, '01::04::03': 3740256, '01::02::04::03': 7838120, '01::04::02::03': 7838120}
finalLinkTX = {}
#threshold value for metric chosen, currently TX(bytes/sec)
THRESHOLD = 10000
#list of GW nodes reaching threshold
noGW = []

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	# server.send_message_to_all("Hey all, a new client has joined us")


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])


# Called when a client sends a message
def message_received(client, server, message):
	if len(message) > 200:
		message = message[:200]+'..'
	print("Client(%d) said: %s" % (client['id'], message))
	matchObj = re.search('(.*):(\d+)',message)					# parses client message
	# if int(matchObj.group(2)) > THRESHOLD:						# matchObj.group() contains {node, measurement}
	# 	if matchObj.group(1) not in noGW:
	# 		noGW.append(matchObj.group(1))
	# else:
	# 	if matchObj.group(1) in GW:
	# 		noGW.remove(matchObj.group(1))

	if matchObj.group(2) >= THRESHOLD:
		noGW[matchObj.group(1)] = matchObj.group(2)
	else:
		if matchObj.group(1) in noGW:
			del noGW[matchObj.group(1)]

#no use
def removeGW(links, nodes):
	for item in list(links.key()):
		for node in nodes:
			if item.endswith(node):
				del links[item]
				break

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
	global finalLinkTX

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

	# GW CODE HERE
	dummy = removeGW(copy.deepcopy(finalLinkTX), noGW)

	shortestPath = min(dummy, key=dummy.get)
	# shortestPath = min(finalLinkTX, key=finalLinkTX.get)

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

# USELESS INITIALIZATION, DEPRECATE/REPLACE WHEN POSSIBLE
class myThread (threading.Thread):
	def __init__(self, name, run_event):				#initializations
		threading.Thread.__init__(self)
		self.name = name
		self.run_event = run_event
	def run(self):
		print ("Starting ", self.name)
		myFunction(self, self.name, self.run_event)
		print ("Exiting ", self.name)

def myFunction(self, threadName, run_event):
	while run_event.is_set():									# insert loadbalancing **inside** the while loop
		#print finalLinkTX										# or your code is doomed to run forever
		#time.sleep(2)

		# Stores Info About H3 And H4's Switch
		switch = {}

		# Mac of H3 And H4
		#deviceMAC = {}

		# Stores Host Switch Ports
		hostPorts = {}

		# Stores Switch To Switch Path
		path = {}

		# Switch Links

		switchLinks = {}

		# Stores Link Ports
		linkPorts = {}

		# Stores Final Link Rates
		#global finalLinkTX

		# Store Port Key For Finding Link Rates
		portKey = ""

		# Stores Link Cost
		cost = 0
		# Graph
		G = nx.Graph()
		dst_ip = min(gateway, key=gateway.get)
		dst_ip_switch = min(gateway)

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


run_event = threading.Event()									# stop condition
run_event.set()
t1 = myThread("Balance", run_event)
t1.start()
try:
	server = WebsocketServer(args.port, args.server)
	server.set_fn_new_client(new_client)
	server.set_fn_client_left(client_left)
	server.set_fn_message_received(message_received)
	server.run_forever()
except KeyboardInterrupt:
	print "closing"
	run_event.clear()
	t1.join()
	print "closed"
