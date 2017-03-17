cd

# Install Oracle Java 8

sudo add-apt-repository ppa:webupd8team/java

sudo apt-get update

sudo apt-get install oracle-java8-installer

sudo apt install ant

git clone git://github.com/floodlight/floodlight.git

cd floodlight

git submodule init

git submodule update

ant
 
sudo mkdir /var/lib/floodlight

sudo chmod 777 /var/lib/floodlight

#Install Mininet, Wireshark and OpenFlow

cd

git clone git://github.com/mininet/mininet

cd mininet

cd util

bash install.sh -a

cd
