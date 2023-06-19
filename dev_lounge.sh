# install ttab using `npm i -g ttab`
# on mac, need to change
#   System Prefs -> Security -> Privacy -> Accessibility: add Terminal
psword -k node
psword -k mambaforge
psword -k rshow
psword -k serve.py
ttab "cd client; npm run dev "
ttab "python rshow/serve.py --dev"
rshow open-url http://localhost:9023 http://localhost:3333
