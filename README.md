# Live BTC Implied Volatility Charts
Using LedgerX public websocket API we're able to demonstrate using Redis as a multipurpose datastore.
Using a server side Lua script to check the received updates counter we can appropriately publish PUBSUB messages to the
listening [Bokeh](https://docs.bokeh.org/en/latest/) app and store the bid/ask prices to a 
[RedisTimeSeries](https://oss.redislabs.com/redistimeseries/) data type atomically.

The Bokeh app displays the implied volatility calculated from the best bid and offer prices received over websocket.
We're using the Black-Scholes formula implemented by the [vollib](http://vollib.org/) library.

We get the price of bitcoin from polling the coinbase API every 3 seconds.

This allows traders to do further analysis and find opportunities in possible mispricings in the volatility component of
the options pricing model.

## Setup

Install [Redis](https://redis.io/) and [RedisTimeSeries](https://oss.redislabs.com/redistimeseries/)
Next, clone the repository and install the dependencies in requirements.txt (`pip -r requirements.txt` in a venv)
Now run `ledgerx_ws.py` which is the script consuming the websocket stream from LedgerX and run 
`bokeh serve --show iv_app.py` from the project root to start up the Bokeh server application and open a web browser to
the local URL.

There are pre-cache files `contracts.pkl` and `id_table.json` which are loaded so no authenticated requests are needed.
If you have a LedgerX account and API key, you can create a file named `secret` with the API key on the first line which
will enable authenticated API queries.

### Docker Install (WIP)
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