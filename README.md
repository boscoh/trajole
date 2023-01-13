
## rshow: integrated ligand/energy-surface trajectory viewer

This viewer allows specialized views of MD trajectories:

- directly use .h5 to optimize scrolling through trajectory
- an integrated view of the Free Energy Surface of 2 collective-variables
  and the associated conformations in a trajectory
- integrated table of multiple ligands sampled against a single pdb file
- energy decomposition matrices of a run of temperature baths in
  a set of parallel tempering trajectories 

```
Usage: rshow [OPTIONS] COMMAND [ARGS]...

  rshow: : integrated analysis/protein viewer

  (C) 2021 Redesign Science

Options:
  --dev              Run server in dev mode (no break/no open browser)
  --solvent          Keep solvent
  --hydrogen         Keep hydrogens
  --background TEXT  Background color to jolecule
  --port INTEGER     port number
  --help             Show this message and exit.

Commands:
  fes        Free-Energy Surface of Collective Variables
  frame      Ligand browser
  ligands    Ligand browser
  matrix     Generic 2D surface linked to a set of trajectories
  re         Replicas in a replica-exchange simulation
  re-dock    Replicas in a replica-exchange simulation
  traj       Trajectory of an MD simulation
  traj-foam  Trajectory of a MD simulation loaded from FoamDB
```

In particular, if you have installed `foamdb` (see installation), you can
view the trajectories stored in our distributed database:

    rshow traj-foam 15
   

## Developing rshow

rshow has two components

- back-end server which is a Python fastapi backend server 
  that reads trajectories and serves it over a local port
- front-end client that runs in the browser and displays
  free-energy surfaces and proteins

## Building the rshow client in development mode

First you must install the dependencies in rseed/rseed/jolecule/vue:

    npm install

Then you must install jolecule somewhere in your system (not in the
rseed directory).

In /path/to/jolecule:

    npm link

Then in rshow/client:

    npm link jolecule

Once linked, we can build the client:

    npm run build




# Janan's Lounge server

Webserver front-end to the FoamDB trajectory database.


## 0. Prerequisite

```
sudo apt-get update
```


## 1. NGINX

NGinx maps incoming calls at 216.153.60.196:80 to internal 127.0.0.1:9023 on the VM

```
sudo apt install nginx
sudo rm /etc/nginx/default
sudo mkdir /var/log/nginx/lounge
```

Create `/etc/nginx/sites-enabled/fastapi`:
```
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    # server_name _ lounge.redesignscience.com 216.153.60.196;
    location / {
        proxy_pass http://127.0.0.1:9023;
        # Simple requests
        if ($request_method ~* "(GET|POST)") {
          add_header "Access-Control-Allow-Origin"  *;
        }

        # Preflighted requests
        if ($request_method = OPTIONS ) {
          add_header "Access-Control-Allow-Origin"  *;
          add_header "Access-Control-Allow-Methods" "GET, POST, OPTIONS, HEAD";
          add_header "Access-Control-Allow-Headers" "Authorization, Origin, X-Requested-With, Content-Type, Accept";
          return 200;
        }
    }
}
```

Restart `sudo systemctl restart nginx`   
Logs: `/var/log/nginx/lounge/error.log`


## 2. LOUNGE SERVER

Runs the python fastapi app on uvicorn on 127.0.0.1:9023.  

Install `awscli` and `argo` separately.  
Use `rs_install` to install `rs`.

Install lounge from our github repo. It will attempt to set foamdb
to the right path if no HOME is detected.

```
cd lounge
python setup.py install
cd server
```

Ensure `lounge/server/config.prod.json`:
```
{
    # for client
    "apiUrl": "http://lounge.redesignscience.com/rpc-run",  

    # for server
    "host": "127.0.0.1",
    "port": 9023
}
```

Test on command line:
```
cd lounge/server
python serve.py
```



## 3. SUPERVISOR - run job

Runs the python fastapi app in the background as a restartable process:

```
sudo apt install supervisor
mkdir /var/log/lounge
```

Create `/etc/supervisor/conf.d/fastapi.conf`:
```
[program:fastapi_app]
directory=/home/bosco/rshow/rshow/server/lounge
environment=PYTHONPATH=/home/bosco/miniconda3/envs/rs/lib/python3.8/site-packages
command=/home/bosco/miniconda3/envs/rs/bin/python serve.py
autostart=true
user=bosco
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/lounge/errors
stdout_logfile=/var/log/lounge/logs
```

Restart: `sudo service supervisor start`

