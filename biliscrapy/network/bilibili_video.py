import logging
import random

import requests
import re
from bilibili_utils import bili_utils
import os
import json
from tqdm import tqdm
import ffmpeg

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


class Video:
    def __init__(self):
        self.utils = bili_utils()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建文件路径
        file_path = os.path.join(self.script_dir, 'bilibili_cookies.json')
        if not file_path:
            self.cookies = {}
        with open(file_path, 'r') as file:
            self.cookies_data = json.load(file)
        self.cookies = {cookie['name']: cookie['value'] for cookie in self.cookies_data}
        self.headers = headers
        self.logger = logging.getLogger('log')

    def get_video_info(self, url) -> str:
        resp = requests.get(url, headers=self.headers, cookies=self.cookies)
        cont = re.compile(r".*?window.__playinfo__=(?P<info1>.*?);\(function\(\)", re.S)
        a = cont.search(resp.text, re.S)
        return '[' + a.group('info1').replace("</script><script>window.__INITIAL_STATE__=", ',') + ']'


if __name__ == '__main__':
    v = Video()
    u = "https://www.bilibili.com/video/BV19g4y1C7ZU?spm_id_from=333.1007.tianma.1-3-3.click"
    _bv = v.utils.bv_get(u)
    print(_bv)
    info = v.get_video_info(u)
    with open('info.json', 'w', encoding='utf-8') as file:
        file.write(info)
    data = json.loads(info)
    video_name = data[1]['videoData']['title']
    v_urls = [i['baseUrl'] for i in data[0]['data']['dash']['video']]
    a_urls = [i['baseUrl'] for i in data[0]['data']['dash']['audio']]
    print(v_urls[0], a_urls[0])

    vresp = requests.get(v_urls[0], headers=headers, cookies=v.cookies)
    v_suffix = 'flv'
    aresp = requests.get(a_urls[0], headers=headers, cookies=v.cookies)
    a_suffix = "mp3"
    a_content_size = int(aresp.headers['content-length'])
    a_parbar = tqdm(total=a_content_size, unit_scale=True, unit='B')
    with open(f'{video_name}_audio.{a_suffix}', 'wb') as af:
        for check in aresp.iter_content(1024):
            if check:
                af.write(check)
                a_parbar.update(len(check))

    # # 获取content的大小
    content_size = int(vresp.headers['Content-Length'])
    # print(content_size)
    # 创建进度条对象
    v_pbar = tqdm(total=content_size, unit='B', unit_scale=True)
    with open(f'{video_name}.{v_suffix}', 'wb') as f:
        for chunk in vresp.iter_content(1024):
            if chunk:
                f.write(chunk)
                v_pbar.update(len(chunk))

    command = f"ffmpeg -i {video_name}.{v_suffix} -i {video_name}_audio.{a_suffix} -c:v copy -c:a aac -strict experimental {video_name}.mp4"
    os.system(command)
    # 等待系统执行完毕
    os.remove(f'{video_name}_audio.{a_suffix}')
    os.remove(f'{video_name}.{v_suffix}')
