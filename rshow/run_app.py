from easytrajh5.fs import load_yaml_dict
from path import Path

from rshow.app import make_app, init_logging
from rshow import handlers

init_logging()
config = load_yaml_dict(Path(__file__).parent / "app.yaml")
app = make_app(handlers, config)
