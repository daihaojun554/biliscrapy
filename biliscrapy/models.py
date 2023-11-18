from django.db import models


# Create your models here.
class BiliDanmu(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    cid = models.CharField(max_length=255)
    content = models.TextField()
    color = models.CharField(max_length=255)
    fontsize = models.IntegerField()
    midHash = models.CharField(max_length=255)
    mode = models.CharField(max_length=255)
    progress = models.FloatField()
    ctime = models.DateTimeField()

    def __str__(self):
        return self.content


class BiliComment(models.Model):
    avid = models.CharField(max_length=255)
    uname = models.CharField(max_length=255)
    # 最高等级就是6级
    current_level = models.IntegerField()
    # 用户等级
    like = models.IntegerField()
    # 用户性别 男 女 保密
    sex = models.CharField(max_length=10)
    ctime = models.DateTimeField()
    message = models.TextField()

    def __str__(self):
        return self.message


class BiliVideo(models.Model):
    bvid = models.CharField(max_length=30, unique=True)
    avid = models.IntegerField(unique=True)
    oid = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    pubdate = models.DateField()
    pic = models.URLField()
    desc = models.TextField()
    danmu_fetched = models.BooleanField(default=False)
    comment_fetched = models.BooleanField(default=False)
    danmaku_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Card(models.Model):
    card_code = models.CharField(max_length=100, unique=True)
    expiration_date = models.DateTimeField()
    last_used_address = models.GenericIPAddressField(null=True, blank=True)
    # action = models.CharField(max_length=100)
    # is_active = models.BooleanField(default=True)
    # is_expired = models.BooleanField(default=False)
    # count = models.IntegerField(default=0)

    def __str__(self):
        return self.card_code
