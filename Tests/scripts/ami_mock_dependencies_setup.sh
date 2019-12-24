#!/usr/bin/bash
echo "Starting mitmproxy dependencies setup"
echo "-------------------------------------"
echo "Installing development requirements for installing python3 on Linux Amazon 2 instance."
sudo yum -y install gcc bzip2-devel ncurses-devel gdbm-devel xz-devel sqlite-devel 
sudo yum -y install openssl-devel tk-devel uuid-devel readline-devel zlib-devel libffi-devel
echo "Downloading python3 source binaries."
# disable-secrets-detection-start
wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
# disable-secrets-detection-end
tar xzf Python-3.8.0.tgz
cd Python-3.8.0
./configure ––enable–optimizations
sudo make -j 8
sudo make altinstall
echo "Python3.8 installed."
python3 -m pip install -U pip --user
pip install python-dateutil --user
pip install mitmproxy --user
echo "Python 'python-dateutil' and 'mitmproxy' installed."
echo "mitmproxy dependencies setup completed"
echo "--------------------------------------"
