from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
import shutil
import os
from argparse import ArgumentParser

# Parse arguments
parser = ArgumentParser()
parser.add_argument(
    "-c",
    "--config_file",
    default=f"config_files{os.sep}exp_config.json",
    help="JSON file describing the simulation configuration",
)
args = parser.parse_args()
config_file = args.config_file

try:
    # read the experiment configuration
    config = json.load(open(config_file, "r"))

    # create the experiments folder
    if not os.path.exists(f".{os.sep}experiments"):
        os.mkdir(f".{os.sep}experiments")


    if (
        not os.path.exists(f"experiments{os.sep}{config['name']}.db")
        or config["reset_db"] == "True"
    ):
        # copy the clean database to the experiments folder
        shutil.copyfile(
            f"data_schema{os.sep}database_clean_server.db", f"experiments{os.sep}{config['name']}.db"
        )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "4YrzfpQ4kGXjuP6w"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///../experiments/{config['name']}.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

except: # Y Web subprocess
    # base path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)).split("y_server")[0]

    # create the experiments folder
    if not os.path.exists(f"{BASE_DIR}experiments"):
        os.mkdir(f"{BASE_DIR}experiments")
        shutil.copyfile(
            f"{BASE_DIR}data_schema{os.sep}database_clean_server.db", f"{BASE_DIR}experiments{os.sep}dummy.db"
        )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "4YrzfpQ4kGXjuP6w"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///../experiments/dummy.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

from y_server.routes import *
