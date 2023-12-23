import time

from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.timezone import make_aware

from .models import BiliDanmu, BiliComment, BiliVideo, Card
from .network.bilibili_danmu import *
from .network.bilibili_comment import Comments
from .network.bilibili_utils import bili_utils
from .network.bilibili_video import Video

from django.utils import timezone

from django.http import JsonResponse, HttpResponse

# Create your views here.
utils = bili_utils()
bili_video = Video()

logger = logging.getLogger('log')
base_url = 'https://www.bilibili.com/video/'


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
            vv = BiliVideo.objects.filter(bvid=bvid).values()
            cid = vv[0]['oid'] if vv else danmu.bv2cid(bv)
            bvid_exists = BiliDanmu.objects.filter(cid=cid).exists()
            if not bvid_exists:
                logger.info("bvid_exists，不存在！！！")
                dates = danmu.get_available_dates(cid)  # 获取视频的所有日期列表
                danmu.down_so_files(cid, dates)  # 下载所有弹ci幕文件
                unique_danmakus = danmu.parse_so_to_json(cid, dates)  # 解析并保存为 JSON 文件
                if unique_danmakus is None:
                    return render(request, 'danmaku.html',
                                  context.update({'message': '解析弹幕失败，请检查BV号是否正确！'}))
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
            print(danmaku_count)
            try:
                logger.info("try.....")
                # 尝试更新视频的抓取弹幕的状态
                logger.info(bvid)
                video = BiliVideo.objects.get(bvid=bvid)
                video.danmu_fetched = True
                video.danmaku_count = danmaku_count
                video.save()
            except  Exception as e:
                logger.error("error~~~~~~~~~")
                logger.error(e)
                # 如果视频记录不存在，则创建新的视频记录
                info = utils.get_info_by_bv(bvid)
                logger.info("info---->{}".format(info))
                if info is None:
                    return render(request, 'danmaku.html', context)
                cid = utils.bv2cid(bvid)
                logger.info(f'{cid}, cid')
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
                logger.info("新视频信息已添加")
            # 查询数据库并返回结果
            # 查询数据库并返回结果
            danmakus = BiliDanmu.objects.filter(cid=cid).values().order_by('ctime')
            paginator = Paginator(danmakus, 15)  # 每页显示10条记录
            page_number = request.POST.get('page') if request.POST.get('page') else 1  # 获取页码参数
            page_obj = paginator.get_page(page_number)  # 获取对应页码的数据
            print(paginator.count)
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
            'message': '请输入正确的链接地址或BV号！',
            'cid': ''
        }
        c = Comments()
        bv_ = utils.bv_get(bv) if bv.startswith("https://www.bilibili.com/video/BV") or bv.startswith(
            "BV") or bv.startswith("bv") else bv
        logger.info(f'bv_====>{bv_}')
        vv = BiliVideo.objects.filter(bvid=bv_).values()
        # logger.info(vv[0]['avid'], 'sadjkaskjadssajasjdsjkaaashhakads')
        av = utils.bv2av(bv_)
        av_count = 1
        while av is None:
            logger.info(f"av is None, retrying...{av_count}")
            av_count += 1
            av = utils.bv2av(bv_)
        avid = vv[0]['avid'] if vv else av
        logger.info(f"avid=====>{avid}")
        if avid is None:
            context = {
                'result': 'error',
                'data': [],
                'message': 'b站服务器返回错误，请重新尝试'
            }
            return render(request, 'comment.html', context)
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
            if info is None:
                return render(request, 'comment.html', context)
            cid = utils.bv2cid(bv_)
            # 如果cid 为空的话就一直重新尝试获取cid
            cid_count = 1
            while cid is None:
                cid = utils.bv2cid(bv_)
                logger.info(f'{cid}, cid,尝试了{cid_count}次')
                cid_count += 1
                time.sleep(3)
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
    keyword = request.POST.get("keyword")
    print(keyword)
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

    # 分页 # 每页显示6个视频
    paginator = Paginator(videos, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    if videos:
        context['message'] = 'success'
        context['data'] = page_obj
        context['code'] = 0

    return render(request, 'generate_chart.html', context)


def download_video(request):
    context = {}
    if request.method == 'POST':
        bvid = request.POST.get('bvid')
        print(bvid)
        if not utils.check_url(bvid):
            context['message'] = 'url 不合法！'
            context['code'] = -1
            return render(request, 'download_video.html', context)
        url = base_url + bvid
        info = bili_video.get_video_info(url)
        if not info:
            context['message'] = '获取视频信息失败！'
            context['code'] = -1
        data = json.loads(info)
        video_name = data[1]['videoData']['title']
        v_urls = [i['baseUrl'] for i in data[0]['data']['dash']['video']]
        a_urls = [i['baseUrl'] for i in data[0]['data']['dash']['audio']]
        print(v_urls[0], a_urls[0])
        v_suffix = 'flv'
        a_suffix = 'mp3'

        # 如果已经存在的话不需要合并
        if not os.path.exists(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "network",
                "data",
                "video",
                f"{video_name}.mp4")):
            logger.info(f"开始合并视频和音频")
            bili_video.download_file(v_urls[0], f'{video_name}.{v_suffix}')
            bili_video.download_file(a_urls[0], f'{video_name}.{a_suffix}')
            bili_video.merge_video_audio(f"{video_name}.{v_suffix}", f"{video_name}.{a_suffix}")
        #     返回给前端响应流数据
        logger.info(f"视频数据已存在！")
        with open(
                f'{os.path.join(os.path.dirname(os.path.abspath(__file__)), "network", "data", "video", f"{video_name}.mp4")}',
                'rb') as f:
            response = HttpResponse(f.read(), content_type='video/mp4')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(f"{video_name}.mp4")
            return response
    return render(request, 'download_video.html', context)


def parse_video(request):
    context = {
        'message': 'success',
        'data': [],
        'code': 0
    }
    if request.method == 'POST':
        url = request.POST.get("_bv")
        if not utils.check_url(url):
            context['message'] = 'url 不合法！'
            context['code'] = -1
            return render(request, 'download_video.html', context)

        logger.info(url)
        bv = utils.bv_get(url)
        logger.info(f"bv,--->{bv}")

        info = utils.get_info_by_bv(bv)
        if info is None:
            context.update({"message": "fail", "code": -1})
            return render(request, 'download_video.html', context)
        context.update({"data": info})
    return render(request, 'download_video.html', context)


def enter_card(request):
    if request.method == 'POST':
        card_code = request.POST.get('card_code')
        current_datetime = timezone.now()
        try:
            card = Card.objects.get(card_code=card_code)
            if card.expiration_date < current_datetime:
                # 卡密已过期
                return render(request, 'enter_card.html', context={
                    "error_message": '卡密已过期，请联系管理员！1842118776@qq.com'
                })
            # 判断卡密是否已被使用
            if card.is_used:
                # 卡密已被使用
                return render(request, 'enter_card.html', context={
                    "error_message": '卡密已被使用！'
                })

            # 如果卡密尚未被使用，将其设置为已使用状态
            card.is_used = True
            # 将卡密存储在会话中
            request.session['card_code'] = card_code
            request.session['expiration_date'] = card.expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            # 将卡密的最后使用地址存储在卡密表中
            card.last_used_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
            card.save()
            return redirect('parse_danmaku')  # 跳转到弹幕页面或其他需要卡密验证的页面
        except Card.DoesNotExist:
            # 卡密不存在
            return render(request, 'enter_card.html', context={
                "error_message": '卡密不存在，请联系管理员！'
            })

    return render(request, 'enter_card.html')


# 退出当前卡密
def exit_card(request):
    if request.method == 'POST':
        code_ = request.session.get("card_code")
        if not code_:
            return redirect('enter_card')
        try:
            card = Card.objects.get(card_code=code_)
            card.is_used = False
            card.save()
            request.session['card_code'] = None
        except  Card.DoesNotExist:
            pass
    return redirect('enter_card')


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


def export_data(request):
    logger.info(request.method)

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            format_ = data.get('format')
            type = data.get('type')
            if type == 'danmaku':
                print(type, 'sssssssssssssssssss')
                cid = data.get('cid')
                logger.info(f"开始导出,数据,数据类型为，{type}，cid为{cid}")
                if format_ == 'json':
                    # 从数据库中查询弹幕的信息，并且返回给前端，前端去下载一个cid—danmaku.json文件
                    danmakus = BiliDanmu.objects.filter(cid=cid).values()
                    return JsonResponse(list(danmakus), encoder=DateTimeEncoder, safe=False)
                if format_ == 'txt':
                    danmakus = BiliDanmu.objects.filter(cid=cid).values()
                    danmakus = [d['content'] + "," + str(d['ctime']) + "," + d['mode'] + ',' + d['id'] for d in
                                danmakus]
                    return HttpResponse('\n'.join(danmakus))
            if type == 'comment':
                avid = data.get('avid')
                logger.info(f"开始导出数据,数据类型为，{type}，avid{avid}")
                if format_ == 'json':
                    # 从数据库中查询弹幕的信息，并且返回给前端，前端去下载一个avid—comment.json文件
                    comments = BiliComment.objects.filter(avid=avid).values()
                    return JsonResponse(list(comments), encoder=DateTimeEncoder, safe=False)
                if format_ == 'txt':
                    comments = BiliComment.objects.filter(avid=avid).values()
                    comments = [d['uname'] + "," + str(d['current_level']) + "," + str(d['like']) + ',' + d[
                        'sex'] + "," + str(d['ctime']) + "," + d['message'] for d in comments]
                    return HttpResponse('\n'.join(comments))
        except Exception as e:
            logger.error(e)
    return render(request, 'danmaku.html')
