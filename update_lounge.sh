./build_local_client.sh

cd config
cp lounge.config.json config.json
cd ..

cd client
npm run build
rm -rf ../rshow/server/lounge/client
cp -r dist ../rshow/server/lounge/client
git add ../rshow/server/lounge/client
cd ..

rsync -avz --progress \
  --exclude '.DS_Store' \
  --exclude 'client/node_modules/' \
  --exclude 'rshow/server/lounge/data' \
  --exclude 'rshow/server/lounge/last_views.yaml' \
  * bosco@216.153.60.196:rs/rshow

ssh -t bosco@216.153.60.196 \
  "cd rs/rshow; /home/bosco/mambaforge/envs/rs/bin/pip install -e ."

ssh -t bosco@216.153.60.196 \
  "sudo service supervisor restart"
