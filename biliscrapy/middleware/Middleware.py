from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from ..models import Card
from django.utils.deprecation import MiddlewareMixin


class MyCardMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exclude_paths = ['/bilibili/enter_card.html', '/admin', '/bilibili/enter_card']
        # 检查当前请求的路径是否在排除列表之外
        if not any(request.path.startswith(path) for path in exclude_paths):
            card_code = request.session.get('card_code')
            # 检查会话中是否存在卡密
            if not card_code:
                # 若卡密不存在，重定向到卡密验证页面
                return redirect('enter_card')
            try:
                card = Card.objects.get(card_code=card_code)
                if card.expiration_date < timezone.now():
                    # 卡密已过期，重定向到卡密验证页面
                    return redirect('enter_card')
            except Card.DoesNotExist:
                # 卡密不存在，重定向到卡密验证页面
                return redirect('enter_card')
        return self.get_response(request)
