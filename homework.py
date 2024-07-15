from bs4 import BeautifulSoup
import requests
import pymysql
import re

class News():
    def __init__(self, urls):
        self.urls = urls
        self.db = pymysql.connect(
            host="localhost",
            user="root",
            password="admin",
            database="news_db",
            charset="utf8mb4"
        )

    def crawling(self):
        htmlData = []
        for url in self.urls:
            response = requests.get(url)
            state = response.status_code

            if state == 200:
                html = response.content
                soup = BeautifulSoup(html, 'html.parser')
                data = soup.find_all(class_='se-fs-fs16 se-ff-system')
            else:
                print(f"state code: {state}")

            textData = [ele.text.strip() for ele in data]
            htmlData.append(textData)

        return htmlData

    def filtering(self, html):
        newsData = []

        for data in html:
            body = ""
            pattern = r"\[(.*?)\] (.*?) \((.+)\)$"

            data = data[1:]
            for text in data:
                #방송국 기사 제목 시간 추출
                match = re.search(pattern, text)

                if match:
                    newsroom = match.group(1)
                    title = match.group(2)
                    time = match.group(3)
                    continue

                #기사 본문이 끝나면 딕셔너리 저장
                if text.startswith('-') and text.endswith('-'):
                    newsDict = {
                        "newsroom": newsroom,
                        "title": title,
                        "time": time.replace('\xa0', ''),
                        "body": body.replace('\u200b', '').replace('\xa0', '')
                    }

                    newsData.append(newsDict)
                    body = ""
                    continue

                body += text

        return newsData    
    
    def insert(self, data):
        cursor = self.db.cursor()

        for news in data:
            newsroom = news['newsroom']
            title = news['title']
            time = news['time']
            body = news['body']

            sql = "INSERT INTO news (newsroom, title, time, body) VALUES (%s, %s, %s, %s)"
            val = (newsroom, title, time, body)
            cursor.execute(sql, val)
            self.db.commit()

            print(cursor.rowcount, "record inserted")

        cursor.close()

    def __del__(self):
        self.db.close()

urls = [
    'https://m.blog.naver.com/sj3589/223493871016?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223492678657?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223491498303?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223490293304?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223489046341?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223486302765?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223485154010?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223483996594?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223482808543?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223481596458?referrerCode=1',
    'https://m.blog.naver.com/sj3589/223478889065?referrerCode=1'
    ]

instance = News(urls)
elements = instance.crawling()
result = instance.filtering(elements)
instance.insert(result)







//*[@id="toplistWrapper"]/div[2]/div/a[10]1페이지 다음키
//*[@id="toplistWrapper"]/div[2]/div/a[1] 1페이지 2번

//*[@id="toplistWrapper"]/div[2]/div/a[2] 2페이지 12번
//*[@id="toplistWrapper"]/div[2]/div/a[11] 2페이지 다음키

//*[@id="toplistWrapper"]/div[2]/div/a[2] 3페이지 22펀
//*[@id="toplistWrapper"]/div[2]/div/a[11] 3페이지 다음키


