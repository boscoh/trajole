./build-client-and-git-add.sh
rsync -avz --progress --exclude '.DS_Store' * bosco@216.153.60.196:lounge
#rsync -avz --progress --exclude='.DS_Store' --exclude="examples" --exclude="node_modules" --exclude=".git" ../rs/rseed bosco@216.153.60.196:
#rsync -avz --progress --exclude '.DS_Store' ../rs/rsjob bosco@216.153.60.196:
#rsync -avz --progress --exclude '.DS_Store' ../rs/AlphaSpace2 bosco@216.153.60.196:
#rsync -avz --progress --exclude '.DS_Store' ../rs/foamdb bosco@216.153.60.196:

