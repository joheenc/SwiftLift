from flask import Flask, render_template
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

from app import routes

@app.route('/')
def home():
    user = {'username': 'Miguel'}
    return render_template('index.html', title='Home', user=user)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
