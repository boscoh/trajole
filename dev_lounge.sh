# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
psword -k npm
psword -k rseed
psword -k serve.py
ttab "cd client; npm run dev "
ttab "cd server; python rshow/server/lounge/serve.py -c"
sleep 0.5
open http://localhost:3333
