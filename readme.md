
## rshow: integrated ligand/energy-surface trajectory viewer

This viewer allows specialized views of MD trajectories:

- directly use .h5 to optimize scrolling through trajectory
- an integrated 2d matrix view with trajectory
- integrated pocket discovery tool
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


# Release Notes
- 1.6.11
  - more bug fixes
- 1.6.10
  - bug fixes for loading frames
- 1.6.9
  - multiple matrix
- 1.6.8
  - always strips water by default
- 1.6.7
  - autodetect sparse versus dense matrix
- 1.6.6
  - defaults to rshow.matrix.yaml
  - handles uploads of matrix json or plain matrix double list
  - popups on left adjusts
  - autodetects sparse versus full matrix in fes
- 1.6.5
  - consolidate with easytraj 0.2.5 and foamdb 0.4.0
- 1.6.4
  - import cleanup
  - logging
  - easytrajh5 0.2.3
- 1.6.3
  - import bus
- 1.6.2
  - alphaspace toggle bug
  - easytrajh5 bus
- 1.6
  - dep to easytrajh5
  - file_mode a/r detect
  - ensemble view
  - slideshow
- 1.5.2
  - distance plots
- 1.5
  - ligand focus
  - LRU fixed
  - select_min_frame
- 1.4
  - dry_topology streaming
  - reworked async calls
  - Alphaspace Radius UX - pockets panel
  - refactored Vue components
  - Vuex for state
  - hydrogen on/off option
  - profiling logging output
- 1.3.4
  - logging
- 1.3.3
  - removed FES remapper
- 1.3.2
  - deprecated FreeEnergySurface
- 1.3.1
  - removed foamdb as dep (creates pip install issues)
- 1.3
  - AS Communities
  - compatible with RSeed 2.2
- 1.2
    - frames in url query
- 1.1
  - alphaspace frame bug fix
- 1.0
  - firs release


