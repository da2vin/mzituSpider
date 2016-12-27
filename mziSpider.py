#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import requests
from requests.adapters import HTTPAdapter
import gevent
import gevent.monkey
from bs4 import BeautifulSoup as bs
import uuid
import os
import time

gevent.monkey.patch_all()
reload(sys)
sys.setdefaultencoding('utf-8')

headers = dict()
headers[
    "User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"
headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
headers["Accept-Encoding"] = "gzip, deflate, sdch"
headers["Accept-Language"] = "zh-CN,zh;q=0.8"
request_retry = HTTPAdapter(max_retries=3)


def my_get(url):
    session = requests.session()
    session.headers = headers
    session.mount('https://', request_retry)
    session.mount('http://', request_retry)
    return session.get(url)


def main():
    start_url = "http://www.mzitu.com/xinggan"
    soup = bs(my_get(start_url).content, "lxml")
    total_page = int(soup.select_one("a.next.page-numbers").find_previous_sibling().text)
    for page in range(1, total_page + 1):
        get_page_content(page)


def get_page_content(page):
    href = "http://www.mzitu.com/xinggan/page/" + str(page)
    soup = bs(my_get(href).content, "lxml")
    li_list = soup.select("div.postlist ul#pins li")
    for li in li_list:
        get_pic(li.select_one("a").attrs["href"])


def get_pic(url):
    response = my_get(url)
    i = 0
    while "400" in bs(response.content, "lxml").title or response.status_code == 404 or response.status_code == 400:
        i += 1
        if i > 5:
            return
        time.sleep(0.8)
        response = my_get(url)
    li_soup = bs(response.content, "lxml")
    title = li_soup.title.text.replace(' ', '-')
    if li_soup.find(lambda tag: tag.name == 'a' and '下一页»' in tag.text) is None:
        with open("log.txt", "a") as fs:
            fs.write(url + "\r\n")
            fs.write(str(response.status_code) + "\r\n")
            fs.write(response.content + "\r\n")
        print "error" + url
    else:
        total_page = int(li_soup.find(lambda tag: tag.name == 'a' and '下一页»' in tag.text) \
                         .find_previous_sibling().text)
        tasks = [gevent.spawn(download_pic, url + "/" + str(page), title, ) for page in range(1, total_page + 1)]
        gevent.joinall(tasks)


def download_pic(url, title):
    response = my_get(url)
    href = bs(response.content, "lxml").select_one("div.main-image img").attrs["src"]
    response = my_get(href)
    i = 0
    while "400" in bs(response.content, "lxml").title or response.status_code == 404 or response.status_code == 400:
        i += 1
        if i > 5:
            return
        time.sleep(0.8)
        response = my_get(url)
    if response.status_code == 200:
        if not os.path.exists("img"):
            os.mkdir("img")
        if not os.path.exists("img/" + title):
            os.mkdir("img/" + title)
        with open("img/" + title + "/" + str(uuid.uuid1()) + ".jpg", 'wb') as fs:
            fs.write(response.content)
            print "download success!:" + title


if __name__ == "__main__":
    main()
