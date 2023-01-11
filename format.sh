cd bin
echo "$PWD"
isort *
black *

cd ../rshow
echo "$PWD"
isort **/*py
black **/*py

