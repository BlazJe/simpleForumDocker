#!/bin/bash
set -x

# create new microk8s instance
sudo snap install microk8s --classic --channel=1.24/stable
mkdir -p ~/.kube
sudo microk8s config > ~/.kube/config
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

echo "Exit and log in again"