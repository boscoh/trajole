
## rshow: integrated ligand/energy-surface trajectory viewer

This viewer allows specialized views of MD trajectories:

- an integrated view of the Free Energy Surface of 2 collective-variables
  and the associated conformations in a trajectory
- fast view of trajectory.h5 file
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

