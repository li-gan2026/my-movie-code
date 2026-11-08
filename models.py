from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin # 导入用户混入类，这是规定

db = SQLAlchemy()

# 1. 新建 User 表（用户表）
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) # 用户名不能重复
    password = db.Column(db.String(100), nullable=False) # 这里存的是加密后的密码

# 2. 修改原来的 Movie 表
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    quote = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 3. 新增：告诉数据库，这部电影属于哪个用户（记录用户ID）
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'my_super_secret_key_123' # 新增：秘钥，用来加密登录状态
    # 给 SQLite 加上超时等待时间，默认 5 秒太短了
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'timeout': 30}
    }
    db.init_app(app)