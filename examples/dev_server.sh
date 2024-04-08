# remove dangling processes
source ../.venv/bin/activate
echo "Example: $1"
if [ "$1" == "traj" ]; then
    rshow --dev traj ./traj/trajectory.h5
elif [ "$1" == "matrix" ]; then
    rshow --dev matrix ./matrix
elif [ "$1" == "fes" ]; then
    rshow --dev matrix ./fes/matrix.yaml
elif [ "$1" == "scan1" ]; then
    rshow --dev matrix ./scan1/matrix.yaml
elif [ "$1" == "frame" ]; then
    rshow --dev frame ./frame/3hhm.pdb
elif [ "$1" == "ligands" ]; then
    cd ./ligands; rshow --dev ligands receptor.pdb fred100.sdf
elif [ "$1" == "re" ]; then
    rshow --dev matrix ./temper/matrix.yaml
elif [ "$1" == "cam3t" ]; then
    rshow --dev matrix ./run5/matrix.yaml
else
    echo "Didn't recognize $1: traj foam matrix fes scan1 temper frame ligands re cam3t"
    exit 1
fi