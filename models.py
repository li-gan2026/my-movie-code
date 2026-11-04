from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Movie(db.Model):

    id = db.Column(db.Integer, primary_key = True)

    title = db.Column(db.String(200), nullable = False)

    rating = db.Column(db.Float, nullable = False)

    quote = db.Column(db.String(500), nullable = True)

    created_at = db.Column(db.DateTime, default = datetime.now)

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

    app.config['SQlALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)