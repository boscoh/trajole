cd config
cp local.config.prod.json local.config.json
cd ..
cd client
npm run build
git add dist

