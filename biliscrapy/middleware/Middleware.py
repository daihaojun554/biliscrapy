from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from ..models import Card
from django.utils.deprecation import MiddlewareMixin


class MyCardMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        card_code = request.META.get('HTTP_CARD_CODE')  # 从请求头获取卡密参数
        #
        path = request.path  # 获取请求路径
        print(path)
        # 如果请求头中包含卡密参数
        if card_code:
            try:
                card = Card.objects.get(card_code=card_code)
            except Card.DoesNotExist:
                return redirect(reverse('invalid_card'))

            current_datetime = timezone.now()

            # 检查卡密是否过期
            if card.expiration_date < current_datetime:
                return redirect(reverse('expired_card'))

            # 更新卡密的最后一次使用地址和时间
            card.last_used_address = request.META.get('REMOTE_ADDR')
            card.save()

            # 将卡密对象存储在请求的card属性中，以便后续视图函数使用
            request.card = card
        if path == '/bilibili/enter_card.html' or path.startswith('/admin'):
            #     放过请求
            response = self.get_response(request)
            return response


        # 如果请求中不包含卡密参数，则需要进行卡密验证
        elif not request.session.get('valid_card'):
            return redirect(reverse('enter_card'))

        response = self.get_response(request)
        return response
