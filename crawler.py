import aiohttp  # 导入异步网络请求库
import time
import asyncio  # 导入异步事件循环库
from models import db, Movie, Tag, movie_tag
from bs4 import BeautifulSoup
import schedule
import threading
from routes import movie_cache

# 1. 定义一个异步函数，专门负责抓取单独一页
async def fetch_page(session, page):
    start = page * 25
    url = f"https://movie.douban.com/top250?start={start}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"🚀 派出快递员去抓第 {page + 1} 页...")
    
    # async with 是异步的上下文管理器，意思是：发请求的这段时间，电脑可以去干别的
    async with session.get(url, headers=headers) as response:
        html = await response.text() # await 就是“等待结果”，把网页源码拿回来
        return html

# 2. 异步主控中心
async def crawl_movies_async(app):
    # 用 aiohttp 建立一个大型的“网络会话”
    async with aiohttp.ClientSession() as session:
        # 创建一个任务列表（把第1页到第10页的任务全部打包）
        tasks = [fetch_page(session, page) for page in range(10)]
        
        # 核心魔法：asyncio.gather 会把所有任务同时发出去，并等待它们全部返回！
        # 返回的 htmls 是一个列表，包含了 10 页的网页源码
        htmls = await asyncio.gather(*tasks)
        
        print("✅ 10 页数据全部下载完毕！准备存入数据库...")

        # 注意：数据库操作依然是同步的，我们需要借用 app 上下文
        with app.app_context():

            db.session.execute(movie_tag.delete())
            
            Movie.query.delete() # 清空旧数据
            movie_cache.clear()
            Tag.query.delete()
            db.session.commit()

            tag_cache = {}

            total_saved = 0
            
            # 遍历拿回来的 10 页源码
            for html in htmls:
                soup = BeautifulSoup(html, "html.parser")
                movie_list = soup.find_all("div", class_="item")
                
                for movie in movie_list:
                    title = movie.find("span", class_="title").text
                    rating = movie.find("span", class_="rating_num").text
                    quote_p = movie.find("p", class_="quote")
                    quote = quote_p.text.strip() if quote_p else "暂无引言"
                    
                    new_movie = Movie(title=title, rating=float(rating), quote=quote)
                    
                    # 👇 全新的智能打标签逻辑 👇
                    
                    # 规则 1：看分数
                    if float(rating) >= 9.5:
                        add_tag_to_movie(new_movie, "高分神作", tag_cache)
                    else:
                        add_tag_to_movie(new_movie, "经典佳作", tag_cache)
                        
                    # 规则 2：看标题里的关键字（假装我们懂分类）
                    if "星际" in title or "太空" in title or "黑客" in title:
                        add_tag_to_movie(new_movie, "科幻大片", tag_cache)
                        
                    if "杀手" in title or "无间" in title:
                        add_tag_to_movie(new_movie, "悬疑犯罪", tag_cache)
                        
                    if "爱" in title or "情" in title:
                        add_tag_to_movie(new_movie, "浪漫爱情", tag_cache)
                        
                    # 规则 3：看经典引言里的关键字
                    if "希望" in quote or "自由" in quote:
                        add_tag_to_movie(new_movie, "治愈励志", tag_cache)

                    # 👆 智能打标签结束 👆

                    db.session.add(new_movie)
                    total_saved += 1
                    
            db.session.commit() # 一次性全部入库
            print(f"🎉 大功告成！一共保存了 {total_saved} 部电影！")

#查标签
def add_tag_to_movie(movie, tag_name, tag_cache):
    #查缓存
    if tag_name in tag_cache:
        tag = tag_cache[tag_name]
    else:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        tag_cache[tag_name] = tag

    if tag not in movie.tags:
        movie.tags.append(tag)


# 3. 给定时器提供一个同步的入口（包裹异步任务）
def job(app):
    # asyncio.run() 就是用来启动异步世界的引擎
    asyncio.run(crawl_movies_async(app))

def start_scheduler(app):
    # 定时器现在调用的是包裹后的 job
    schedule.every(60).seconds.do(job, app) # 改成60秒跑一次，减轻服务器压力
    
    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    threading.Thread(target=run, daemon=True).start()