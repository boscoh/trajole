import os
from path import Path
from rseed.util.fs import load_yaml_dict
from rshow.make_app import make_app
from rshow.log import init_logging

init_logging()

this_dir = Path(__file__).abspath().parent

config = load_yaml_dict(this_dir / "dev_config.yaml")

if config.server == "local":
    from rshow.server.local import handlers

    client_dir = this_dir / "server/local/client"
    data_dir = this_dir / "server/local/data"
    if "work_dir" in config:
        os.chdir(config.work_dir)
    handlers.init_traj_reader(config)

elif config.server == "lounge":
    from rshow.server.lounge import handlers

    client_dir = this_dir / "server/lounge/client"
    data_dir = this_dir / "server/lounge/data"

else:
    raise Exception("no config.server specified")

app = make_app(handlers, client_dir, data_dir)
