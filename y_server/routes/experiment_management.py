import os
import shutil
from flask import request
import json
from y_server import app, db
from y_server.modals import (
    Coalition_Opinion,
    Coalitions,
    Emotions,
    User_opinions,
    Post_Sentiment,
    Post_Toxicity,
    User_mgmt,
    Post,
    Reactions,
    Follow,
    Hashtags,
    Post_hashtags,
    Mentions,
    Post_emotions,
    Rounds,
    Recommendations,
    Websites,
    Articles,
    Voting,
    Interests,
    Post_topics,
    User_interest,
    Images,
    Article_topics,
)


@app.route("/change_db", methods=["POST"])
def change_db():
    """
    Change the database to the given name.

    :param db_name: the name of the database
    :return: the status of the change
    """
    # get the data from the request
    data = json.loads(request.get_data())
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:////{data['path']}"

    db.init_app(app)
    return {"status": 200}


@app.route("/shutdown", methods=["POST"])
def shutdown_server():
    """
    Shutdown the server
    """
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    shutdown()


@app.route("/reset", methods=["POST"])
def reset_experiment():
    """
    Reset the experiment.
    Delete all the data from the database.

    :return: the status of the reset
    """
    db.session.query(Post_Sentiment).delete()
    db.session.query(Post_Toxicity).delete()
    db.session.query(Coalition_Opinion).delete()
    db.session.query(Coalitions).delete()
    db.session.query(User_opinions).delete()
    db.session.query(Emotions).delete()
    db.session.query(Post_emotions).delete()
    db.session.query(Post_hashtags).delete()
    db.session.query(Mentions).delete()
    db.session.query(Reactions).delete()
    db.session.query(Follow).delete()
    db.session.query(Post_topics).delete()
    db.session.query(User_interest).delete()
    db.session.query(Voting).delete()
    db.session.query(Recommendations).delete()
    db.session.query(Articles).delete()
    db.session.query(Article_topics).delete()
    db.session.query(Images).delete()
    db.session.query(Websites).delete()
    db.session.query(Interests).delete()
    db.session.query(Rounds).delete()
    db.session.query(Hashtags).delete()
    db.session.query(Post).delete()
    db.session.query(User_mgmt).delete()
    
    db.session.commit()
    return {"status": 200}


@app.route("/save_experiment", methods=["POST"])
def save_experiment():
    """
    Save a copy of the experiment database in the given path.

    :return: the status of the save
    """
    data = json.loads(request.get_data())
    db_tag = data["tag"]

    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    db_base_name = os.path.splitext(os.path.basename(db_uri.split("///")[-1]))[0]

    exp_path = f"experiments/{db_tag}"
    if not os.path.exists(exp_path):
        os.makedirs(exp_path)
    
    shutil.copyfile(f"experiments/{db_base_name}.db", f"{exp_path}/{db_base_name}_{db_tag}.db")
    return {"status": 200}