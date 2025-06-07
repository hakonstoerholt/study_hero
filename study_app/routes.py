from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify, session
from study_app import db
from study_app.models import User, Topic, Document, Question, Battle, UserResponse, Quest
from study_app.pdf_processor import process_pdf_file
# Removed evaluate_answer import
from study_app.ai_interface import generate_questions
from study_app.game_logic import calculate_xp, update_user_stats, award_xp
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json # Import json for models

# Create a Blueprint for our main routes
main_bp = Blueprint('main', __name__)

# Assume a function to get the current user (replace with actual auth later)
def get_current_user():
    """Gets user with ID 1, creating a default one if it doesn't exist (for testing)."""
    user = db.session.get(User, 1)
    if not user:
        # Create a default user if user 1 doesn't exist
        print("Creating default user with ID 1 for testing.")
        user = User(id=1, username='TestUser', email='test@example.com', level=1, total_xp=0)
        db.session.add(user)
        try:
            db.session.commit()
            print("Default user created successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default user: {e}")
            return None # Return None if creation failed
        # Re-fetch the user after commit to ensure it's attached to the session
        user = db.session.get(User, 1)
    return user

@main_bp.route('/')
def index():
    """Landing page or dashboard if user is logged in."""
    user = get_current_user()
    topics = Topic.query.filter_by(user_id=user.id).all() if user else []
    # Pass user object directly
    return render_template('index.html', user=user, topics=topics)

@main_bp.route('/topic/<int:topic_id>')
def view_topic(topic_id):
    """View a topic's details, documents, and questions."""
    user = get_current_user()
    topic = Topic.query.get_or_404(topic_id)
    # Ensure the topic belongs to the user or handle permissions appropriately
    # if user and topic.user_id != user.id:
    #     flash("You don't have permission to view this topic.", "danger")
    #     return redirect(url_for('main.index'))
    return render_template('topic.html', topic=topic, user=user)

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload_document():
    """Handle document uploads."""
    if request.method == 'POST':
        # Check if a file was submitted
        if 'pdf_file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['pdf_file']
        
        # Check if user submitted an empty form
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Get form data
            topic_id = request.form.get('topic_id')
            if not topic_id:
                # Create a new topic if none exists
                topic_title = request.form.get('topic_title', 'Untitled Topic')
                topic_description = request.form.get('topic_description', '')
                
                # For now using a mock user until auth is implemented
                mock_user_id = 1
                
                new_topic = Topic(
                    title=topic_title,
                    description=topic_description,
                    user_id=mock_user_id
                )
                db.session.add(new_topic)
                db.session.flush()  # Generate ID for new_topic without committing
                topic_id = new_topic.id
            
            # Process the PDF file
            extracted_text = process_pdf_file(file_path)
            
            # Save document to database
            new_document = Document(
                filename=filename,
                file_path=file_path,
                topic_id=topic_id,
                content=extracted_text
            )
            db.session.add(new_document)
            db.session.commit()
            
            # Generate initial questions based on the document
            # Request 4 options per question (1 correct, 3 distractors)
            questions_data = generate_questions(extracted_text, num_questions=5, num_options=4)
            
            # Save questions to database
            for q_data in questions_data:
                # Ensure all required keys are present
                if not all(k in q_data for k in ["question", "options", "answer", "explanation", "difficulty"]):
                    flash(f"Skipping question due to missing data: {q_data.get('question', 'N/A')}", "warning")
                    continue
                    
                new_question = Question(
                    content=q_data['question'],
                    # Use the options_list setter to store options as JSON
                    options_list=q_data['options'], 
                    answer=q_data['answer'],
                    explanation=q_data['explanation'],
                    difficulty=q_data['difficulty'],
                    topic_id=topic_id
                    # xp_value is handled by default in the model
                )
                db.session.add(new_question)

            db.session.commit()

            # Create default quests for the new topic
            training_quest = Quest(
                user_id=mock_user_id,
                title=f"Study {topic_title}",
                description="Answer 5 training questions from this topic",
                target=5,
                quest_type='training',
                reward_xp=50
            )
            battle_quest = Quest(
                user_id=mock_user_id,
                title=f"Defeat the {topic_title} Boss",
                description="Answer 5 battle questions correctly",
                target=5,
                quest_type='battle',
                reward_xp=75
            )
            db.session.add_all([training_quest, battle_quest])
            db.session.commit()

            flash('Document uploaded and processed successfully!')
            return redirect(url_for('main.view_topic', topic_id=topic_id))
    
    # For GET requests, show the upload form
    topics = Topic.query.all()
    return render_template('upload.html', topics=topics)

@main_bp.route('/training/<int:topic_id>')
def training_mode(topic_id):
    """Training mode for a specific topic."""
    user = get_current_user() # Fetch the user
    topic = Topic.query.get_or_404(topic_id)
    questions = Question.query.filter_by(topic_id=topic_id).order_by(Question.difficulty).all()
    # Pass user to the template
    return render_template('training.html', topic=topic, questions=questions, user=user)

@main_bp.route('/battle/<int:topic_id>')
def battle_mode(topic_id):
    """Battle mode for a specific topic."""
    user = get_current_user() # Fetch the user
    if not user:
        flash("Please log in to start a battle.", "warning")
        return redirect(url_for('main.index')) # Or login page
        
    topic = Topic.query.get_or_404(topic_id)
    
    # Create a new battle instance
    # Use the actual user's ID
    new_battle = Battle(
        user_id=user.id, 
        topic_id=topic_id,
        difficulty=1 # Consider using calculate_boss_difficulty(user.level)
    )
    db.session.add(new_battle)
    db.session.commit()
    
    # Store the battle ID in session
    session['battle_id'] = new_battle.id
    
    # Get challenging questions for the battle
    questions = Question.query.filter_by(topic_id=topic_id).order_by(Question.difficulty.desc()).limit(5).all()
    
    # Pass user to the template
    return render_template('battle.html', topic=topic, questions=questions, battle=new_battle, user=user)

@main_bp.route('/answer', methods=['POST'])
def submit_answer():
    """Submit an answer to a question."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not logged in'}), 401
        
    data = request.json
    question_id = data.get('question_id')
    user_answer = data.get('answer') # This will now be the selected option text
    response_time = data.get('response_time')
    
    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Direct comparison for multiple-choice
    is_correct = (user_answer == question.answer)
    explanation = question.explanation # Use the stored explanation
    
    xp_to_add = 0
    if is_correct:
        xp_to_add = question.xp_value

    # Store user's response
    user_response = UserResponse(
        user_id=user.id, # Use logged-in user's ID
        question_id=question_id,
        response_text=user_answer, # Store the selected option text
        is_correct=is_correct,
        response_time=response_time
    )
    db.session.add(user_response)
    
    leveled_up = False
    if is_correct and xp_to_add > 0:
        # Award XP and update level using the helper function
        leveled_up = award_xp(user.id, xp_to_add, db.session) # Use logged-in user's ID
        # REMOVED: flash(f"Correct! +{xp_to_add} XP", 'success')
        if leveled_up:
            # User object in session is already updated by award_xp
            # REMOVED: flash(f"Level Up! You reached Level {user.level}!", 'info')
            pass # Keep structure, but no flash needed here
    elif not is_correct:
        # Provide the correct answer in the feedback for incorrect answers
        # REMOVED: flash(f"Incorrect. The correct answer was: '{question.answer}'. Explanation: {explanation}", 'danger')
        pass # Keep structure, but no flash needed here
    else: # Correct but 0 XP
        # REMOVED: flash("Correct!", 'success')
        pass # Keep structure, but no flash needed here

    # Update battle progress if in battle mode
    battle_id = session.get('battle_id')
    battle_updated_status = None
    
    if battle_id:
        battle = db.session.get(Battle, battle_id)
        # Ensure battle belongs to the current user
        if battle and battle.user_id == user.id:
            battle.score += xp_to_add 
            # Potentially add logic here to end battle if won/lost
            # e.g., if battle.score >= required_score: battle.status = 'won'
            battle_updated_status = battle.status
    
    # Update quest progress for correct answers
    from study_app.game_logic import update_quest_progress
    quests_completed = []
    if is_correct:
        q_type = 'battle' if battle_id else 'training'
        quests_completed = update_quest_progress(user.id, db.session, quest_type=q_type, increment=1)

    # Commit session changes
    db.session.commit()
    
    return jsonify({
        'is_correct': is_correct,
        # Send back the correct answer and explanation regardless
        'correct_answer': question.answer, 
        'explanation': explanation,
        'xp_earned': xp_to_add,
        'battle_status': battle_updated_status,
        'leveled_up': leveled_up,
        # Send back updated user stats for potential UI updates
        'user_level': user.level,
        'user_total_xp': user.total_xp,
        'quests_completed': quests_completed
    })

@main_bp.route('/profile')
def user_profile():
    """User profile page with stats and history."""
    user = get_current_user()
    if not user:
        # If no user (e.g., ID 1 doesn't exist or auth fails), redirect or show error
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('main.index')) # Or a login page
    
    topics = Topic.query.filter_by(user_id=user.id).all()
    battles = Battle.query.filter_by(user_id=user.id).order_by(Battle.started_at.desc()).all()
    
    # Pass user object directly
    return render_template('profile.html', user=user, topics=topics, battles=battles)

@main_bp.route('/topic/<int:topic_id>/delete', methods=['POST'])
def delete_topic(topic_id):
    """Delete a topic and its associated content."""
    user = get_current_user()
    if not user:
        flash("Please log in to delete topics.", "warning")
        return redirect(url_for('main.index')) # Or login page

    topic = db.session.get(Topic, topic_id)

    if not topic:
        flash("Topic not found.", "danger")
        return redirect(url_for('main.index'))

    # Basic authorization check (replace with proper auth later)
    if topic.user_id != user.id:
        flash("You don't have permission to delete this topic.", "danger")
        return redirect(url_for('main.index'))

    try:
        # Delete associated questions first
        Question.query.filter_by(topic_id=topic.id).delete()
        # Delete associated documents (consider deleting files from disk too)
        # Add logic here to delete files from the UPLOAD_FOLDER if needed
        # for doc in topic.documents:
        #     try:
        #         os.remove(doc.file_path)
        #     except OSError as e:
        #         print(f"Error deleting file {doc.file_path}: {e}")
        Document.query.filter_by(topic_id=topic.id).delete()
        # Delete associated battles
        Battle.query.filter_by(topic_id=topic.id).delete()
        # Delete the topic itself
        db.session.delete(topic)
        db.session.commit()
        flash(f"Topic '{topic.title}' and all its content deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting topic: {str(e)}", "danger")
        print(f"Error deleting topic {topic_id}: {e}") # Log the error

    return redirect(url_for('main.index'))


@main_bp.route('/quests')
def view_quests():
    """Display active quests for the current user."""
    user = get_current_user()
    quests = Quest.query.filter_by(user_id=user.id).all() if user else []
    return render_template('quests.html', quests=quests, user=user)
