from flask import Flask
from models import db, init_db, User # 导入 User
from routes import main_bp
from crawler import start_scheduler
from flask_login import LoginManager # 导入登录管家

app = Flask(__name__)
init_db(app)
app.register_blueprint(main_bp)

# 1. 初始化登录管家
login_manager = LoginManager()
login_manager.init_app(app)
# 2. 如果没登录的人想访问保护页面，把他踢到登录页面（我们一会写）
login_manager.login_view = 'main.login' 

# 3. 告诉管家，怎么通过 ID 找回用户
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

start_scheduler(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
         # === 换成下面这两行 ===
        # 直接从数据库引擎底层开启 WAL 模式，避免新版本报错
        from sqlalchemy import text
        db.session.execute(text('PRAGMA journal_mode=WAL;'))
        # ====================
        
    app.run(debug=True, use_reloader=False)