import datetime
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

import json

import os

import logging


class bili_utils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler("bilibili.log")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def bv_get(self, bvorurl):
        # https://api.bilibili.com/x/web-interface/view?bvid=BV1uG41197Tf
        # 将bv提取出来
        bv_identifier = "BV"  # BV号的标识符
        if "http://" in bvorurl or "https://" in bvorurl:  # 检查是否是一个URL
            self.logger.info("你输入的是http链接，正在解析...")
            bv_index = bvorurl.find(bv_identifier)
            if bv_index != -1:  # 如果找到了BV号
                bv = bvorurl[bv_index:bv_index + len(bv_identifier) + 10]  # 提取BV号
                self.logger.info(f"BV号为......: {bv}")
                return bv
            else:
                self.logger.info("你输入的链接地址有误！")
                return
        elif bv_identifier in bvorurl:  # 如果输入的是BV号
            self.logger.info("你输入的是BV号，正在解析...")
            bv = bvorurl
            return bv
        else:
            self.logger.info("请输入正确的链接地址或BV号！")
            return

    '''
        av 就是 oid 评论里面的参数
    '''

    def bv2av(self, bv):
        bv2av_url = 'https://api.bilibili.com/x/web-interface/view?bvid='
        if bv.startswith("BV"):
            uurrll = bv2av_url + str(bv)
            js_str = requests.get(uurrll).json()

            if js_str['code'] != 0:
                print("服务器返回错误！请稍后再试！{}".format(js_str))
                return None
            if js_str['data']['aid']:
                avid = js_str['data']['aid']
                self.logger.info(f"找到的avid{avid}")
                return avid
            else:
                return None
        else:
            return None

    '''
    cid 是弹幕用的参数
    '''

    def bv2cid(self, bv):
        url = f"https://api.bilibili.com/x/player/pagelist?bvid={str(bv)}&jsonp=jsonp"
        json_s = requests.get(url).json()
        if json_s['code'] == 0:
            cid = json_s['data'][0]['cid']
            self.logger.info("提取出来的cid是：" + str(cid))
            return cid
        else:
            self.logger.error("服务器返回错误！请稍后再试！")
            return None

    def get_bilibili_cookies(self):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        # 动态获取路径 不用每次都手动输入路径
        # chromedriver.exe 的路径
        # 获取当前脚本的绝对路径
        current_path = os.path.dirname(os.path.abspath(__file__))

        # 构建 chromedriver 的绝对路径
        driver_path = os.path.join(current_path, 'chromedriver.exe')

        # 创建 WebDriver 服务
        service = Service(driver_path)
        # service = Service('./chromedriver.exe')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options, service=service)

        # 打开 Bilibili 网站
        driver.get('https://www.bilibili.com/')
        #

        login_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                                    '#i_cecream > div.bili-feed4 > div.bili-header.large-header > div.bili-header__bar > ul.right-entry > li:nth-child(1) > li > div.right-entry__outside.go-login-btn')))
        login_btn.click()
        # 等待登录完成成
        time.sleep(10)
        driver.get('https://www.bilibili.com/')
        # 在这里，模拟登录流程（需要输入账号和密码）
        # 扫码登录然后，等待完成，完成的条件是屏幕上出现了某个

        search = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#nav-searchform > div.nav-search-btn')))
        search.click()
        time.sleep(3)
        cookies = driver.get_cookies()
        # 获取当前脚本的路径
        current_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_path, 'bilibili_cookies.json'), 'w') as f:
            # 写入当前文件
            f.write(json.dumps(cookies))
        # 写入成功
        print('写入成功', cookies)
        driver.quit()
        return

    def get_info_by_bv(self, bv):
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={str(bv)}"
        js_str = requests.get(url).json()

        if js_str['code'] == 0:
            return js_str['data']
        else:
            return None


if __name__ == '__main__':
    utils = bili_utils()
    # utils.get_bilibili_cookies()
    #
    # with open('./bilibili_cookies.json', 'r') as file:
    #     cookies_data = json.load(file)
    #
    # # 将 cookies 数据转换为字典
    # cookies = {cookie['name']: cookie['value'] for cookie in cookies_data}
    #
    # # 使用 cookies 字典
    # self.logger.info(cookies)
    get = utils.bv_get("BV1uG41197Tf")
    utils.bv2av(get)
