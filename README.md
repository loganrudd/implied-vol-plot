# implied-vol-plot
Using the LedgerX public websocket API we're able to get live top of the orderbook updates for an option chain with over 150 different contracts and save the data to a RedisTimeSeries type as well as publish updates to listening subscribers.  An example subscriber, an interactive plot showing the implied volatility skew of the selected expiration and type (call or put).

## Setup

Install docker: https://docs.docker.com/engine/install/

Run the command `sysctl vm.overcommit_memory=1` to avoid background save failure under low memory condition

Install docker-compose: https://docs.docker.com/compose/install/

If you don't configure docker to be used without sudo you'll have to add sudo in front of any docker command

To build image: `sudo docker build -t iv_app:dev .`

To run image interactively, mapping port 5006 from the container to 5006 on your local machine:
`sudo docker run -it -p 5006:5006 -w "/implied-vol-plot" -v "$(pwd):/implied-vol-plot" iv_app:dev bash`

To run it in the background in detached mode:
`sudo docker run -d -p 5006:5006 -w "/implied-vol-plot" -v "$(pwd):/implied-vol-plot" iv_app:dev`

Docker-compose:

To start services: `docker-compose up` #can add -d flag to run in background
To stop services: `docker-compose down`
To run a specific service interactively: `docker-compose exec <name-of-service-in-docker-compose-yaml> sh`