# Nexus tokenomics

## Working with docker

Build docker image and tag it as "ape":

`docker build . -t ape`

Mount current directory as `/app` inside the docker container, set current directory to `/app` and run the sim script using the ape image we've just created:

`docker run -it -v $PWD:/app -w /app ape`
