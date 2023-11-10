# build local client
cd config
cp local.prod.json config.json
cd ../client
npm run build
rm -rf ../rshow/server/local/client
cp -r dist ../rshow/server/local/client
git add ../rshow/server/local/client
cd ..

# build lounge client
cd config
cp lounge.config.json config.json
cd ../client
npm run build
rm -rf ../rshow/server/lounge/client
cp -r dist ../rshow/server/lounge/client
git add ../rshow/server/lounge/client
cd ..
