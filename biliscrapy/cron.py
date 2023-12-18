from django.core.management.base import BaseCommand

from biliscrapy.models import BiliVideo


class Command(BaseCommand):
    help = 'Deletes records from the database'
    def handle(self, *args, **options):
        # 在这里编写删除数据库内容的代码
        # BiliVideo.objects.all().delete()
        pass