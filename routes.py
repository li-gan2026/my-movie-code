from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user,  login_required, current_user
from models import db, Movie, User

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
        
        # 查一下这个名字有没有被注册过
        if User.query.filter_by(username=username).first():
            return "这个用户名已经被注册啦！<a href=' '>返回</a >"
            
        new_user = User(username=username, password=password) # 简单起见，明文密码存了，真实开发要加密！
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
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user) # 让管家记住这个人
            return redirect('/')
        else:
            return "账号或密码错误！<a href='/login'>重试</a >"
    return render_template('login.html')

# 退出登录
@main_bp.route('/logout')
def logout():
    logout_user() # 管家注销
    return redirect('/login') 