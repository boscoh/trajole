./build_lounge_client.sh
rsync -avz --progress --exclude '.DS_Store' --exclude 'node_modules' * bosco@216.153.60.196:rshow
