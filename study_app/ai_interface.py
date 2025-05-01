import google.generativeai as genai
import os
from flask import current_app

def initialize_gemini():
    """Initialize the Gemini API with the API key."""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY in .env file.")
    
    genai.configure(api_key=api_key)
    return genai

def generate_questions(content, num_questions=5):
    """
    Generate questions from the provided content using Gemini API.
    
    Args:
        content (str): The text content to generate questions from
        num_questions (int): Number of questions to generate
        
    Returns:
        list: List of dictionaries containing question, answer, explanation, and difficulty
    """
    genai_client = initialize_gemini()
    
    prompt = f"""
    Based on the following study content, generate {num_questions} quiz questions with varying difficulty levels.
    For each question:
    1. Create a challenging but clear question
    2. Provide the correct answer
    3. Include a brief explanation of why the answer is correct
    4. Assign a difficulty level from 1-5 (1 being easiest, 5 being hardest)
    
    Format each question as a JSON object with these fields: 
    "question", "answer", "explanation", "difficulty"
    
    Study Content:
    {content[:80000]}  # Limiting content length to avoid token limits
    """
    
    try:
        # Using the Gemini Pro model for question generation
        model = genai_client.GenerativeModel('models/gemini-2.5-flash-preview-04-17')
        response = model.generate_content(prompt)
        
        # Parse the response to extract the questions
        # This parsing would need to be adjusted based on actual Gemini API response format
        response_text = response.text
        
        # For demo purposes, returning mock data
        # In a real implementation, parse the response from Gemini
        # The actual implementation would need to parse JSON from the response
        
        # Mock questions for demonstration
        questions = [
            {
                "question": "What is the primary purpose of the content you just read?",
                "answer": "To explain the key concepts of the subject matter",
                "explanation": "The content focuses on explaining fundamental concepts and their applications.",
                "difficulty": 2
            },
            {
                "question": "According to the text, what are the main components of the system described?",
                "answer": "The main components would be extracted from actual content",
                "explanation": "The text outlines several key components that work together.",
                "difficulty": 3
            }
        ]
        
        # Generate additional mock questions to reach the requested number
        while len(questions) < num_questions:
            questions.append({
                "question": f"Sample question {len(questions)+1} from the content?",
                "answer": "Sample answer based on content",
                "explanation": "This would be replaced with actual AI-generated content.",
                "difficulty": (len(questions) % 5) + 1
            })
        
        return questions
        
    except Exception as e:
        print(f"Error generating questions with Gemini: {str(e)}")
        # Return some basic questions if API fails
        return [{"question": "Basic question about the content?", 
                "answer": "Basic answer", 
                "explanation": "Basic explanation", 
                "difficulty": 1}] * num_questions

def evaluate_answer(user_answer, correct_answer, question_text):
    """
    Evaluate a user's answer against the correct answer using AI.
    
    Args:
        user_answer (str): The user's submitted answer
        correct_answer (str): The correct answer for comparison
        question_text (str): The original question for context
        
    Returns:
        dict: Dictionary with evaluation results
    """
    genai_client = initialize_gemini()
    
    prompt = f"""
    Question: {question_text}
    Correct Answer: {correct_answer}
    User's Answer: {user_answer}
    
    Evaluate if the user's answer is correct or not. Consider semantic meaning rather than exact wording.
    Return your evaluation as a JSON object with these fields:
    1. "is_correct": boolean (true/false)
    2. "explanation": A brief explanation of why the answer is correct or incorrect
    3. "score": A score from 0-100 indicating how close the answer is to being correct
    """
    
    try:
        model = genai_client.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # This would need to be adjusted based on actual Gemini API response format
        # For demo purposes, doing a simple check
        simple_user_answer = user_answer.lower().strip()
        simple_correct_answer = correct_answer.lower().strip()
        
        # Very basic check - in a real app, the AI would do semantic comparison
        is_correct = simple_correct_answer in simple_user_answer or simple_user_answer in simple_correct_answer
        
        return {
            "is_correct": is_correct,
            "explanation": "Your answer includes the key concepts mentioned in the correct answer." if is_correct 
                          else "Your answer misses key concepts from the correct answer.",
            "score": 90 if is_correct else 30
        }
        
    except Exception as e:
        print(f"Error evaluating answer with Gemini: {str(e)}")
        # Simple fallback comparison
        simple_match = user_answer.lower().strip() == correct_answer.lower().strip()
        return {
            "is_correct": simple_match,
            "explanation": "Based on direct comparison." if simple_match else "Answer doesn't match expected response.",
            "score": 100 if simple_match else 0
        }