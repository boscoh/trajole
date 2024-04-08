# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal

# check options for input example file
if [[ "$1" =~ ^(traj|foam|matrix|fes|scan1|temper|frame|ligands|re|cam3t)$ ]]; then
    echo "opening $1 example"
else
    echo "Pleas choose one of traj|foam|matrix|fes|scan1|temper|frame|ligands|re|cam3t"
    exit 1
fi

# clear older running jobs that got orphaned
if command -v psword &> /dev/null
then
  psword -k MacOS/Python
  psword -k mambaforge
  psword -k rshow
  psword -k node
fi

# run server in dev mode with reload on port 9023 with chosen example
ttab "cd examples; ./dev_server.sh $1"

# run client server on port 3333
ttab "cd client; npm run dev;"

# open client on browser when server is ready
source ./.venv/bin/activate
rshow open-url http://localhost:9023 http://localhost:3333/#/foamtraj/0
