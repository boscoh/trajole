import os
import logging
from path import Path
from rseed.util.fs import load_yaml_dict
from rshow.make_app import make_app

logging.basicConfig(level=logging.INFO)

this_dir = Path(__file__).parent
client_dir = this_dir / "server/lounge/client"

config = load_yaml_dict(this_dir / "dev_config.yaml")

if config.server == "local":
    from rshow.server.local import handlers

    if "work_dir" in config:
        os.chdir(config.work_dir)

    handlers.init_traj_stream_from_config(config)

elif config.server == "lounge":

    from rshow.server.lounge import handlers

else:
    raise Exception("no config.server specified")

app = make_app(handlers, client_dir)
