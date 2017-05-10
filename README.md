# sdn198
For testing and checking codes only

1. dst ay magiging yung gateway na mafilter out ni eric.
2. metrics na pwede pagpilian ay ang hop count, latency, at rx/tx


Scope and limitation.
1. Hindi magawa yung hop count at latency dahil sa batman. Hindi mabago yung next hop niya at hop penalty. so lagi siyang shortest path. 
2. Mas maganda sana if mag balance ng route if may cumonnect na bago imbis na ipoll yung lahat ng src_ip. mas makakabalance ng maayos pag ganun

Setting up the Gateway nodes
1. 198/setup/gateway.sh or gateway2.sh
2. Then perform ( transfer of wlan1 to namespace
    new terminal: ip netns exec blue bash 
    old terminal: ps -ea | grep bash........dmesg | grep phy....... iw phy set netns 14123/1440/1462 (the numbers that are in tty2 only, 
    never tty1)
    new terminal: ip link list
3. Then at namespace, run 198/minipc/gateway.sh
4. Then we have access to the Internet
      
Setup of mesh for testing
1. Controller enp4s0 should be 192.168.1.208
2. AFter setting up of minipc ap, nodes, and gateway
  - a. Namespace at AP, ping 192.168.123.13/ or the gateways
  - b. Namespace at GW, ping 192.168.123.10/ or the access points
  - c. Change the resolve.conf file in the namespace in the access points - change domain name to 8.8.8.8
  * the access points and gateways' namespace ip address should appear in Floodlight topology
3. Run balancer code to push flows. Then the namespaces should be able to ping each other. The access points should be able to access the
   Internet. 

