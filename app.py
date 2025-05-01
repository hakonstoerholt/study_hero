from flask import Flask, render_template
from study_app import create_app

app = Flask(__name__)

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)