FROM ubuntu:18.04

WORKDIR /home/

### Install packages and utilities

RUN apt-get update && \
    apt-get -yy install git python3 python3-pip graphviz xdg-utils
RUN pip3 install solidity_parser solc-select graphviz
RUN git clone https://github.com/MingxiYe/solc-DApp.git