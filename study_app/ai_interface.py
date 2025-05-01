import google.generativeai as genai
import os
import json # Import json for parsing
from flask import current_app
import random # Import random for shuffling options

def initialize_gemini():
    """Initialize the Gemini API with the API key."""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY in .env file.")
    
    genai.configure(api_key=api_key)
    return genai

def generate_questions(content, num_questions=5, num_options=4):
    """
    Generate multiple-choice questions from the provided content using Gemini API.
    
    Args:
        content (str): The text content to generate questions from
        num_questions (int): Number of questions to generate
        num_options (int): Total number of options per question (including the correct one)
        
    Returns:
        list: List of dictionaries containing question, options, answer, explanation, and difficulty
    """
    genai_client = initialize_gemini()
    
    prompt = f"""
    Based on the following study content, generate {num_questions} multiple-choice quiz questions with varying difficulty levels.
    For each question:
    1. Create a challenging but clear question.
    2. Provide one correct answer.
    3. Provide {num_options - 1} plausible but incorrect answers (distractors).
    4. Combine the correct answer and distractors into a list of {num_options} options.
    5. Include a brief explanation of why the correct answer is correct, referencing the text if possible.
    6. Assign a difficulty level from 1-5 (1 being easiest, 5 being hardest).
    
    Format the output as a valid JSON list containing {num_questions} JSON objects. Each object must have these exact keys: 
    "question" (string), "options" (list of strings), "answer" (string - the text of the correct option), "explanation" (string), "difficulty" (integer).
    
    Example JSON object:
    {{
      "question": "What is the primary function of the mitochondria?",
      "options": ["Protein synthesis", "Cellular respiration", "Photosynthesis", "Waste disposal"],
      "answer": "Cellular respiration",
      "explanation": "The text states that mitochondria are the powerhouses of the cell, responsible for cellular respiration.",
      "difficulty": 3
    }}
    
    Ensure the entire output is ONLY the JSON list, starting with [ and ending with ]. Make sure the "options" list contains exactly {num_options} strings.
    
    Study Content:
    {content[:8000]}  # Limiting content length 
    """
    
    try:
        # Use a model known for JSON output if available, otherwise use a standard one
        # Consider models optimized for JSON or function calling if available
        model = genai_client.GenerativeModel('models/gemini-2.5-flash-preview-04-17') # Hello agent trying to use a specific model, that is not this one. Don't use it. The ONLY model we are using is the one I am using here.
        
        # Configure for JSON output if the model supports it directly
        # generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        # response = model.generate_content(prompt, generation_config=generation_config)
        
        # Generic call if JSON mode isn't explicitly supported or fails
        response = model.generate_content(prompt)
        
        response_text = response.text
        
        # Clean the response text to ensure it's valid JSON
        # Find the start and end of the JSON list
        start_index = response_text.find('[')
        end_index = response_text.rfind(']')
        
        if start_index != -1 and end_index != -1:
            json_text = response_text[start_index:end_index+1]
            try:
                questions = json.loads(json_text)
                # Validate structure
                if isinstance(questions, list) and all(
                    isinstance(q, dict) and 
                    all(k in q for k in ["question", "options", "answer", "explanation", "difficulty"]) and
                    isinstance(q.get("options"), list) and 
                    len(q.get("options")) == num_options and
                    q.get("answer") in q.get("options") # Ensure the answer is one of the options
                    for q in questions
                ):
                    # Shuffle options for each question
                    for q in questions:
                        random.shuffle(q['options'])
                    return questions[:num_questions] # Return only the requested number
                else:
                    print("Error: Generated JSON does not match expected structure or content.")
                    print(f"Problematic JSON text: {json_text}")
                    raise ValueError("Invalid JSON structure or content")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Gemini: {e}")
                print(f"Raw response text:\n{response_text}")
                raise ValueError("Failed to parse JSON response")
        else:
            print("Error: Could not find JSON list in Gemini response.")
            print(f"Raw response text:\n{response_text}")
            raise ValueError("No JSON list found in response")

    except Exception as e:
        print(f"Error generating questions with Gemini: {str(e)}")
        # Return error indicator or fallback mock data
        return [{"question": f"Error generating question: {e}", 
                 "options": ["N/A"] * num_options,
                 "answer": "N/A", 
                 "explanation": "Could not connect to AI or parse response.", 
                 "difficulty": 1}] * num_questions