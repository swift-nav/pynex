#!/usr/bin/env bash


function install_deps_debian () {
    # Sudo'd version of travis installation instructions
    sudo apt-get update
    sudo apt-get install python-software-properties
    sudo apt-get -y install libhdf5-serial-dev \
         python-pip \
         python-dev
}

function install_deps_osx () {
    if [[ ! -x /usr/local/bin/brew ]]; then
        echo "You're missing homebrew"
        exit 1
    fi
    brew install homebrew/science/hdf5
    sudo easy_install pip
}

if [[ "$OSTYPE" == "linux-"* ]]; then
    install_deps_debian
elif [[ "$OSTYPE" == "darwin"* ]]; then
    install_deps_osx
else
    echo "This script does not support this platform. Please file a Github issue!"
    exit 1
fi

