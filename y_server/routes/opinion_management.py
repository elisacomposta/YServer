import json
import numpy as np
from flask import request
from y_server import app, db
from sqlalchemy import desc
from y_server.modals import (
    Interests,
    Coalitions,
    Coalition_Opinion,
    User_mgmt,
    User_opinions
)
from y_server.utils.opinion_dynamics import weighted_mean, median, friedkin_johnsen, weighted_friedkin_johnsen


@app.route("/init_opinions", methods=["POST"])
def init_opinions():
    """
    Initialize the opinions for the user according to the coalition.

    :return: a json object with the status of the initialization
    """
    data = json.loads(request.get_data())
    user_id = int(data["user_id"])
    coalition = data["coalition"]

    coalition_obj = Coalitions.query.filter_by(coalition=coalition).first()
    coalition_opinions = Coalition_Opinion.query.filter_by(coalition_id=coalition_obj.id).all()
    user = User_mgmt.query.filter_by(id=user_id).first()

    for coalition_opinion in coalition_opinions:
        user_opinion = User_opinions(
            score=coalition_opinion.score,
            score_llm=coalition_opinion.score,
            user_id=user_id,
            topic_id=coalition_opinion.interest_id,
            round=user.joined_on,
            description=coalition_opinion.description,
        )

        db.session.add(user_opinion)
        db.session.commit()
        
    return json.dumps({"status": 200})


@app.route("/update_opinion", methods=["POST"])
def update_opinion ():
    """
    Compute the opinion of a user on a topic.
    Available methods:
    - weighted_mean: weighted mean of the scores, with decay factor
    - median: median of the scores
    - friedkin_johnsen: Friedkin-Johnsen model
    - state_dependent_fj: state-dependent Friedkin-Johnsen model
    """
    
    data = json.loads(request.get_data())
    user_id = data["user_id"]
    interests = data["interests"]
    method = data.get("method", "weighted_mean")
    tid = int(data["tid"])
    susceptibility = data.get("susceptibility", 0)
    llm_scores = data.get("llm_scores", [None]*len(interests))
    descriptions = data.get("descriptions", [None]*len(interests))
    decay_factor = 0.8
    
    for i in range(len(interests)):
        topic = Interests.query.filter_by(interest=interests[i]).first()
            
        if method == "weighted_mean":
            score = weighted_mean(user_id, topic, decay_factor=decay_factor)
        
        elif method == "median":
            score = median(user_id, topic)

        elif method == "friedkin_johnsen":
            score = friedkin_johnsen(user_id, topic, susceptibility=susceptibility)

        elif method == "state_dependent_fj":
            score = friedkin_johnsen(user_id, topic, susceptibility=susceptibility, is_state_dependent=True)

        elif method == "weighted_friedkin_johnsen":
            score = weighted_friedkin_johnsen(user_id, topic, susceptibility=susceptibility)

        if llm_scores[i] is None:
            last_opinion = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(desc(User_opinions.round)).first()
            llm_scores[i] = last_opinion.score_llm

        opinion = User_opinions(
            score=round(score, 3),
            score_llm=round(llm_scores[i], 3),
            user_id=user_id,
            topic_id=topic.iid,
            round=tid,
            description=descriptions[i],
        )
        db.session.add(opinion)
        db.session.commit()

    return json.dumps({"status": 200})

@app.route("/get_opinions", methods=["GET"])
def get_opinions():
    """
    Get the opinion of a user on the given topics.

    :return: a json object with the opinions
    """
    data = json.loads(request.get_data())
    user_id = data["user_id"]
    interests = data["interests"]

    res = []

    for interest in interests:
        topic = Interests.query.filter_by(interest=interest).first()
        opinion = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(desc(User_opinions.round)).first()
        if opinion is not None:
            data = {
                "topic": interest,
                "score": opinion.score,
                "score_llm": opinion.score_llm,
                "description": opinion.description,
            }
            res.append(data)

    return json.dumps(res)

@app.route("/get_last_opinion_round", methods=["GET"])
def get_last_opinion_round():
    """
    Get the last round of opinions for a user.

    :return: a json object with the last round of opinions
    """
    data = json.loads(request.get_data())
    user_id = data["user_id"]

    opinion = User_opinions.query.filter_by(user_id=user_id).order_by(desc(User_opinions.round)).first()

    return json.dumps({"round": opinion.round}) if opinion else json.dumps({"round": 0})