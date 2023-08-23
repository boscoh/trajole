cd config
cp lounge.config.json config.json
cd ../client
npm run build
rm -rf ../rshow/server/lounge/client
cp -r dist ../rshow/server/lounge/client
git add ../rshow/server/lounge/client

