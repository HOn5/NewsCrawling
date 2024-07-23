from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pymysql
import re

class NewsCrawling():
    def __init__(self, url):
        self.url = url
        #계정 정보, db이름
        self.db = pymysql.connect(
            host="localhost",
            user="root",
            password="admin",
            database="news_db",
            charset="utf8mb4"
        )

    def get_urls(self):
        driver = webdriver.Chrome()
        newsUrls = []

        # 웹 페이지 로드
        driver.get(self.url)

        # iframe으로 전환
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))

        #목록 클릭
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn_openlist.pcol2._toggleTopList._returnFalse"))).click()

        #30줄 보기
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="listCountToggle"]'))).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="changeListCount"]/a[5]'))).click()

        #링크 추출 최대 페이지 7
        for page in range(1, 5):
            #첫 페이지의 경우 버튼의 갯수가 하나 적음   
            if page == 1:
                for btn in range(1, 11):
                    try:
                        # 현재 페이지에서 링크 수집 
                        elements = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.pcol2._setTop._setTopListUrl'))
                        )
                        hrefs = [element.get_attribute('href') for element in elements]
                        newsUrls.extend(hrefs)

                        # 다음 페이지 버튼 클릭
                        number = f'//*[@id="toplistWrapper"]/div[2]/div/a[{btn}]'
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, number))
                        )
                        next_button.click()

                        # 페이지 로딩 대기
                        WebDriverWait(driver, 10).until(
                            EC.staleness_of(next_button)
                        )
                    except Exception as e:
                        print(f"Error on page {page}: {e}")
                        continue
            else:
                for btn in range(2, 12):
                    #마지막 페이지일 때 break
                    if page == 6 and btn == 8:
                        break

                    try:
                        # 현재 페이지에서 링크 수집
                        elements = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.pcol2._setTop._setTopListUrl'))
                        )
                        hrefs = [element.get_attribute('href') for element in elements]
                        newsUrls.extend(hrefs)

                        # 다음 페이지 버튼 클릭
                        number = f'//*[@id="toplistWrapper"]/div[2]/div/a[{btn}]'
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, number))
                        )
                        next_button.click()

                        # 페이지 로딩 대기
                        WebDriverWait(driver, 10).until(
                            EC.staleness_of(next_button)
                        )

                    except Exception as e:
                        print(f"Error on page {page}: {e}")
                        continue
        driver.quit()
        return newsUrls
            
    def crawling(self, urls):
        driver = webdriver.Chrome()
        newsTexts = []

        for url in urls:
            driver.get(url)
            
            try:
                # 요소 찾기
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'p.se-text-paragraph.se-text-paragraph-align-'))
                )

                # 각 요소의 텍스트 가져오기
                newsTexts.append([element.text for element in elements])

            except TimeoutException:
                print(f"Elements not found for URL: {url}")

                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'p.se-text-paragraph.se-text-paragraph-align-justify'))
                )

                newsTexts.append([element.text for element in elements])

        driver.quit()

        return newsTexts
    
    def filtering(self, html):
        newsData = []

        for texts in html:
            body = ""
            # 문장에서 제목, 날짜, 방송사 찾기
            pattern = r"\[(.*?)\] (.*?) \((.+)\)$"

            for text in texts:
                # 문장에 별 모양이 있는 경우
                if '\u2605' in text:
                    continue

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
                        "time": time,
                        "body": body
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

            # 중복 확인 쿼리
            select_query = "SELECT COUNT(*) FROM news WHERE title = %s"
            cursor.execute(select_query, (title,))
            result = cursor.fetchone()

            if result[0] == 0:
                # 중복되지 않은 경우 삽입
                sql = "INSERT INTO news (newsroom, title, time, body) VALUES (%s, %s, %s, %s)"
                val = (newsroom, title, time, body)
                cursor.execute(sql, val)
                self.db.commit()

                print(cursor.rowcount, "record inserted")
            else:
                print(f"Duplicate entry found for title: {title}")

        cursor.close()

    def __del__(self):
        self.db.close()

url = 'https://blog.naver.com/sj3589/223507471958'
instance = NewsCrawling(url)
newsUrls = instance.get_urls()
texts = instance.crawling(newsUrls)
data = instance.filtering(texts)
instance.insert(data)