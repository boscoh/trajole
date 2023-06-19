# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
psword -k node
psword -k mambaforge
psword -k rshow
psword -k serve.py
ttab "cd client; npm run dev "

# ttab "rshow --dev traj-foam 17"
#ttab "cd examples; rshow --dev matrix matrix"
#ttab "python rshow/cli.py --dev fes examples/fes"
ttab "cd examples/scan1; python ../../rshow/cli.py --dev fes "
#ttab "python rshow/cli.py --dev traj examples/trajectory.h5"
#ttab "cd examples/temper; rshow --dev re ."
#ttab "python rshow/cli.py --dev frame examples/3hhm.pdb"
#ttab "cd examples/ligands; rshow --dev ligands 2vuk_220C.pdb 2vuk.oeb 2vuk.csv"

rshow open-url http://localhost:9023 http://localhost:3333/#/foamtraj/0
