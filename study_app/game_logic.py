from study_app import db
import math
from study_app.models import User

def calculate_xp(is_correct, response_time, difficulty):
    """
    Calculate experience points earned based on answer correctness, response time, and question difficulty.
    
    Args:
        is_correct (bool): Whether the user's answer was correct
        response_time (float): Time taken to answer in seconds
        difficulty (int): Question difficulty level (1-5)
        
    Returns:
        int: Experience points earned
    """
    # Base XP based on difficulty
    base_xp = difficulty * 10
    
    if not is_correct:
        # Give some XP even for incorrect answers (for trying)
        return max(1, int(base_xp * 0.1))
    
    # Time factor: faster answers get more XP
    # Reasonable time expectations based on difficulty (in seconds)
    expected_time = 10 + (difficulty * 5)
    
    # Calculate time bonus (1.0 at expected_time, up to 2.0 for very fast answers)
    time_factor = min(2.0, expected_time / max(1, response_time))
    
    # Calculate total XP
    total_xp = int(base_xp * time_factor)
    
    return max(1, total_xp)  # Ensure at least 1 XP is awarded

def update_user_stats(user, xp_earned):
    """
    Update user stats with earned XP and handle level ups.
    
    Args:
        user: User model object
        xp_earned (int): XP to add to the user
        
    Returns:
        bool: Whether the user leveled up
    """
    old_level = user.level
    level_up = user.add_experience(xp_earned)
    db.session.add(user)
    
    return level_up

def calculate_boss_difficulty(user_level, topic_performance=None):
    """
    Calculate the difficulty of a boss battle based on user level and topic performance.
    
    Args:
        user_level (int): The user's current level
        topic_performance (float, optional): Average performance on this topic (0-1)
        
    Returns:
        int: Boss difficulty level (1-5)
    """
    base_difficulty = min(5, max(1, user_level // 3 + 1))
    
    # Adjust based on topic performance if provided
    if topic_performance is not None:
        # Lower performance means easier boss (to not discourage the user)
        performance_adjustment = -int((1 - topic_performance) * 2)
        adjusted_difficulty = base_difficulty + performance_adjustment
        return min(5, max(1, adjusted_difficulty))
    
    return base_difficulty

def check_battle_success(battle):
    """
    Check if a battle has been won based on score and other factors.
    
    Args:
        battle: Battle model object
        
    Returns:
        bool: Whether the battle was successful
    """
    # Basic implementation: Battle is successful if score is at least 50
    if battle.score >= 50:
        battle.status = "won"
        return True
    else:
        battle.status = "lost"
        return False

def get_next_question_difficulty(previous_responses):
    """
    Determine the difficulty of the next question based on previous answers.
    
    Args:
        previous_responses (list): List of previous user responses
        
    Returns:
        int: Recommended difficulty level for next question (1-5)
    """
    if not previous_responses:
        return 1  # Start with easy questions
    
    # Calculate percentage of correct answers
    correct_count = sum(1 for resp in previous_responses if resp.is_correct)
    correct_percentage = correct_count / len(previous_responses)
    
    # Calculate average response time
    avg_time = sum(resp.response_time for resp in previous_responses) / len(previous_responses)
    
    # Calculate average difficulty of previous questions
    avg_difficulty = sum(resp.question.difficulty for resp in previous_responses) / len(previous_responses)
    
    # Determine next difficulty
    if correct_percentage >= 0.8 and avg_time < 15:
        # User is doing well and answering quickly, increase difficulty
        return min(5, math.ceil(avg_difficulty + 1))
    elif correct_percentage <= 0.3:
        # User is struggling, decrease difficulty
        return max(1, math.floor(avg_difficulty - 1))
    else:
        # Keep difficulty roughly the same
        return round(avg_difficulty)

def calculate_combo_bonus(consecutive_correct):
    """
    Calculate XP bonus for consecutive correct answers (combo).
    
    Args:
        consecutive_correct (int): Number of consecutive correct answers
        
    Returns:
        int: Bonus XP for combo
    """
    if consecutive_correct <= 1:
        return 0
    
    # Exponential growth with a cap
    bonus = min(100, int(5 * (consecutive_correct ** 1.5)))
    return bonus

def award_xp(user_id, xp_to_add, db_session):
    """Fetches a user and calls their add_experience method."""
    user = db_session.get(User, user_id) # Use db.session.get for primary key lookup
    if user:
        leveled_up = user.add_experience(xp_to_add)
        # No need to explicitly update level here, add_experience handles it.
        # db_session.add(user) # Usually not needed if user is already in session
        return leveled_up # Return whether a level up occurred
    return False