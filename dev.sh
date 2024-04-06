# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal

psword -k node
psword -k mambaforge
psword -k rshow

echo "$1"
if [ "$1" == "traj" ]; then
    ttab "rshow --dev traj examples/trajectory.h5" ;
elif [ "$1" == "matrix" ]; then
    ttab "cd examples; rshow --dev matrix matrix" ;
elif [ "$1" == "fes" ]; then
    ttab "rshow --dev matrix examples/fes/fes.rshow.yaml" ;
elif [ "$1" == "scan1" ]; then
    ttab "cd examples/scan1; rshow --dev matrix scan1/fes.rshow.yaml " ;
elif [ "$1" == "frame" ]; then
    ttab "rshow --dev frame examples/3hhm.pdb" ;
elif [ "$1" == "ligands" ]; then
    ttab "cd examples/ligands; rshow --dev ligands receptor.pdb fred100.sdf"
elif [ "$1" == "cam3" ]; then
    ttab "cd examples/model5; rshow --dev matrix matrix_fes0.yaml"
elif [ "$1" == "cam3t" ]; then
    ttab "cd examples/run5; rshow --dev matrix fes.rshow.yaml"
else
    echo "Didn't recognize $1: traj foam matrix fes scan1 temper frame ligands"
    exit 1
fi

ttab "cd client; npm run dev;"

rshow open-url http://localhost:9023 http://localhost:3333/#/foamtraj/0
