# bash script that starts the app on a native Ubuntu 17.10 installation

#!/bin/sh 

echo "Start building..."

sudo apt-add-repository universe
sudo apt-get update
sudo apt-get install python-pip
pip --version
sudo pip install tifffile
sudo pip install keras 
sudo pip install tensorflow==1.5 
sudo pip install pandas
sudo pip install matplotlib
sudo apt-get install python-tk
sudo pip install scikit-image

cd Desktop/CalciumImagingAnalyzer/sample

python sample.py

echo "Done!"
