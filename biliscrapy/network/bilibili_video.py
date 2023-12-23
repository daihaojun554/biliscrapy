import logging
import random

import requests
import re
from .bilibili_utils import bili_utils
import os
import json
from tqdm import tqdm


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

    def get_video_info(self, url: str) -> str:
        """
       从给定的URL中提取视频信息。
       :param url: 要获取信息的视频的URL。
       :return: 返回包含视频信息的JSON字符串，如果URL无效，则返回字符串'invalid url'。
        """
        try:
            isValid = self.utils.check_url(url)
            if not isValid:
                return 'url is invalid'
            resp = requests.get(url, headers=self.headers, cookies=self.cookies)
            cont = re.compile(r".*?window.__playinfo__=(?P<info1>.*?);\(function\(\)", re.S)
            a = cont.search(resp.text, re.S)
            info = a.group('info1').replace("</script><script>window.__INITIAL_STATE__=", ',')
            return f"[{info}]"
        except requests.RequestException as e:
            self.logger.error("Error occurred while getting video info: {}".format(str(e)))
            return ''

    def download_file(self, url, filename):
        """
        下载文件的函数

        参数:
        url (str): 要下载的文件的URL
        filename (str): 下载的文件保存的路径和文件名
        """
        try:
            response = requests.get(url, headers=self.headers, stream=True, cookies=self.cookies)
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 1024
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)
            with open(filename, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    progress_bar.update(len(data))
            progress_bar.close()
            self.logger.info("Downloading file.{}".format(filename))
        except requests.exceptions.RequestException as e:
            self.logger.error("Error occurred while downloading the file: {}".format(str(e)))


    def merge_video_audio(self, video_file, audio_file):
        """
        合并视频和音频文件。

        参数:
            self: 类自身引用。
            video_file: 视频文件路径。
            audio_file: 音频文件路径。
        返回值:
            无
        异常:
            如果视频文件或音频文件不存在，则会打印错误消息并返回。
        注意:
            合并后的文件以视频文件的基础名称和 '.mp4' 扩展名的形式保存。
            原始视频和音频文件在合并成功后会被删除。
        """
        if not os.path.isfile(video_file):
            print(f"Error: {video_file} 不是文件或不存在。")
            return
        if not os.path.isfile(audio_file):
            print(f"Error: {audio_file} 不是文件或不存在。")
            return

        # 合并视频和音频文件
        # 使用ffmpeg命令行工具将视频和音频文件合并为mp4格式文件
        cmd = f"ffmpeg -i {video_file} -i {audio_file} -c:v copy -c:a aac -strict experimental {os.path.splitext(video_file)[0]}.mp4"
        try:
            os.system(cmd)
        except Exception as e:
            print(f"运行 ffmpeg 时发生错误: {e}")
            return

        # 检查合并后的文件是否成功创建
        output_file = os.path.splitext(os.path.basename(video_file))[0] + '.mp4'
        if not os.path.isfile(output_file):
            print("文件合并失败。")
            return

        # 删除原始视频和音频文件
        os.remove(video_file)
        os.remove(audio_file)
        self.logger.info(f"成功合并视频和音频,------->{output_file}")



if __name__ == '__main__':
    v = Video()
    u='https://www.bilibili.com/video/BV1Le411C7LV?spm_id_from=333.1007.tianma.2-2-5.click'
    _bv = v.utils.bv_get(u)
    print(_bv)
    info = v.get_video_info(u)
    if not info:
        print('invalid url')
        exit(0)
    with open('info.json', 'w', encoding='utf-8') as file:
        file.write(info)
    try:
        data = json.loads(info)
    except json.JSONDecodeError as e:
        print(f'Error decoding JSON: {e}')
        exit(0)
    video_name = data[1]['videoData']['title']
    v_urls = [i['baseUrl'] for i in data[0]['data']['dash']['video']]
    a_urls = [i['baseUrl'] for i in data[0]['data']['dash']['audio']]
    print(v_urls[0], a_urls[0])
    v_suffix = 'flv'
    a_suffix = 'mp3'
    v.download_file(v_urls[0], f'{video_name}.{v_suffix}')
    v.download_file(a_urls[0], f'{video_name}.{a_suffix}')

    v.merge_video_audio(f"{video_name}.{v_suffix}", f"{video_name}.{a_suffix}")
