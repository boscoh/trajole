./build-client.sh
rsync -avz --progress --exclude '.DS_Store' * bosco@216.153.60.196:lounge
