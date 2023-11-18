import json
from datetime import datetime
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware

from .models import BiliDanmu, BiliComment, BiliVideo, Card
from .network.bilibili_danmu import *
from .network.bilibili_comment import Comments
from .network.bilibili_utils import bili_utils

from django.utils import timezone

import csv

from django.views.decorators.csrf import csrf_exempt

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
            danmaku_count = BiliDanmu.objects.filter(cid=cid).count()
            try:
                # 尝试更新视频的抓取弹幕的状态
                print(bvid)
                video = BiliVideo.objects.get(bvid=bvid)
                video.danmu_fetched = True
                video.danmaku_count = danmaku_count
                video.save()
            except  BiliVideo.DoesNotExist:
                # 如果视频记录不存在，则创建新的视频记录
                info = utils.get_info_by_bv(bvid)
                cid = utils.bv2cid(bvid)

                video = BiliVideo(bvid=bvid,
                                  avid=info['aid'],
                                  oid=cid,
                                  title=info['title'],
                                  author=info['owner']['name'],
                                  tag=info['tname'],
                                  pubdate=make_aware(datetime.fromtimestamp(info['pubdate'])),
                                  pic=info['pic'],
                                  desc=info['desc'],
                                  danmu_fetched=True,
                                  danmaku_count=danmaku_count
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
            bili_comment_count = BiliComment.objects.filter(avid=avid).count()
            try:
                # 尝试更新视频的抓取弹幕的状态
                video = BiliVideo.objects.get(avid=avid)
                video.comment_fetched = True
                video.comment_count = bili_comment_count
                video.save()
            except BiliVideo.DoesNotExist:
                # 如果视频记录不存在，则创建新的视频记录
                info = utils.get_info_by_bv(bv_)
                cid = utils.bv2cid(bv_)
                video = BiliVideo(avid=avid,
                                  bvid=bv_,
                                  oid=cid,
                                  title=info['title'],
                                  author=info['owner']['name'],
                                  tag=info['tname'],
                                  pubdate=make_aware(datetime.fromtimestamp(info['pubdate'])),
                                  pic=info['pic'],
                                  desc=info['desc'],
                                  comment_fetched=True,
                                  comment_count=bili_comment_count
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


def generate_chart(request):
    """
    生成图表
    :param request:
    :return:
    """
    context = {
        'message': 'fail',
        'data': [],
        'code': -1,

    }
    videos = BiliVideo.objects.all().values().order_by('pubdate')
    # 分页
    paginator = Paginator(videos, 6)  # 每页显示10个视频
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    if videos:
        context['message'] = 'success'
        context['data'] = page_obj
        context['code'] = 0

    return render(request, 'generate_chart.html', context)


def enter_card(request):
    if request.method == 'POST':
        card_code = request.POST.get('card_code')
        path = request.path
        try:
            card = Card.objects.get(card_code=card_code)
            current_datetime = make_aware(datetime.now())

            print('过期时间：', card.expiration_date)
            print('当前时间：', current_datetime)
            if card.expiration_date < current_datetime:
                print('卡密已过期')
                request.session['valid_card'] = False
                return render(request, 'enter_card.html',
                              context={'error_message': '卡密已过期!请联系管理员!1842118776@qq.com'})
            card.last_used_address = request.META.get('REMOTE_ADDR')
            card.save()
        except Card.DoesNotExist:
            print("卡密不存在")
            request.session['valid_card'] = False
            request.session['card_code'] = card_code
            return render(request, 'enter_card.html',
                          context={'error_message': '卡密不存在,请联系管理员!1842118776@qq.com'})

        # 将卡密标记为有效，并将卡密信息保存在session中
        request.session['valid_card'] = True
        request.session['card_code'] = card_code
        return render(request, 'danmaku.html')
    #     卡密验证成功，
    return render(request, 'enter_card.html')


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


def export_data(request):
    if request.method == 'POST':
        datas = json.loads(request.body)
        format = datas.get('format')
        cid = datas.get('cid')

        if format == 'json' and cid is not None:
            # 去数据库查询弹幕数据
            danmakus = BiliDanmu.objects.filter(cid=cid).values()
            danmakus_list = list(danmakus)
            json_data = json.dumps(danmakus_list, ensure_ascii=False,cls=DateTimeEncoder)

            # 设置文件名
            filename = f"{cid}_danmaku.json"

            # 创建临时文件
            # 临时文件路径

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_data)

            # 创建 FileResponse 对象
            response = FileResponse(open(filename, 'rb'), as_attachment=True, filename=filename)

            # 删除临时文件
            os.remove(filename)

            return response

    return HttpResponse(status=400)
