import requests
from bs4 import BeautifulSoup

def crawl_douban():
    url = "https://movie.douban.com/top250"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    response = requests.get(url, headers=headers)
    print("状态码：", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")

    movie_list = soup.find_all("div", class_="item")

    print(f"一共找到 {len(movie_list)} 部电影。\n")

    for movie in movie_list:
        title = movie.find("span", class_="title").text

        rating = movie.find("span", class_="rating_num").text

        quote_p = movie.find("p", class_="quote")

        if quote_p:
            quote = quote_p.text.strip()
        else:
            quote = "暂无引言"

        print(f"《{title}》/ 评分：{rating} / 引言：{quote}")

if __name__ == "__main__":
    crawl_douban()