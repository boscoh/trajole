source ../.venv/bin/activate
echo "Example: $1"
if [ "$1" == "traj" ]; then
    trajolecule --dev traj ./traj/trajectory.h5
elif [ "$1" == "matrix" ]; then
    trajolecule --dev matrix ./matrix
elif [ "$1" == "fes" ]; then
    trajolecule --dev matrix ./fes/matrix.yaml
elif [ "$1" == "scan1" ]; then
    trajolecule --dev matrix ./scan1/matrix.yaml
elif [ "$1" == "frame" ]; then
    trajolecule --dev frame ./frame/3hhm.pdb
elif [ "$1" == "ligands" ]; then
    cd ./ligands; trajolecule --dev ligands receptor.pdb fred100.sdf
elif [ "$1" == "re" ]; then
    trajolecule --dev matrix ./temper/matrix.yaml
elif [ "$1" == "cam3t" ]; then
    trajolecule --dev matrix ./run5/matrix.yaml
else
    echo "Didn't recognize $1: traj matrix fes scan1 temper frame ligands re cam3t"
    exit 1
fi