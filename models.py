from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

# 1. 新建一个“中间表”，用来记录电影和标签的对应关系
# 它不需要写成 class，用 db.Table 定义最简单
movie_tag = db.Table('movie_tag',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# 2. 用户表（保持不变）
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# 3. 新建标签表
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True) # 标签名不能重复

# 4. 电影表（注意看最下面新增的 tags 属性）
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)
    quote = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # 👇 核心魔法：告诉 SQLAlchemy，这部电影拥有多个标签。
    # secondary=movie_tag 就是告诉它去查刚才建的那个中间表
    tags = db.relationship('Tag', secondary=movie_tag, backref=db.backref('movies', lazy=True))


def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'my_super_secret_key_123' 
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 15}}
    db.init_app(app)