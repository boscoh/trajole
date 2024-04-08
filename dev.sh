# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
if [[ "$1" =~ ^(traj|foam|matrix|fes|scan1|temper|frame|ligands|re|cam3t)$ ]]; then
    echo "opening $1 example"
else
    echo "Pleas choose one of traj|foam|matrix|fes|scan1|temper|frame|ligands|re|cam3t"
    exit 1
fi
./dev_clear.sh
ttab "./dev_server.sh $1"
ttab "cd client; npm run dev;"
source ./.venv/bin/activate
rshow open-url http://localhost:9023 http://localhost:3333/#/foamtraj/0
