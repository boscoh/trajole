source ../.venv/bin/activate
echo "Example: $1"
if [ "$1" == "traj" ]; then
    trajole --dev traj ./traj/trajectory.h5
elif [ "$1" == "matrix" ]; then
    trajole --dev matrix ./matrix
elif [ "$1" == "fes" ]; then
    trajole --dev matrix ./fes/matrix.yaml
elif [ "$1" == "scan1" ]; then
    trajole --dev matrix ./scan1/matrix.yaml
elif [ "$1" == "frame" ]; then
    trajole --dev frame ./frame/3hhm.pdb
elif [ "$1" == "ligands" ]; then
    cd ./ligands; trajole --dev ligands receptor.pdb fred100.sdf
elif [ "$1" == "re" ]; then
    trajole --dev matrix ./temper/matrix.yaml
elif [ "$1" == "cam3t" ]; then
    trajole --dev matrix ./run5/matrix.yaml
else
    echo "Didn't recognize $1: traj foam matrix fes scan1 temper frame ligands re cam3t"
    exit 1
fi