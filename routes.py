from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_user, logout_user,  login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Movie, User, Tag
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 1. 创建蓝图（Blueprint）。这是 Flask 拆分代码的核心！
# 'main' 是蓝图的名字，__name__ 是当前文件的位置
main_bp = Blueprint('main', __name__)

movie_cache = {}

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

# 这是一个专门按标签筛选的路由
@main_bp.route('/tag/<string:tag_name>')
def filter_by_tag(tag_name):
    # 1. 先根据网址里的标签名，去 Tag 表里把那个标签找出来
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    
    # 2. 魔法时刻：直接通过 tag.movies 拿到所有关联的电影！
    # 记得吗？我们在 models.py 里写了 backref=db.backref('movies'...)
    movies = tag.movies 
    
    # 3. 把电影数据扔给首页模板去展示
    # 因为 index.html 需要 pagination 对象，为了不报错，我们可以稍微变通一下
    # 这里为了简单，我们就不分页了，直接传入
    return render_template("index.html", movies=movies, pagination=None, keyword="")

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

# 这个接口专门给前端 AJAX 调用的，只返回纯数据，不返回网页
@main_bp.route('/api/movies')
def api_movies():
    keyword = request.args.get('keyword', '')
    tag_name = request.args.get('tag', '')
    page = request.args.get('page', 1, type=int)
    
    # 👇 核心 1：拼接一个唯一的“缓存键名”
    # 比如用户搜了星际，看第2页，键名就是 "keyword:星际|tag:|page:2"
    cache_key = f"keyword:{keyword}|tag:{tag_name}|page:{page}"
    
    # 👇 核心 2：先查记事本里有没有
    if cache_key in movie_cache:
        print(f"🚀 命中缓存！瞬间返回：{cache_key}")
        return jsonify(movie_cache[cache_key])
        
    print(f"🐢 未命中缓存，正在查数据库：{cache_key}")
    # 下面是原来的查数据库逻辑
    query = Movie.query
    if keyword:
        query = query.filter(Movie.title.like(f'%{keyword}%'))
    if tag_name:
        query = query.filter(Movie.tags.any(Tag.name == tag_name))
        
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    
    movie_list = []
    for m in pagination.items:
        movie_list.append({
            "id": m.id,
            "title": m.title,
            "rating": m.rating,
            "quote": m.quote,
            "tags": [t.name for t in m.tags] 
        })
        
    result = {
        "success": True, 
        "data": movie_list,
        "page": pagination.page,         
        "total_pages": pagination.pages, 
        "has_prev": pagination.has_prev, 
        "has_next": pagination.has_next  
    }
    
    # 👇 核心 3：把查出来的结果，抄在记事本上！
    movie_cache[cache_key] = result
    
    return jsonify(result)

# 退出登录
@main_bp.route('/logout')
def logout():
    logout_user() # 管家注销
    return redirect('/login') 