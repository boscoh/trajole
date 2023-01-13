cd rshow
echo "$PWD"
isort **/*py
black **/*py

cd ../client
echo "$PWD"
npm run format
