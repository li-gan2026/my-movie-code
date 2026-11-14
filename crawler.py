import requests
from bs4 import BeautifulSoup
from models import db, Movie
import time
import schedule
import threading

# 注意：我们让函数接收一个 app 参数
def crawl_movies(app):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    with app.app_context(): # 用传进来的 app
        Movie.query.delete()
        total_saved = 0
        
        for page in range(10):
            start = page * 25 
            url = f"https://movie.douban.com/top250?start={start}"
            print(f"正在抓取第 {page + 1} 页...")
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            movie_list = soup.find_all("div", class_="item")
            
            for movie in movie_list:
                title = movie.find("span", class_="title").text
                rating = movie.find("span", class_="rating_num").text
                quote_p = movie.find("p", class_="quote")
                quote = quote_p.text.strip() if quote_p else "暂无引言"
                
                new_movie = Movie(title=title, rating=float(rating), quote=quote)
                db.session.add(new_movie)
                db.session.commit()
                total_saved += 1
                
            time.sleep(1) 
            
        print(f"后台自动抓取：大功告成！一共保存了 {total_saved} 部电影！")

# 这是一个启动定时器的函数
def start_scheduler(app):
    # 因为 crawl_movies 需要传 app 参数，所以我们要用一个内部函数包一下
    def job():
        crawl_movies(app)
        
    schedule.every(30).seconds.do(job)
    
    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    # 启动后台线程
    threading.Thread(target=run, daemon=True).start()