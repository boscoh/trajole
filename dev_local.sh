# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
psword -k npm
psword -k rshow
psword -k serve.py
ttab "cd client; npm run dev "
#ttab "rshow2 --dev traj-foam 2"
#ttab "cd examples; rshow2 --dev matrix matrix"
#ttab "rshow2 --dev fes examples/fes"
ttab "rshow2 --dev traj examples/trajectory.h5"
#ttab "cd examples/temper; rshow2 --dev re ."
#ttab "rshow2 --dev frame examples/3hhm.pdb"
#ttab "cd examples/ligands; rshow2 --dev ligands 2vuk_220C.pdb 2vuk.oeb 2vuk.csv"
sleep 0.5
open http://localhost:3333/#/foamtraj/0
