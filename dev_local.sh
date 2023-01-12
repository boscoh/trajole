# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
ttab "cd client; npm run dev "
#ttab "rshow2 --dev traj-foam 2"
# ttab "rshow2 --dev matrix examples/matrix"
ttab "rshow2 --dev fes examples/fes"
#ttab "rshow2 --dev traj examples/trajectory.h5"
#ttab "rshow2 --dev re examples/re"
#ttab "rshow2 --dev frame examples/3hhm.pdb"
#ttab "rshow2 --dev ligands examples/ligands/5v9o_apo.pdb examples/ligands/5v9o_poses.sdf examples/ligands/5v9o_poses.csv"
sleep 0.5
open http://localhost:3333
