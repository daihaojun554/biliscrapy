import random
import time

import requests

import logging
from .bilibili_utils import bili_utils

import json
import os

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


class Comments:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建文件路径
        file_path = os.path.join(script_dir, 'bilibili_cookies.json')
        if not file_path:
            self.cookies = {}
        with open(file_path, 'r', encoding='utf-8') as file:
            self.cookies_data = json.load(file)
        self.cookies = {cookie['name']: cookie['value'] for cookie in self.cookies_data}
        self.utils = bili_utils()
        self.logger = logging.getLogger('log')

    def extract_comments(self, replies):
        extracted_comments = []
        if not replies:
            return extracted_comments
        for reply in replies:
            extracted_comment = {
                'uname': reply['member']['uname'],
                'current_level': reply['member']['level_info']['current_level'],
                'like': reply['like'],
                'sex': reply['member']['sex'],
                'ctime': reply['ctime'],
                'message': reply['content']['message']
            }
            extracted_comments.append(extracted_comment)

            if 'replies' in reply and reply['replies']:
                nested_replies = self.extract_comments(reply['replies'])
                extracted_comments.extend(nested_replies)

        return extracted_comments

    def get_comments(self, bvorurl):
        self.logger.info("Getting comments for bvorurl:{}".format(bvorurl))
        bv = self.utils.bv_get(bvorurl)
        avid = self.utils.bv2av(bv)
        count = 1
        while avid is None:
            avid = self.utils.bv2av(bv)
            count += 1
            self.logger.info(f"avid is None, retrying...count is {count}")
            time.sleep(3)
        self.logger.info(f"avid===>{avid}")
        comments = []  # 使用列表存储评论

        # 获取评论总数和每页评论数量
        # 计算总页数
        page_num = 1
        page_size = 20

        while True:
            url = f'https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&sort=2&pn={page_num}&ps={page_size}'
            response = requests.get(url, headers=headers, cookies=self.cookies)
            data = response.json()
            if data['code'] != 0:
                break
            # 提取回复信息
            extracted_data = self.extract_comments(data['data']['replies'])

            # 过滤重复的评论
            new_comments = [comment for comment in extracted_data if comment not in comments]
            comments.extend(new_comments)  # 将新的评论添加到列表中
            self.logger.info(f"提取到了{len(new_comments)}条评论，从第 {page_num} 页")
            if len(new_comments) == 0:
                self.logger.info("提取完毕所有评论，共提取到{}条评论！=====>avid{}".format(len(comments), avid))
                break
            # 判断是否有下一页
            total_count = data['data']['page']['count']
            total_pages = (total_count + page_size - 1) // page_size  # 计算总页数
            if page_num >= total_pages:
                self.logger.info("提取完毕所有评论，共提取到{}条评论！=====>avid{}".format(len(comments), avid))
                break

            # 构建下一页的URL
            page_num += 1
            self.logger.info("开始提取第{}页评论".format(page_num))
            time.sleep(random.uniform(0.5, 1.5))
        self.logger.info(f"总共{len(comments)}条评论！")

        # 写入JSON文件
        os.makedirs("./data/comment/", exist_ok=True)  # 创建多层目录
        file_path = f'./data/comment/{avid}_{page_num}-{page_size}_{len(comments)}.json'
        if len(comments) < 2000:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(comments, f, indent=4, ensure_ascii=False)
        return comments

#
# if __name__ == '__main__':
#     comments = Comments().get_comments(
#         "https://www.bilibili.com/video/BV1d94y157SN?spm_id_from=333.1007.tianma.2-1-4.click")
