from django.urls import path
from . import views

urlpatterns = [
    path("danmaku.html", views.danmaku, name='parse_danmaku'),
    path("comment.html", views.comment, name='parse_comments'),
    path("flash_cookies", views.reflash_cookie, name='flash_cookies'),

]
