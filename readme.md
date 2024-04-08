
## rshow: integrated ligand/energy-surface trajectory viewer

This viewer allows specialized views of MD trajectories:

- directly use .h5 to optimize scrolling through trajectory
- an integrated 2d matrix view with trajectory
- integrated table of multiple ligands sampled against a single pdb file
- interactive contact map
- interactive inter-atomic distance plots
- multiple instances
- port mapping for remote vm's

TODO:
- example with multiple matrix
- remove openeye ligand reading

```console
> rshow
Usage: rshow [OPTIONS] COMMAND [ARGS]...

  rshow: mdtraj h5 viewer

  (C) 2021 Redesign Science

Options:t
  --dev        Run continuous server
  --solvent    Keep solvent
  --port TEXT  port number
  --help       Show this message and exit.

Commands:
  frame      Open PDB or PARMED
  ligands    Open PDB with ligands in SDF
  matrix     Open H5 with matrix
  open-url   Open OPEN_URL when TEST_URL works
  traj       Open H5
```


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




