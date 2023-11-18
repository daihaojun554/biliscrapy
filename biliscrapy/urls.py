from django.urls import path
from . import views

urlpatterns = [
    path("danmaku.html", views.danmaku, name='parse_danmaku'),
    path("comment.html", views.comment, name='parse_comments'),
    path("flash_cookies", views.reflash_cookie, name='flash_cookies'),
    path('generate-chart/', views.generate_chart, name='generate_chart'),
    path('enter_card.html', views.enter_card, name='enter_card'),
    path('export_data/',views.export_data,name='export_data')
]
