import asyncio

import bilibili_api
from bilibili_api import Credential, comment, sync

import json


async def fetch_comments():
    credential = Credential(
        sessdata="7eb46617%2C1714742319%2C85483%2Ab2CjAqL-7cfp9Mx6q8CxmbvDwoykkGbv4PKMhVwUmYmMQmBS-Ng5ugLidic4Zl-x7rYksSVnBuUXh6Zl9wQlF5M3F3NGZ6bGt3UkxIemNuSWtLUVJMeDJmZERSRF9CWU1aQzFLcld5Z1A1UmFkR3h4Rm5tMEl4SGFCa3hyVDFSa1JNTmV6LV9YcHp3IIEC",
        bili_jct='178e23b7d758383588c7d147ddd160ae', buvid3="FBCE3B93-8693-B99F-CA8E-22D5A30C322112100infoc",
        dedeuserid='82684758')

    comments = await bilibili_api.comment.get_comments(credential=credential, oid=1301272812, page_index=2,
                                                       type_=comment.CommentResourceType.VIDEO)
    print(comments)


# asyncio.run(fetch_comments())

#     "get": {
#       "url": "https://api.bilibili.com/x/v2/reply",
#       "method": "GET",
#       "verify": false,
#       "params": {
#         "pn": "int: 页码",
#         "type": "",
#         "oid": "int: 动态时画册 id 或动态 id",
#         "sort": "int: 排序方式，2 按热度 0 按时间"
#       },
#       "comment": "获取评论，分页模式"
#     },

async def main():
    credential = Credential(
        sessdata="7eb46617%2C1714742319%2C85483%2Ab2CjAqL-7cfp9Mx6q8CxmbvDwoykkGbv4PKMhVwUmYmMQmBS-Ng5ugLidic4Zl-x7rYksSVnBuUXh6Zl9wQlF5M3F3NGZ6bGt3UkxIemNuSWtLUVJMeDJmZERSRF9CWU1aQzFLcld5Z1A1UmFkR3h4Rm5tMEl4SGFCa3hyVDFSa1JNTmV6LV9YcHp3IIEC",
        bili_jct='178e23b7d758383588c7d147ddd160ae',
        buvid3="FBCE3B93-8693-B99F-CA8E-22D5A30C322112100infoc",
        dedeuserid='82684758'
    )
    comments = []
    page = 1
    c = await comment.get_comments(533863954, comment.CommentResourceType.VIDEO, page, credential=credential)
    with open('./data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(c, ensure_ascii=False))
#     oid = 875993519
#     if not c:
#         break
#     count += int(c['page']['size'])
#     if c['replies']:  # 检查c['replies']是否可迭代
#         comments.extend(c['replies'])
#         print(f"已获取 {count} 条评论")
#     if page * int(c['page']['size']) < c['page']['count']:
#         page += 1
#     else:
#         break
# for cmt in comments:
#     # 写入csv文件中去
#     with open(f'comments_{oid}.txt', 'a', encoding='utf-8-sig') as f:
#         f.write(f"{cmt['member']['uname']}-----{cmt['content']['message'].strip().replace(chr(10), '')}\n")
#     print(f"{cmt['member']['uname']}: {cmt['content']['message']}")
# print(f"\n\n共有 {count} 条评论（不含子评论）")


asyncio.run(main())
