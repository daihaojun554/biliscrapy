import logging
import os
import json
import sys
from datetime import datetime
import requests
from .protobuf import bili_pb2 as Danmaku
from .bilibili_utils import bili_utils

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


# import bili_pb2 as Danmaku

class Danmu:
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
        
       

    def bv2cid(self, bvorurl):
        try:
            bv = self.utils.bv_get(bvorurl)
            cid = self.utils.bv2cid(bv)
            return cid
        except Exception as e:
            self.logger.error(e)
            return None

    # 获取某个 oid 下存在弹幕的日期列表
    def get_available_dates(self, oid, year=None, month=None):
        if not year or not month:
            now = datetime.now()
            year = now.year
            month = now.month
        url = f'https://api.bilibili.com/x/v2/dm/history/index?type=1&oid={oid}&month={year}-{month}'
        response = requests.get(url, cookies=self.cookies, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            self.logger.error("请检查你输入的 oid 号码!!")
            self.logger.error(f"当前请求的 URL 为: {url}")
            return []

    '''
    下载某个视频的弹幕文件
    '''

    def down_so_files(self, oid, dates):
        if dates == None:
            return
        if oid == None:
            self.logger.info("请输入正确的 oid 号码!!")
            return
        if not os.path.exists(os.path.join(self.script_dir, 'data/danmaku')):
            os.mkdir(os.path.join(self.script_dir, 'data/danmaku'))
        elif dates:
            url = f'https://api.bilibili.com/x/v2/dm/web/history/seg.so?type=1&oid={oid}'
            for date in dates:
                url_ = f'{url}&date={date}'
                self.logger.info(f"正在下载 {oid}-{date}.so 文件，请稍后...")
                response = requests.get(url_, cookies=self.cookies, headers=self.headers)
                if response.status_code == 200:
                    with open(os.path.join(self.script_dir, 'data/danmaku/', f'{oid}-{date}.so'), 'wb') as f:
                        f.write(response.content)
                else:
                    self.logger.info("请检查你输入的 oid 号码!!")
                    self.logger.info(f"当前请求的 URL 为: {url}")
                    return
            self.logger.info(f"下载完成！")

    # 将.so文件解析并保存为JSON文件
    def parse_so_to_json(self, oid, dates):
        try:
            if dates == None:
                self.logger.error("日期为空")
                return
            all_danmaku = set()  # 用集合存储所有弹幕数据
            for date in dates:
                file_path = os.path.join(self.script_dir, 'data/danmaku/', f'{oid}-{date}.so')
                with open(file_path, 'rb') as f:
                    data = f.read()

                my_seg = Danmaku.DmSegMobileReply()
                my_seg.ParseFromString(data)

                for item in my_seg.elems:
                    danmaku_dict = {
                        'id': item.id,
                        'progress': item.progress,
                        'mode': item.mode,
                        'fontsize': item.fontsize,
                        'color': item.color,
                        'midHash': item.midHash,
                        'content': item.content,
                        'ctime': item.ctime,
                        'idStr': item.idStr
                        # 添加其他字段以适应 Protobuf 消息结构
                    }

                    # 将字典对象转换为元组，然后添加到集合中进行去重
                    danmaku_tuple = tuple(sorted(danmaku_dict.items()))
                    all_danmaku.add(danmaku_tuple)

            # 将集合中的元组转换回字典对象
            unique_danmaku = [dict(t) for t in all_danmaku]
            self.logger.info(f"找到了 {len(unique_danmaku)} 个唯一的 弹幕 在 {oid}这个视频")
            # 返回一个集合
            # 最后将所有内容写入一个 JSON 文件
            with open(os.path.join(self.script_dir, f'data/danmaku/{oid}_unique_danmaku.json'), 'w',
                      encoding='utf-8') as json_file:
                json.dump(unique_danmaku, json_file, ensure_ascii=False, indent=2)
            # with open(f'./data/danmaku/{oid}_unique_danmaku.json', 'w', encoding='utf-8') as json_file:
            #     json.dump(unique_danmaku, json_file, ensure_ascii=False, indent=2)
            self.logger.info("Done!..........")
            # 所有操作结束后，将so文件删除
            for date in dates:
                os.remove(os.path.join(self.script_dir, f'./data/danmaku/{oid}-{date}.so'))
                self.logger.info(f"{oid}-{date}.so 文件已删除")
                # 返回一个集合
            return unique_danmaku
        except Exception as e:
            self.logger.info(e)
            return []


if __name__ == '__main__':
    # # 调用函数获取特定 oid 下所有日期的弹幕数据
    bv = input("请输入BV号或者是b站视频链接：")
    danmu = Danmu()
    bv = danmu.bv2cid(bv)
    # bv = bv2cid("https://www.bilibili.com/video/BV1q84y1D7X5?spm_id_from=333.1007.tianma.1-1-1.click")
    dates = danmu.get_available_dates(bv)  # 获取视频的所有日期列表
    danmu.down_so_files(bv, dates)  # 下载所有弹幕文件
    danmu.parse_so_to_json(bv, dates)  # 解析并保存为 JSON 文件
