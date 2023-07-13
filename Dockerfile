FROM ubuntu:jammy

RUN apt-get update
RUN apt-get install -y curl git python3 python3-pip

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

RUN useradd -m ubuntu

USER ubuntu
ENV SHELL=/bin/bash
RUN curl -sqL https://foundry.paradigm.xyz | bash
RUN ~/.foundry/bin/foundryup

CMD ["/bin/bash", "-l", "-i", "/app/cmd.sh"]
