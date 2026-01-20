#!/bin/bash
set -x

# install everything we need for our workshop
# tested on Ubuntu 20.04 LTS

# install docker (we'll use quickndirty way as we're in a throwaway VM, but better to change this for serious work)
curl -fsSL https://get.docker.com | bash

# enables using docker without sudo for our username (ubuntu by default)
sudo usermod -aG docker $USER

# install kubectl
sudo curl -L https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl
sudo chmod +x /usr/local/bin/kubectl

#install minikube
sudo curl -L https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 -o /usr/local/bin/minikube
sudo chmod +x /usr/local/bin/minikube

# install stern
curl -L https://github.com/stern/stern/releases/download/v1.22.0/stern_1.22.0_linux_amd64.tar.gz | tar xz
sudo cp ~/stern_1.22.0_linux_amd64/stern /usr/local/bin/stern

# install kube-ps1 K8s prompt
sudo curl -L https://raw.githubusercontent.com/jonmosco/kube-ps1/master/kube-ps1.sh -o /usr/local/bin/kube-ps1.sh
sudo chmod +x /usr/local/bin/kube-ps1.sh

# kubectx
sudo curl -L https://raw.githubusercontent.com/ahmetb/kubectx/master/kubectx -o /usr/local/bin/kctx
sudo curl -L https://raw.githubusercontent.com/ahmetb/kubectx/master/kubens  -o /usr/local/bin/kns
sudo chmod +x /usr/local/bin/kctx
sudo chmod +x /usr/local/bin/kns

sudo curl -L https://raw.githubusercontent.com/ahmetb/kubectx/master/completion/kubectx.bash -o /usr/share/bash-completion/completions/kctx
sudo curl -L https://raw.githubusercontent.com/ahmetb/kubectx/master/completion/kubens.bash -o /usr/share/bash-completion/completions/kns

# ktx
sudo curl -L https://raw.githubusercontent.com/heptiolabs/ktx/master/ktx -o /usr/local/bin/ktx
sudo chmod +x /usr/local/bin/ktx

sudo curl -L https://raw.githubusercontent.com/heptiolabs/ktx/master/ktx-completion.sh -o /usr/share/bash-completion/completions/ktx

# kind
sudo curl -L https://kind.sigs.k8s.io/dl/v0.17.0/kind-linux-amd64 -o /usr/local/bin/kind
sudo chmod +x /usr/local/bin/kind


# add to .bashrc

tee -a ~/.bashrc <<'EOF'
# autocompletion stern
source <(stern --completion bash)
# autocompletion kubectl
source <(kubectl completion bash)
# alias for kubectl (yes, you'll type kubectl A LOT. Trust me on this.)
alias k=kubectl
complete -F __start_kubectl k
# enable ktx
source /usr/local/bin/ktx
# autocompletion minikube
source <(minikube completion bash)
# autocompletion kind
source <(kind completion bash)
# set Visual Studio Code as KUBE_EDITOR
# KUBE_EDITOR='code --wait'
# kube-PS1 prompt
source /usr/local/bin/kube-ps1.sh
# add kube-ps1 to default Ubuntu prompt
PS1='${debian_chroot:+($debian_chroot)}\(\033[01;32m\)\u@\h\(\033[00m\) $(kube_ps1):\(\033[01;34m\)\w\(\033[00m\)\$ '
EOF

###
### Now exit and login back again.
###

echo Now exit and login back again.
