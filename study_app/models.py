from datetime import datetime
from study_app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    topics = db.relationship('Topic', backref='owner', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
        
    def add_experience(self, amount):
        """Add experience to the user and level up if necessary."""
        self.experience += amount
        # Simple leveling formula: level = experience // 100
        new_level = self.experience // 100 + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Indicates level up occurred
        return False

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    documents = db.relationship('Document', backref='topic', lazy=True)
    questions = db.relationship('Question', backref='topic', lazy=True)
    
    def __repr__(self):
        return f'<Topic {self.title}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text)  # Extracted text content from the document
    
    def __repr__(self):
        return f'<Document {self.filename}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.Integer, default=1)  # 1-5 scale
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_responses = db.relationship('UserResponse', backref='question', lazy=True)
    
    def __repr__(self):
        return f'<Question {self.id}>'

class UserResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    response_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    response_time = db.Column(db.Float)  # Time taken to answer in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserResponse {self.id}>'

class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='in-progress')  # in-progress, won, lost
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Battle {self.id}>'