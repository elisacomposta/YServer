import json
from flask import request
from y_server import app, db
from sqlalchemy import desc
from y_server.modals import Post, Post_topics, User_mgmt, Reactions, User_interest, Interests


@app.route("/get_user_id", methods=["GET", "POST"])
def get_user_id():
    """
    Get the user id.

    :return: a json object with the user id
    """
    data = json.loads(request.get_data())
    username = data["username"]

    user = User_mgmt.query.filter_by(username=username).first()
    if user is None:
        return json.dumps({"id": None})

    return json.dumps({"id": user.id})


@app.route("/get_user", methods=["POST"])
def get_user():
    """
    Get user information.

    :return: a json object with the user information
    """
    data = json.loads(request.get_data())
    username = data["username"]
    email = data["email"]

    user = User_mgmt.query.filter_by(username=username, email=email).first()

    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "leaning": user.leaning,
        "age": int(user.age),
        "user_type": user.user_type,
        "password": user.password,
        "ag": user.ag,
        "ne": user.ne,
        "ex": user.ex,
        "co": user.co,
        "oe": user.oe,
        "rec_sys": user.recsys_type,
        "language": user.language,
        "education_level": user.education_level,
        "joined_on": user.joined_on,
        "owner": user.owner,
        "round_actions": user.round_actions,
        "frec_sys": user.frecsys_type,
        "gender": user.gender,
        "nationality": user.nationality,
        "toxicity": user.toxicity,
        "is_page": user.is_page,
        "is_misinfo": user.is_misinfo,
        "susceptibility": user.susceptibility,
    }

    optional_fields = [
        "original_id", "toxicity_post_avg", "toxicity_post_var",
        "toxicity_comment", "activity_post", "activity_comment"
    ]

    for field in optional_fields:
        if hasattr(user, field):
            user_data[field] = getattr(user, field)

    return json.dumps(user_data)


@app.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    :return: a json object with the status of the registration
    """
    data = json.loads(request.get_data())
    user = User_mgmt.query.filter_by(username=data["name"], email=data["email"]).first()
    is_page = 0 if "is_page" not in data else data["is_page"]
    is_misinfo = 0 if "is_misinfo" not in data else data["is_misinfo"]

    if user is None:
        user = User_mgmt(
            username=data["name"],
            email=data["email"],
            password=data["password"],
            leaning=data["leaning"],
            age=int(data["age"]),
            user_type=data["user_type"],
            oe=data["oe"],
            co=data["co"],
            ex=data["ex"],
            ag=data["ag"],
            ne=data["ne"],
            recsys_type="default",
            language=data["language"],
            education_level=data["education_level"],
            joined_on=int(data["joined_on"]),
            round_actions=int(data["round_actions"]),
            owner=data["owner"],
            gender=data["gender"],
            nationality=data["nationality"],
            toxicity=data["toxicity"],
            is_page=is_page,
            original_id=data["original_id"],
            toxicity_post_avg=data["toxicity_post_avg"],
            toxicity_post_var=data["toxicity_post_var"],
            toxicity_comment=data["toxicity_comment"],
            activity_post=data["activity_post"],
            activity_comment=data["activity_comment"],
            is_misinfo=is_misinfo,
            susceptibility=data["susceptibility"],
        )
        db.session.add(user)
        try:
            db.session.commit()
        except:
            return json.dumps({"status": 404})

    return json.dumps({"status": 200})


@app.route("/churn", methods=["POST"])
def churn_agents():
    """
    Churn users that do not post for a while.

    :return:
    """

    data = json.loads(request.get_data())
    n_users = data["n_users"]
    left_on = data["left_on"]

    #  get the max round value from the post table for each user
    query = (db.session.query(Post.user_id, db.func.max(Post.round)).
             join(User_mgmt, Post.user_id == User_mgmt.id).
             filter(User_mgmt.left_on.is_(None), User_mgmt.is_page == 0).
             group_by(Post.user_id)).order_by(db.func.max(Post.round).asc()).limit(n_users)

    results = query.all()

    removed = {}
    for user_id, _ in results:
        user = User_mgmt.query.filter_by(id=user_id).first()
        user.left_on = left_on
        db.session.commit()
        removed[user_id] = None

    return json.dumps({"status": 200, "removed": removed})


@app.route("/update_user", methods=["POST"])
def update_user():
    """
    Update user information.

    :return: a json object with the status of the update
    """
    data = json.loads(request.get_data())

    user = User_mgmt.query.filter_by(
        username=data["username"], email=data["email"]
    ).first()

    if user is not None:
        if "recsys_type" in data:
            recsys_type = data["recsys_type"]
            user.recsys_type = recsys_type
            db.session.commit()

        if "frecsys_type" in data:
            frecsys_type = data["frecsys_type"]
            user.frecsys_type = frecsys_type
            db.session.commit()

    return json.dumps({"status": 200})


@app.route("/user_exists", methods=["POST"])
def user_exists():
    """
    Check if the user exists.

    :return: a json object with the status of the user
    """
    data = json.loads(request.get_data())
    user = User_mgmt.query.filter_by(username=data["name"], email=data["email"]).first()

    if user is None:
        return json.dumps({"status": 404})

    return json.dumps({"status": 200, "id": user.id})


@app.route(
    "/get_user_from_post",
    methods=["POST", "GET"],
)
def get_user_from_post():
    """
    Get the author of a post.

    :return: a json object with the author
    """
    data = json.loads(request.get_data())
    post_id = data["post_id"]
    post = Post.query.filter_by(id=post_id).first()

    return json.dumps(post.user_id)


@app.route("/timeline", methods=["GET"])
def get_timeline():
    """
    Get the timeline of a user.

    :return: a json object with the timeline
    """
    data = json.loads(request.get_data())
    user_id = data["user_id"]

    user = User_mgmt.query.filter_by(id=user_id).first()
    all_posts = Post.query.filter_by(user_id=user.id).order_by(desc(Post.id))
    res = []
    for post in all_posts:
        res.append(
            {
                "post_id": post.id,
                "post": post.tweet,
                "round": post.round,
                "reposts": len(post.retweets),
                "likes": len(list(Reactions.query.filter_by(id=post.id, type="like"))),
                "dislikes": len(
                    list(Reactions.query.filter_by(id=post.id, type="dislike"))
                ),
                "comments": len(list(Post.query.filter_by(comment_to=post.id))),
            }
        )

    return json.dumps(res)


@app.route("/set_interests", methods=["POST"])
def set_interests():
    """
    Set the interests of a user.

    :return: a json object with the status of the update
    """
    data = json.loads(request.get_data())

    for interest in data:
        ints = Interests(
            interest=interest,
        )
        db.session.add(ints)
        db.session.commit()

    return json.dumps({"status": 200})


@app.route("/set_user_interests", methods=["POST"])
def set_user_interests():
    """
    Set the interests of a user.

    :return: a json object with the status of the update
    """
    data = json.loads(request.get_data())
    user_id = data["user_id"]
    interests = data["interests"]
    round_id = data["round"]

    for interest in interests:
        # check if the interest is specified as id or by name
        iid = None
        if isinstance(interest, str):
            try:
                iid = Interests.query.filter_by(interest=interest).first().iid
            except:
                # add interest to the interest table
                ints = Interests(
                    interest=interest,
                )
                db.session.add(ints)
                db.session.commit()
                iid = Interests.query.filter_by(interest=interest).first().iid

        else:
            iid = interest

        user_interest = User_interest(
            user_id=user_id, interest_id=iid, round_id=round_id
        )
        db.session.add(user_interest)
        db.session.commit()

    return json.dumps({"status": 200})


@app.route("/get_user_interests", methods=["GET"])
def get_user_interests():
    """
    Get the interests of a user.

    :return: a json object with the interests
    """
    data = json.loads(request.get_data())
    user_id = int(data["user_id"])
    round_id = int(data["round_id"])
    n_interests = int(data["n_interests"])
    time_window = int(data["time_window"])
    base_rounds = max(0, round_id - time_window)

    # get the top n_interests interests of the user in the time window
    interests = (
        db.session.query(
            User_interest.interest_id,
            Interests.interest,
            db.func.count(User_interest.interest_id).label("count"),
        )
        .join(Interests, User_interest.interest_id == Interests.iid)
        .filter(
            User_interest.user_id == user_id,
            User_interest.round_id >= base_rounds,
            User_interest.round_id <= round_id,
        )
        .group_by(User_interest.interest_id)
        .order_by(db.desc(db.func.count(User_interest.interest_id)))
        .limit(n_interests)
        .all()
    )

    res = []
    for interest in interests:
        res.append({"id": int(interest[0]), "topic": interest.interest})

    return json.dumps(res)

@app.route("/get_active_topics", methods=["GET"])
def get_active_topics():
    """
    Get the active topic names of a user (from posts or reactions) within a time window.

    :return: a json array of topic names
    """
    data = json.loads(request.get_data())
    user_id = int(data["user_id"])
    base_round = int(data["base_round"])
    end_round = int(data["end_round"])

    post_topics = (
        db.session.query(Interests.interest)
        .join(Post_topics, Post_topics.topic_id == Interests.iid)
        .join(Post, Post.id == Post_topics.post_id)
        .filter(
            Post.user_id == user_id,
            Post.round >= base_round,
            Post.round <= end_round,
        )
    )

    reaction_topics = (
        db.session.query(Interests.interest)
        .join(Post_topics, Post_topics.topic_id == Interests.iid)
        .join(Post, Post.id == Post_topics.post_id)
        .join(Reactions, Reactions.post_id == Post.id)
        .filter(
            Reactions.user_id == user_id,
            Reactions.round >= base_round,
            Reactions.round <= end_round,
        )
    )
    all_topic_names = (
        post_topics.union(reaction_topics)
        .distinct()
        .all()
    )
    topic_names = [topic[0] for topic in all_topic_names]
    return json.dumps(topic_names)
