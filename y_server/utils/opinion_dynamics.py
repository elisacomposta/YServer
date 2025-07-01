from sqlalchemy import desc
from sqlalchemy import func, and_
from y_server.modals import User_opinions, Follow, Reactions, Post_topics, Post
from y_server import db
import numpy as np
from collections import defaultdict

ACTION_WEIGHT = {
    "like": 0.2,
    "dislike": -0.2,
    "follow": 1.0,
}

def weighted_mean(user_id, topic, decay_factor=0.8):  
    opinions = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(desc(User_opinions.id)).all()
    scores = [o.score for o in opinions]

    weighted_sum, total_weight = 0, 0
    weight = 1.0
    
    for s in scores:
        weighted_sum += s * weight
        total_weight += weight
        weight *= decay_factor
    
    return weighted_sum / total_weight if total_weight > 0 else 0


def median(user_id, topic):
    opinions = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(desc(User_opinions.id)).all()
    return np.median([o.score for o in opinions])


def friedkin_johnsen(user_id, topic, tid, susceptibility=0, is_state_dependent=False):    
    """
    Compute the opinion of a user on a topic using the Friedkin-Johnsen model.

    The Friedkin-Johnsen model is defined as:
        x_i(t+1) = (1 - λ) * x_i(0) + λ * Σ x_j(t) / N

    State-dependent version:
        x_i(t+1) = (1 - λ) * x_i(t) + λ * Σ x_j(t) / N

    where:
        - λ is the susceptibility of the user to peer influence
        - x_i(0) is the user's initial opinion
        - x_i(t) is the user's current opinion
        - Σ x_j(t) / N is the average opinion of the user's peers
    """
    # Get user's opinion
    initial_opinion = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid, round=0).first().score
    current_opinion = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(User_opinions.round.desc()).first().score
    persistent_opinion = current_opinion if is_state_dependent else initial_opinion

    # Get the following user IDs
    touched_users = (db.session.query(Follow.follower_id).filter(Follow.user_id == user_id).distinct().all())
    following_ids = []
    for (follower_id,) in touched_users:
        last_action = (Follow.query.filter_by(user_id=user_id, follower_id=follower_id).order_by(Follow.round.desc()).first())
        if last_action and last_action.action == "follow":
            following_ids.append(follower_id)

    # Get latest opinions of peers 
    peer_opinions = []
    for fid in following_ids:
        latest_opinion = User_opinions.query.filter_by(user_id=fid, topic_id=topic.iid).order_by(User_opinions.round.desc()).first()
        peer_opinions.append(latest_opinion.score)
    
    if len(peer_opinions) == 0:
        return current_opinion  # No influence: return current opinion
    
    peer_avg_opinion = np.mean(peer_opinions)

    return (1 - susceptibility) * persistent_opinion + susceptibility * peer_avg_opinion

def weighted_friedkin_johnsen(user_id, topic, susceptibility=0):
    """
    Compute the opinion of a user on a specific topic using the Friedkin-Johnsen model with weighted opinions.

    The Friedkin-Johnsen model is defined as:
        x_i(t+1) = (1 - λ) * x_i(0) + λ * Σ w_j * x_j(t) / Σ w_j
    """

    # Get user's persistent opinion (x_i(0))
    user_opinion_entry = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(User_opinions.round.desc()).first()
    persistent_opinion = user_opinion_entry.score if user_opinion_entry else 0.5  # Default if missing

    # Get neighbors' weights for this topic
    weights = compute_neighbor_weights(user_id, topic)

    # Get latest opinions of peers and compute the weighted sum
    weighted_sum = 0.0
    for neighbor_id, w in weights.items():
        neighbor_opinion = User_opinions.query.filter_by(user_id=neighbor_id, topic_id=topic.iid).order_by(User_opinions.round.desc()).first()
        if neighbor_opinion:
            weighted_sum += w * neighbor_opinion.score

    # Compute final opinion
    total_weight = sum(weights.values())
    if total_weight == 0:
        return persistent_opinion

    return (1 - susceptibility) * persistent_opinion + susceptibility * (weighted_sum / total_weight)

def compute_neighbor_weights(user_id, topic):
    """
    Compute the weights of the neighbors for a user on a specific topic.
    
    Returns:
        dict[neighbor_id] = weight
    """
    # Get the user's last opinion update
    user_last_opinion = User_opinions.query.filter_by(user_id=user_id, topic_id=topic.iid).order_by(desc(User_opinions.round)).first()
    last_tid = user_last_opinion.round if user_last_opinion else -1
    
    # Get the following user IDs
    touched_users = (db.session.query(Follow.follower_id).filter(Follow.user_id == user_id).distinct().all())
    following_ids = []
    for (follower_id,) in touched_users:
        last_action = (Follow.query.filter_by(user_id=user_id, follower_id=follower_id).order_by(Follow.round.desc()).first())
        if last_action and last_action.action == "follow":
            following_ids.append(follower_id)

    # Initialize weights
    weights = defaultdict(float)

    # Add weights for following users
    for fid in following_ids:
        weights[fid] += ACTION_WEIGHT["follow"]

    # Add weights for reactions
    reactions = (
        db.session.query(Reactions, Post.user_id)
        .join(Post_topics, Reactions.post_id == Post_topics.post_id)
        .join(Post, Reactions.post_id == Post.id)
        .filter(
            Reactions.user_id == user_id,
            Reactions.round > last_tid,
            Post_topics.topic_id == topic.iid
        )
        .all()
    )

    for reaction, neighbor_id in reactions:
        weights[neighbor_id] += ACTION_WEIGHT[reaction.type]

    return dict(weights)
