cd config
cp config.dev.json config.json
cd ../client
npm run build
rm -rf ../rshow/server/local/client
cp -r dist ../rshow/server/local/client
git add ../rshow/server/local/client

