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
headers = {
    'authority': 'message.bilibili.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'origin': 'https://www.bilibili.com',
    'pragma': 'no-cache',
    'referer': 'https://www.bilibili.com/',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
}

class bili_utils:
    def __init__(self):
        self.logger = logging.getLogger('log')
        self.header = headers
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(self.script_dir, 'bilibili_cookies.json')
        with open(file_path, 'r') as file:
            self.cookies_data = json.load(file)
        self.cookies = {cookie['name']: cookie['value'] for cookie in self.cookies_data}

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
            self.logger.info(f"你输入的是BV号{bvorurl}，正在解析...")
            bv = bvorurl
            return bv
        else:
            self.logger.info(f"请输入正确的链接地址或BV号！,{bvorurl}")
            return "BV1111111111"

    '''
        av 就是 oid 评论里面的参数
    '''

    def bv2av(self, bv):
        bv2av_url = 'https://api.bilibili.com/x/web-interface/view?bvid='
        if bv.startswith("BV"):
            url = bv2av_url + str(bv)
            retry_count = 0
            max_retries = 10
            retry_delay = 1  # seconds
            while retry_count < max_retries:
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # 检查请求是否成功
                    data = response.json()
                    if 'data' in data and 'aid' in data['data']:
                        avid = data['data']['aid']
                        self.logger.info(f"找到的avid{avid}")
                        return avid
                    else:
                        self.logger.info("未找到有效的aid值，正在重新尝试获取...")
                        retry_count += 1
                        time.sleep(retry_delay)
                except (requests.RequestException, ValueError) as e:
                    self.logger.info(f"请求发生错误：{e}")
                    retry_count += 1
                    self.logger.info("服务器返回错误！请稍后再试！")
                    self.logger.info(f"正在重新尝试获取aid，尝试次数==>{retry_count}")
                    time.sleep(retry_delay)

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
            return self.bv2cid(bv)

    def get_bilibili_cookies(self):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
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
        self.logger.info('写入成功{}'.format(cookies))
        driver.quit()
        return

    def get_info_by_bv(self, bv):
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={str(bv)}"
        js_str = requests.get(url,headers=self.header,cookies=self.cookies).json()
        retry_count = 1
        while js_str['code']!=0:
            js_str = requests.get(url,headers=self.header,cookies=self.cookies).json()
            retry_count+=1
            self.logger.info(f"服务器返回错误！请稍后再试！,{retry_count}")
            return js_str['data']
            
            
        


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
