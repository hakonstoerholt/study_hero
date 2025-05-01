from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify, session
from study_app import db
from study_app.models import User, Topic, Document, Question, Battle, UserResponse
from study_app.pdf_processor import process_pdf_file
from study_app.ai_interface import generate_questions, evaluate_answer
from study_app.game_logic import calculate_xp, update_user_stats
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Create a Blueprint for our main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page or dashboard if user is logged in."""
    # For now, we'll just pass an empty user, this would be replaced with actual auth later
    mock_user = {"username": "Demo User", "level": 5, "experience": 450}
    topics = Topic.query.all()
    return render_template('index.html', user=mock_user, topics=topics)

@main_bp.route('/topic/<int:topic_id>')
def view_topic(topic_id):
    """View a topic's details, documents, and questions."""
    topic = Topic.query.get_or_404(topic_id)
    return render_template('topic.html', topic=topic)

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
            questions = generate_questions(extracted_text, 5)
            
            # Save questions to database
            for q in questions:
                new_question = Question(
                    content=q['question'],
                    answer=q['answer'],
                    explanation=q['explanation'],
                    difficulty=q['difficulty'],
                    topic_id=topic_id
                )
                db.session.add(new_question)
            
            db.session.commit()
            
            flash('Document uploaded and processed successfully!')
            return redirect(url_for('main.view_topic', topic_id=topic_id))
    
    # For GET requests, show the upload form
    topics = Topic.query.all()
    return render_template('upload.html', topics=topics)

@main_bp.route('/training/<int:topic_id>')
def training_mode(topic_id):
    """Training mode for a specific topic."""
    topic = Topic.query.get_or_404(topic_id)
    questions = Question.query.filter_by(topic_id=topic_id).order_by(Question.difficulty).all()
    return render_template('training.html', topic=topic, questions=questions)

@main_bp.route('/battle/<int:topic_id>')
def battle_mode(topic_id):
    """Battle mode for a specific topic."""
    topic = Topic.query.get_or_404(topic_id)
    
    # Create a new battle instance
    mock_user_id = 1  # Replace with actual user ID when auth is implemented
    
    new_battle = Battle(
        user_id=mock_user_id,
        topic_id=topic_id,
        difficulty=1
    )
    db.session.add(new_battle)
    db.session.commit()
    
    # Store the battle ID in session
    session['battle_id'] = new_battle.id
    
    # Get challenging questions for the battle
    questions = Question.query.filter_by(topic_id=topic_id).order_by(Question.difficulty.desc()).limit(5).all()
    
    return render_template('battle.html', topic=topic, questions=questions, battle=new_battle)

@main_bp.route('/answer', methods=['POST'])
def submit_answer():
    """Submit an answer to a question."""
    data = request.json
    question_id = data.get('question_id')
    user_answer = data.get('answer')
    response_time = data.get('response_time')
    
    # Get the question from the database
    question = Question.query.get_or_404(question_id)
    
    # Evaluate the answer using AI
    evaluation = evaluate_answer(user_answer, question.answer, question.content)
    is_correct = evaluation['is_correct']
    explanation = evaluation['explanation']
    
    # Calculate XP based on correctness and response time
    xp_earned = calculate_xp(is_correct, response_time, question.difficulty)
    
    # Store user's response
    mock_user_id = 1  # Replace with actual user ID when auth is implemented
    
    user_response = UserResponse(
        user_id=mock_user_id,
        question_id=question_id,
        response_text=user_answer,
        is_correct=is_correct,
        response_time=response_time
    )
    db.session.add(user_response)
    
    # Update user stats and battle progress if in battle mode
    battle_id = session.get('battle_id')
    battle_updated = None
    
    if battle_id:
        battle = Battle.query.get(battle_id)
        if battle:
            battle.score += xp_earned
            # Update battle status if needed
            battle_updated = battle.status
    
    # Update user stats (level, experience)
    user = User.query.get(mock_user_id)
    if user:
        level_up = update_user_stats(user, xp_earned)
    
    db.session.commit()
    
    return jsonify({
        'is_correct': is_correct,
        'explanation': explanation,
        'xp_earned': xp_earned,
        'battle_status': battle_updated
    })

@main_bp.route('/profile')
def user_profile():
    """User profile page with stats and history."""
    # For now, using a mock user
    mock_user_id = 1
    user = User.query.get(mock_user_id)
    
    if not user:
        # Create a sample user for demo purposes
        user = User(
            id=mock_user_id,
            username="Demo User",
            email="demo@example.com",
            level=5,
            experience=450
        )
        db.session.add(user)
        db.session.commit()
    
    topics = Topic.query.filter_by(user_id=user.id).all()
    battles = Battle.query.filter_by(user_id=user.id).order_by(Battle.started_at.desc()).all()
    
    return render_template('profile.html', user=user, topics=topics, battles=battles)