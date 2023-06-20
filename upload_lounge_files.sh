./build_lounge_client.sh
rsync -avz --progress --exclude '.DS_Store' --exclude 'client/node_modules' --exclude 'rshow/server/lounge/last_views.yaml' * bosco@216.153.60.196:rs/rshow
