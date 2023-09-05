FROM ubuntu:jammy

# add basic utils and python
RUN apt-get update
RUN apt-get install -y curl git inotify-tools python3 python3-pip

# add nodejs
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# add nodemon
RUN npm install -g nodemon

# install python deps
ADD requirements.txt .
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver
RUN rm requirements.txt

RUN useradd -m ubuntu

USER ubuntu
ENV SHELL=/bin/bash
ENV HOME=/home/ubuntu
ENV PATH=${HOME}/.foundry/bin:${HOME}/bin:${PATH}

# add foundry
RUN curl -sqL https://foundry.paradigm.xyz | bash
RUN foundryup

CMD nodemon --watch scripts -e py -x ape run sim
