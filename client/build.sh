# set the port for the built client
cd ../config
cp local.prod.json config.json
cd ../client

# build local client
npm run build

# copy over to server directory
rm -rf ../server/client
cp -r dist ../server/client

# make sure changes are added to repo
cd ..
if [ -d ".git" ]; then
  echo "update git repo"
  git add ./server/client
fi
