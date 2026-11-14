from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user,  login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Movie, User
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 1. 创建蓝图（Blueprint）。这是 Flask 拆分代码的核心！
# 'main' 是蓝图的名字，__name__ 是当前文件的位置
main_bp = Blueprint('main', __name__)

# 2. 注意！以前写 @app.route，现在全部改成 @main_bp.route
@main_bp.route('/')
def index():
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    
    query = Movie.query
    if keyword:
        query = query.filter(Movie.title.like(f'%{keyword}%'))
        
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    return render_template("index.html", movies=pagination.items, pagination=pagination, keyword=keyword)

@main_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_movie():
    if request.method == 'POST':
        title = request.form.get('title')
        rating = request.form.get('rating')
        quote = request.form.get('quote')
        
        new_movie = Movie(title=title, rating=float(rating), quote=quote)
        db.session.add(new_movie)
        db.session.commit()
        return redirect('/')
    return render_template('add.html')

@main_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_movie(id):
    movie = Movie.query.get_or_404(id)
    if request.method == 'POST':
        movie.title = request.form.get('title')
        movie.rating = float(request.form.get('rating'))
        movie.quote = request.form.get('quote')
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', movie=movie)

@main_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_movie(id):
    movie = Movie.query.get_or_404(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect('/')

@main_bp.route('/api/stats')
def get_stats():
    top_count = Movie.query.filter(Movie.rating >= 9.5).count()

    mid_count = Movie.query.filter(Movie.rating >= 9.0, Movie.rating < 9.5).count()

    low_count = Movie.query.filter(Movie.rating < 9.0).count()

    data = {
        "labels": ["9.5分以上", "9.0 ~ 9.4分", "9.0分以下"],
        "values": [top_count, mid_count, low_count]
    }
    return data

# 注册页面
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        
        # 查一下这个名字有没有被注册过
        if User.query.filter_by(username=username).first():
            return "这个用户名已经被注册啦！<a href=' '>返回</a >"
            
        new_user = User(username=username, password=hashed_password) # 简单起见，明文密码存了，真实开发要加密！
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

# 登录页面
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user) # 让管家记住这个人
            return redirect('/')
        else:
            return "账号或密码错误！<a href='/login'>重试</a >"
    return render_template('login.html')

@main_bp.route('/api/ai_review/<int:id>')
def ai_review(id):
    # 1. 去数据库里找这部电影
    movie = Movie.query.get_or_404(id)
    
    # 2. 把我们要发给 AI 的问题准备好
    prompt = f"你是一个资深影评人。请根据电影《{movie.title}》以及它的经典台词『{movie.quote}』，写一段150字以内的精彩影评，要求语言优美、引人入胜。"
    
    # 3. 准备发给智谱 AI 的数据（照着官方文档的格式填）
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    # 把原来写死的 Key，换成从暗格里读
    api_key = os.getenv("ZHIPU_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    data = {
        "model": "glm-4-flash", # 这是免费且极速的模型
        "messages": [{"role": "user", "content": prompt}]
    }
    
    # 4. 向 AI 发起请求
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        # 如果返回的数据里有 error，说明出错了
        if 'error' in result:
            return {"success": False, "review": f"AI 报错: {result['error']['message']}"}
        
    # 如果没报错，正常拿影评
        ai_text = result['choices'][0]['message']['content']
        return {"success": True, "review": ai_text}
    except Exception as e:
        # 加上这一行，把真正的错误打印在终端里！
        print(f"========== AI 报错原因 ==========")
        print(e)
        print(f"=================================")
        return {"success": False, "review": f"AI 报错: {str(e)}"}

# 退出登录
@main_bp.route('/logout')
def logout():
    logout_user() # 管家注销
    return redirect('/login') 