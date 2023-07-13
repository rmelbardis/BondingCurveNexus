FROM ubuntu:jammy

RUN apt-get update
RUN apt-get install -y curl git python3 python3-pip
RUN curl -sqL https://foundry.paradigm.xyz | bash && $HOME/.foundry/bin/foundryup

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

CMD ["python3", "scripts/run.py"]
