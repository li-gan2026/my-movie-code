from flask import Flask
from models import db, init_db
from routes import main_bp
# 导入刚才写好的爬虫启动器
from crawler import start_scheduler

app = Flask(__name__)
init_db(app)
app.register_blueprint(main_bp)

# 启动后台定时爬虫
start_scheduler(app)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)