import json
from flask import request
from y_server import app, db
from y_server.modals import Coalitions, Coalition_Opinion, Interests

@app.route("/set_coalition_opinion", methods=["POST"])
def set_coalition_opinion():
    """
    Set the opinion of the coalition
    :return: json response
    """
    data = json.loads(request.get_data())
    coalition = data["coalition"]
    topic_opinions = data["topic_opinions"]
    topic_descriptions = data["topic_descriptions"]

    # Create coalition if it doesn't exist
    coalition_obj = Coalitions.query.filter_by(coalition=coalition).first()
    if not coalition_obj:
        coalition_obj = Coalitions(coalition=coalition)
        db.session.add(coalition_obj)
        db.session.commit()

    # for each topic, set the coalition sentiment
    for topic, score in topic_opinions.items():
        # Create topic if it does not exist
        topic_obj = Interests.query.filter_by(interest=topic).first()
        if not topic_obj:
            topic_obj = Interests(interest=topic)
            db.session.add(topic_obj)
            db.session.commit()

        # Set opinion
        coalition_opinion = Coalition_Opinion(
            coalition_id=coalition_obj.id, 
            interest_id=topic_obj.iid, 
            score=score,
            description=topic_descriptions[topic])
        
        db.session.add(coalition_opinion)
        db.session.commit()

    return json.dumps({"status": 200})


