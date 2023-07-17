# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal

psword -k node
psword -k mambaforge
psword -k rshow
psword -k serve.py

ttab "cd client; npm run dev "

echo "$1"
if [ "$1" == "traj" ]; then
    ttab "rshow --dev traj examples/trajectory.h5" ;
elif [ "$1" == "foam" ] ; then
    ttab "rshow --dev traj-foam 23" ;
elif [ "$1" == "matrix" ]; then
    ttab "cd examples; rshow --dev matrix matrix" ;
elif [ "$1" == "fes" ]; then
    ttab "rshow --dev fes examples/fes" ;
elif [ "$1" == "scan1" ]; then
    ttab "cd examples/scan1; rshow --dev fes " ;
elif [ "$1" == "temper" ]; then
    ttab "cd examples/temper; rshow --dev re ." ;
elif [ "$1" == "frame" ]; then
    ttab "rshow --dev frame examples/3hhm.pdb" ;
elif [ "$1" == "ligands" ]; then
    ttab "cd examples/ligands; rshow --dev ligands 2vuk_220C.pdb 2vuk.oeb 2vuk.csv"
else
    echo "Didn't recognize $1"
    exit 1
fi

rshow open-url http://localhost:9023 http://localhost:3333/#/foamtraj/0
