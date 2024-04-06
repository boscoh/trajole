# build local client
cd config
cp local.prod.json config.json
cd ../client
npm run build
rm -rf ../rshow/client
cp -r dist ../rshow/client
git add ../rshow/client
cd ..
git add rshow/client
