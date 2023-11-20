FROM ubuntu:jammy

# add basic utils
RUN apt-get update
RUN apt-get install -y curl git inotify-tools ca-certificates gnupg python3 python3-pip

# add nodejs
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update
RUN apt-get install -y nodejs

# add nodemon
RUN npm install -g nodemon

# install python deps
ADD requirements.txt .
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver
RUN rm requirements.txt

RUN useradd -m ubuntu
USER ubuntu

CMD nodemon -w scripts -e py -x ape run sim
