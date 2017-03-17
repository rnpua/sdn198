#!/usr/bin/env python

import asyncio
import websockets
import time
from random import randint
import psutil
import re
import subprocess
import argparse

parser = argparse.ArgumentParser()								#argument parser, takes in interface to listen
parser.add_argument("interface", nargs='?', default="empty")
args = parser.parse_args()

async def hello():
	while True:
		async with websockets.connect('ws://localhost:8765') as websocket:
			tput = getTput()		#replace function depending on network metric
			await websocket.send(str(tput))		#send as string
			#cmd = subprocess.Popen("/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport -I en0", shell=True, stdout=subprocess.PIPE)
			# ^ is sample func, already included in getLink() or getTput()
			time.sleep(1)

			myVariable = 1

def getTput():		#insert arguments depending on argparse
	net = psutil.net_io_counters(pernic=True)['en0']
	time.sleep(1)
	net2 = psutil.net_io_counters(pernic=True)['en0']
	temp = net2.bytes_sent - net.bytes_sent				#sample metric
	return temp

def getLink():		#insert arguments depending on argparse
	link = subprocess.check_output('iwconfig %s' % args.interface, shell=True, stdout=subprocess.PIPE)
	matchObj = re.search(b'Link Quality=([0-9]{1,2})\/([0-9]{1,2})', link)
	return "%s:%f" % (args.interface, int(matchObj.group(1))/int(matchObj.group(2)))

asyncio.get_event_loop().run_until_complete(hello())

##########################################
#if psutil is unavailable
# #!/usr/bin/python3

# def get_bytes(t, iface='wlan0'):
#     with open('/sys/class/net/' + iface + '/statistics/' + t + '_bytes', 'r') as f:
#         data = f.read();
#     return int(data)

# if __name__ == '__main__':
#     (tx_prev, rx_prev) = (0, 0)

#     while(True):
#         tx = get_bytes('tx')
#         rx = get_bytes('rx')

#         if tx_prev > 0:
#             tx_speed = tx - tx_prev
#             print('TX: ', tx_speed, 'bps')

#         if rx_prev > 0:
#             rx_speed = rx - rx_prev
#             print('RX: ', rx_speed, 'bps')

#         time.sleep(1)

#         tx_prev = tx
#         rx_prev = rx


######## RANDOM SHT

# while True:
# 	cmd = subprocess.Popen("iwconfig %s".(interface), shell=True, stdout=subprocess.PIPE)
# 	for line in cmd.stdout:
# 		if 'Link Quality' in line:
# 		# 	print(line.lstrip('  ')),
# 		# elif 'Not Associated' in line:
# 		# 	print("No signal")

# 	time.sleep(1)