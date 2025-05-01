# Study RPG

Turn studying into an adventure! Study RPG is a web application that gamifies the learning process. Upload your study materials (PDFs), practice with AI-generated questions, test your knowledge in battles, and level up as you learn.

## Features

*   **Upload Study Materials:** Upload PDF documents containing your notes or textbook chapters.
*   **AI-Powered Question Generation:** Automatically generates quiz questions based on the uploaded content using AI (Gemini).
*   **Training Mode:** Practice answering questions related to your study topics.
*   **Battle Mode:** Test your mastery against challenging questions in a battle format.
*   **Leveling System:** Earn Experience Points (XP) for correct answers and completing battles. Level up your profile as you progress.
*   **Track Progress:** View your level, total XP, and study statistics.

## Technology Stack

*   **Backend:** Python, Flask, SQLAlchemy
*   **Frontend:** HTML, CSS (Bootstrap), JavaScript
*   **AI:** Google Gemini API (for question generation and potentially answer evaluation)
*   **Database:** SQLite (default, configurable via environment variable)
*   **PDF Processing:** Uses a PyPDF2 library to extract information from Study Materials.

## Setup and Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd study_rpg
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    *   Create a `.env` file in the project root directory.
    *   Add the following variables:
        ```dotenv
        SECRET_KEY='your_strong_secret_key' # Replace with a real secret key
        DATABASE_URL='sqlite:///instance/study_rpg.db' # Or your preferred database URL
        GEMINI_API_KEY='your_google_gemini_api_key' # Add your Gemini API key
        UPLOAD_FOLDER='uploads' # Optional: Change upload directory
        ```
    *   **Important:** Ensure `.env` is listed in your `.gitignore` file to avoid committing secrets.

5.  **Initialize the database (if using Flask-Migrate or similar):**
    *   Check `app.py` or related files for database migration commands (e.g., `flask db init`, `flask db migrate`, `flask db upgrade`). Run them if necessary. If not using migrations, the database might be created automatically on the first run or require a specific setup step.

## Usage

1.  **Run the Flask application:**
    ```bash
    flask run
    ```
    Or if using a run script (e.g., `run.py`):
    ```bash
    python run.py
    ```
2.  **Access the application:** Open your web browser and navigate to `http://127.0.0.1:5000` (or the address provided by Flask).
3.  **Upload:** Go to the upload section and select a PDF file to create a new study topic.
4.  **Train:** Select a topic and enter Training Mode to practice questions.
5.  **Battle:** Select a topic and enter Battle Mode to test your knowledge under pressure.
6.  **Profile:** Check your profile to see your level and stats.

---

*This README provides a basic overview. You can expand it with more details about specific features, contribution guidelines, or deployment instructions.*
