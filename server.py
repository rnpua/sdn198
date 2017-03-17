#!/usr/bin/env python

import asyncio
import websockets
import threading
import re
import threading
import time
import argparse

parser = argparse.ArgumentParser()							#argument parser, takes in host
parser.add_argument("host", nargs='?', default="empty")
args = parser.parse_args()

exitFlag = 0

sample = 1.5

class myThread (threading.Thread):
	def __init__(self, threadID, name):			#initializations
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):								#run main thread func
		print ("Starting " + self.name)
		myFunction(self.name)
		print ("Exiting " + self.name)

def myFunction(threadName):		#thread functionality split
	global tput
	global sample
	#insert global variables here s.t. both threads access the same variable
	if threadName == "Receive": #coroutine of receiver from socket to GW
		while True:
			#if exitFlag:
			#	threadName.exit()
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			loop = websockets.serve(recv, 'localhost', 8765) 	#replace localhost with args.host
			#print("start_server:", start_server)
			asyncio.get_event_loop().run_until_complete(loop)
			asyncio.get_event_loop().run_forever()
	else: #coroutine to balancer
		while True:
			#if exitFlag:
			#	threadName.exit()
			#insert code here
			print("Balancer:%f" % float(sample))
			time.sleep(1)
			#exitFlag = 1

async def recv(websocket, path):
	global sample
	print("Receiving")
	tput = await websocket.recv()
	print("Received")
	sample = tput
	time.sleep(5)
	#link = re.search('[-+]?\d*\.\d+',tput)		#parse sent message to get float by regex
	#print(float(link))
	#sample = link
	# insert dictionary edit here

#create new threads
thread1 = myThread(1, "Receive")		#create first thread for receiving status updates
thread2 = myThread(2, "Balance")		#create another for loadbalancing

#start new threads
thread1.start()
thread2.start()
thread1.join()							#joining threads to close both
thread2.join()
print ("Exiting Main Thread")