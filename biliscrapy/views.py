from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.timezone import make_aware

from .models import BiliDanmu, BiliComment, Video
from .network.bilibili_danmu import *
from .network.bilibili_comment import Comments
from .network.bilibili_utils import bili_utils

# Create your views here.
utils = bili_utils()


def danmaku(request):
    if request.method == 'POST':
        bv = request.POST.get('bv')  # 获取用户输入的 BV 号或链接
        bvid = utils.bv_get(bv)
        url = bv
        context = {
            'result': 'error',
            'data': [],
            'message': '请输入正确的链接地址或BV号！'
        }
        if bv.startswith("https://www.bilibili.com/video/BV") or bv.startswith("BV") or bv.startswith("bv"):
            danmu = Danmu()
            cid = danmu.bv2cid(bv)
            bvid_exists = BiliDanmu.objects.filter(cid=cid).exists()
            if not bvid_exists:
                dates = danmu.get_available_dates(cid)  # 获取视频的所有日期列表
                danmu.down_so_files(cid, dates)  # 下载所有弹ci幕文件
                unique_danmakus = danmu.parse_so_to_json(cid, dates)  # 解析并保存为 JSON 文件
                danmu_objects = [
                    BiliDanmu(
                        id=danmaku['id'],
                        cid=cid,
                        content=danmaku['content'],
                        color=danmaku['color'],
                        fontsize=danmaku['fontsize'],
                        midHash=danmaku['midHash'],
                        mode=danmaku['mode'],
                        progress=danmaku['progress'],
                        ctime=make_aware(datetime.fromtimestamp(danmaku['ctime']))
                    )
                    for danmaku in unique_danmakus
                ]
                BiliDanmu.objects.bulk_create(danmu_objects)
            #     不存在 弹幕信息
            try:
                # 尝试更新视频的抓取弹幕的状态
                print(bvid)
                video = Video.objects.get(bvid=bvid)
                video.danmu_fetched = True
            except  Video.DoesNotExist:
                # 如果视频记录不存在，则创建新的视频记录
                info = utils.get_info_by_bv(bvid)
                cid = utils.bv2cid(bvid)
                video = Video(bvid=bvid,
                              avid=info['aid'],
                              oid=cid,
                              title=info['title'],
                              author=info['owner']['name'],
                              tag=info['tname'],
                              pubdate=make_aware(datetime.fromtimestamp(info['pubdate'])),
                              pic=info['pic'],
                              desc=info['desc'],
                              danmu_fetched=True,
                              )  # 设置弹幕抓取状态
                video.save()
                print("新视频信息已添加")
            # 查询数据库并返回结果
            # 查询数据库并返回结果
            danmakus = BiliDanmu.objects.filter(cid=cid).values().order_by('ctime')
            paginator = Paginator(danmakus, 15)  # 每页显示10条记录
            page_number = request.POST.get('page') if request.POST.get('page') else 1  # 获取页码参数
            page_obj = paginator.get_page(page_number)  # 获取对应页码的数据
            context = {
                "url": url,
                'result': 'error',
                'bvid': bv,
                'total': paginator.count,
                'data': page_obj,
                'new_request': not bvid_exists,
            }
            if len(danmakus) > 0:
                context['result'] = 'success'
        return render(request, 'danmaku.html', context)
    return render(request, 'danmaku.html')


def comment(request):
    if request.method == 'POST':
        bv = request.POST.get('bv')  # 获取用户输入的 BV 号或链接
        url = bv
        context = {
            'result': 'error',
            'data': [],
            'message': '请输入正确的链接地址或BV号！'
        }
        c = Comments()
        bv_ = utils.bv_get(bv) if bv.startswith("https://www.bilibili.com/video/BV") or bv.startswith(
            "BV") or bv.startswith("bv") else bv
        avid = utils.bv2av(bv_)
        print(avid)
        if avid:
            comments_exist = BiliComment.objects.filter(avid=avid).exists()
            if not comments_exist:
                comments = c.get_comments(bv)
                comment_obj = [BiliComment(
                    avid=avid,
                    uname=cmt['uname'],
                    current_level=cmt['current_level'],
                    like=cmt['like'],
                    sex=cmt['sex'],
                    ctime=make_aware(datetime.fromtimestamp(cmt['ctime'])),
                    message=cmt['message']
                ) for cmt in comments]
                BiliComment.objects.bulk_create(comment_obj)
            try:
                # 尝试更新视频的抓取弹幕的状态
                video = Video.objects.get(avid=avid)
                video.comment_fetched = True
                video.save()
            except Video.DoesNotExist:
                # 如果视频记录不存在，则创建新的视频记录
                info = utils.get_info_by_bv(bv_)
                cid = utils.bv2cid(bv_)
                video = Video(avid=avid,
                              bvid=bv_,
                              oid=cid,
                              title=info['title'],
                              author=info['owner']['name'],
                              tag=info['tname'],
                              pubdate=make_aware(datetime.fromtimestamp(info['pubdate'])),
                              pic=info['pic'],
                              desc=info['desc'],
                              comment_fetched=True,
                              )  # 设置弹幕抓取状态
                video.save()
            comments = BiliComment.objects.filter(avid=avid).values().order_by('ctime')
            paginator = Paginator(comments, 15)
            page_number = request.POST.get('page', 1)
            page_obj = paginator.get_page(page_number)
            context = {
                "url": url,
                'result': 'success',
                'bvid': bv,
                'total': paginator.count,
                'data': page_obj,
                "new_request": not comments_exist,
            }
        return render(request, 'comment.html', context)
    return render(request, 'comment.html')


def reflash_cookie(request):
    """
    刷新cookie
    :param request:
    :return:
    """
    utils.get_bilibili_cookies()
    return render(request, 'danmaku.html')
