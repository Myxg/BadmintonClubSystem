#coding: utf-8
from __future__ import unicode_literals

import os
import collections
import json

from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser

from common.pub_map import (
    MATCH_TYPE_DICT, MATCH_TYPE, USER_ID_TYPE, RESOURCE_ID_TYPE,
    FAVORITE_FOLDER_RECORD_TYPE
)

# Create your models here.

class AthleteCompany(models.Model):

    CONTACT_WAY = (
        (0, u'手机'),
        (1, u'固话')
    )

    STATE = (
        (0, u'启用'),
        (1, u'删除'),
        (2, u'禁用')
    )

    company_id = models.CharField(max_length=32, unique=True)
    company_name = models.CharField(max_length=64, unique=True)
    author_rep = models.CharField(max_length=64, default='', db_index=True)
    credit_code = models.CharField(max_length=128, default='', db_index=True)
    company_addr = models.CharField(max_length=1024, default='')
    contact = models.CharField(max_length=64, default='')
    contact_way = models.IntegerField(choices=CONTACT_WAY, default=0)
    context_info = models.CharField(max_length=64, default='')
    state = models.IntegerField(choices=STATE, default=0)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'athlete_company'

class AthleteInfo(models.Model):

    GENDER = (
        (0, u'男'),
        (1, u'女'),
    )
    
    SPORT_LEVEL = (
        (0, u'特级'),
        (1, u'一级'),
        (2, u'二级'),
        (3, u'三级'),
        (4, u'四级'),
        (5, u'五级'),
        (6, u'六级'),
        (7, u'七级'),
        (8, u'八级'),
    )

    STATE = (
        (0, u'启用'),
        (1, u'删除'),
        (2, u'禁用')
    )

    HAND_HELD = (
        (0, u'右手'),
        (1, u'左手'),
    )

    athlete_id = models.CharField(max_length=32, unique=True)
    company_id = models.CharField(max_length=32, default='', db_index=True)
    name = models.CharField(max_length=64, db_index=True)
    english_name = models.CharField(max_length=64, db_index=True, default='')
    gender = models.IntegerField(choices=GENDER, default=0)
    profile_photo = models.ImageField(max_length=128, upload_to="clubstatic/img/athlete", default='clubstatic/img/athlete/default-photo.png')
    nationality = models.CharField(max_length=32, default='')
    native_place = models.CharField(max_length=255, default='')
    folk = models.CharField(max_length=32, default='汉族')
    birthday = models.DateTimeField(blank=True, null=True)
    sport_project = models.CharField(max_length=32)
    hand_held = models.IntegerField(choices=HAND_HELD, default=0)
    sport_level = models.IntegerField(choices=SPORT_LEVEL)
    initial_training_time = models.DateTimeField(blank=True, null=True)
    first_coach = models.CharField(max_length=64, default='')
    pro_team_coach = models.CharField(max_length=64, default='')
    nat_team_coach = models.CharField(max_length=64, default='')
    state = models.IntegerField(choices=STATE, default=0)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'athlete_info'

    @property
    def company_name(self):
        if self.company_id:
            company = AthleteCompany.objects.filter(company_id = self.company_id).first()
            if company:
                return company.company_name
        return ''

    @property
    def sport_events(self):
        fields = (
            'id', 'sport_event_id', 'event_name', 'event_type', 'event_time', 'rank', 'rank_info',
            'event_honor', 'event_honor_img01', 'event_honor_img02', 'event_honor_img03',
            'created_at', 'updated_at'
        )
        events = []
        sport_events = SportEventExp.objects.filter(athlete_id = self.athlete_id).order_by('id').all()
        if sport_events:
            for event in sport_events:
                tmp = []
                for field in fields:
                    if hasattr(event, 'get_{}_display'.format(field)):
                        tmp.append((field, getattr(event, 'get_{}_display'.format(field))()))
                    elif isinstance(getattr(event, field), models.fields.files.ImageFieldFile):
                        tmp.append((field, getattr(event, field).url))
                    else:
                        tmp.append((field, getattr(event, field)))
                events.append(collections.OrderedDict(tmp))
        return events            

    @property
    def group(self):
        group_ids = AthleteGroupLink.objects.filter(
            athlete_id = self.id
        ).order_by('id').values_list('group_id', flat=True)
        groups = AthleteGroup.objects.filter(pk__in = group_ids).order_by('id').all()
        return [
            collections.OrderedDict((
                ('id', group.id),
                ('name', group.name)
            ))
            for group in groups]

class AthleteGroup(models.Model):
    name = models.CharField(unique=True, max_length=64)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'athlete_group'

    @property
    def athlete(self):
        athlete_ids = AthleteGroupLink.objects.filter(
            group_id = self.id
        ).order_by('id').values_list('athlete_id', flat=True)
        athletes = AthleteInfo.objects.filter(pk__in = athlete_ids).order_by('id').all()
        return [
            collections.OrderedDict((
                ('id', athlete.id),
                ('name', athlete.name)
            ))
        for athlete in athletes]

    @property
    def resource_ids(self):
        athlete_ids = AthleteGroupLink.objects.filter(
            group_id = self.id
        ).order_by('id').values_list('athlete_id', flat=True)
        athletes = AthleteInfo.objects.filter(
            pk__in = athlete_ids
        ).values_list('id', flat=True)
        return athletes

class AthleteGroupLink(models.Model):
    athlete_id = models.IntegerField(db_index=True)
    group_id = models.IntegerField(db_index=True)

    class Meta:
        managed = False
        db_table = 'athlete_group_link'
        unique_together = (('athlete_id', 'group_id'),)

class SportEventExp(models.Model):
    
    EVENT_TYPE = (
        (0, u'国内'),
        (1, u'国外'),
    )

    STATE = (
        (0, u'启用'),
        (1, u'删除'),
        (2, u'禁用')
    )

    sport_event_id = models.CharField(max_length=32, unique=True)
    athlete_id = models.CharField(max_length=32, db_index=True)
    event_name = models.CharField(max_length=64, db_index=True)
    event_type = models.IntegerField(choices=EVENT_TYPE, default=0)
    event_time = models.DateTimeField(blank=True, null=True)
    rank = models.CharField(max_length=64)
    rank_info = models.CharField(max_length=2048, default='')
    event_honor = models.CharField(max_length=2048, default='')
    event_honor_img01 = models.ImageField(max_length=128, upload_to="clubstatic/img/honor", default='clubstatic/img/honor/default-honor.jpg')
    event_honor_img02 = models.ImageField(max_length=128, upload_to="clubstatic/img/honor", default='clubstatic/img/honor/default-honor.jpg')
    event_honor_img03 = models.ImageField(max_length=128, upload_to="clubstatic/img/honor", default='clubstatic/img/honor/default-honor.jpg')
    state = models.IntegerField(choices=STATE, default=0)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sport_event_exp'

class MatchInfo(models.Model):

    MATCH_RESULT = (
        (1, u'胜'),
        (2, u'负'),
    )

    match_id = models.CharField(unique=True, max_length=32)
    level1 = models.CharField(max_length=32, default='')
    level2 = models.CharField(max_length=32, default='')
    match_type = models.IntegerField(choices=MATCH_TYPE, default=0)
    match_name = models.CharField(max_length=128, db_index=True)
    match_date = models.DateTimeField(blank=True, null=True)
    player_a = models.CharField(max_length=32, db_index=True)
    player_a_id = models.CharField(max_length=128, db_index=True)
    player_b = models.CharField(max_length=32, db_index=True)
    player_b_id = models.CharField(max_length=128, db_index=True)
    winnum_a = models.IntegerField(default=0)
    winnum_b = models.IntegerField(default=0)
    match_result = models.IntegerField(choices=MATCH_RESULT)
    match_round = models.CharField(max_length=32, default='')
    memo = models.CharField(max_length=2048, default='')
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'match_info'

class VideoProcInfo(models.Model):
    
    STATE = (
        (0, u"初始化完成"), # 开始执行任务
        (1, u"下载比赛视频完成"),
        (2, u"视频帧转图片完成"),
        (3, u"视频转换完成"),
        (4, u"任务完成"),
    )

    INIT = (
        (0, u"记录初始化未完成"),
        (1, u"记录初始化完成")
    )

    match_id = models.CharField(max_length=32)
    task_id = models.CharField(unique=True, max_length=64)
    tb_name = models.CharField(max_length=32)
    init = models.IntegerField(choices=INIT, default=0)
    state = models.IntegerField(choices=STATE, default=0)
    error_code = models.CharField(max_length=32, default='')
    error_info = models.CharField(max_length=2048, default='')
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'video_proc_info'
        unique_together = (('match_id', 'tb_name'),)

    @property
    def task_is_failured(self):
        return True if self.error_code else False

    @property
    def match_info(self):
        match = MatchInfo.objects.filter(match_id = self.match_id).first()
        return match

    @property
    def match_pkid(self):
        return self.match_info.id if self.match_info else 0

    @property
    def match_name(self):
        return self.match_info.match_name if self.match_info else ''

class RptHits(models.Model):
    
    matchid = models.CharField(max_length=255, blank=True, null=True)
    frame_hit = models.IntegerField()
    frame_prev = models.IntegerField()
    frame_next = models.IntegerField()
    action = models.CharField(max_length=255)
    player = models.CharField(max_length=255, blank=True, null=True)
    zone_start = models.IntegerField()
    height = models.IntegerField()
    zone_end = models.IntegerField()
    video = models.CharField(max_length=255, blank=True, null=True)
    route = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=50, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rpt_hits'

    @property
    def is_comment(self):
        if self.video:
            comment = VideoComment.objects.filter(
                video_name = os.path.basename(self.video)
            ).first()
            if comment:
                return True
        return False

class RptScores(models.Model):
    matchid = models.CharField(max_length=255, blank=True, null=True)
    game = models.CharField(max_length=255, blank=True, null=True)
    score = models.IntegerField()
    score_a = models.IntegerField()
    score_b = models.IntegerField()
    a1num = models.CharField(max_length=255, blank=True, null=True)
    a2num = models.CharField(max_length=255, blank=True, null=True)
    serve = models.CharField(max_length=255, blank=True, null=True)
    goal = models.CharField(max_length=255, blank=True, null=True)
    frame_start = models.IntegerField()
    frame_end = models.IntegerField()
    duration = models.IntegerField()
    updown = models.CharField(max_length=255, blank=True, null=True)
    video = models.CharField(max_length=255, blank=True, null=True)
    route = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=50, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rpt_scores'

    @property
    def is_mark_error(self):
        return self.frame_end <= self.frame_start

    @property
    def is_comment(self):
        if self.video:
            comment = VideoComment.objects.filter(
                video_name = os.path.basename(self.video)
            ).first()
            if comment:
                return True
        return False

class RptServerecord(models.Model):
    matchid = models.CharField(max_length=64, blank=True, null=True)
    score_a = models.IntegerField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    score_b = models.IntegerField(blank=True, null=True)
    serve = models.CharField(max_length=255, blank=True, null=True)
    hit = models.IntegerField(blank=True, null=True)
    special_hit = models.IntegerField()
    land = models.IntegerField(blank=True, null=True)
    game = models.IntegerField()
    video = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=50, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rpt_serverecord'

    @property
    def video_url(self):
        score = RptScores.objects.filter(
            matchid = self.matchid,
            game = self.game,
            score = self.score
        ).first()
        if score:
            return score.video
        return ''

    @property
    def is_comment(self):
        if self.video_url:
            comment = VideoComment.objects.filter(
                video_name = os.path.basename(self.video_url)
            ).first()
            if comment:
                return True
        return False

class RptPlaygroundrecord(models.Model):
    matchid = models.CharField(unique=True, max_length=64, blank=True, null=True)
    a = models.CharField(max_length=255, blank=True, null=True)
    b = models.CharField(max_length=255, blank=True, null=True)
    c = models.CharField(max_length=255, blank=True, null=True)
    d = models.CharField(max_length=255, blank=True, null=True)
    normal = models.IntegerField(blank=True, null=True)
    game = models.IntegerField()
    video = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=50, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rpt_playgroundrecord'

class RptGoalrecord(models.Model):
    matchid = models.CharField(max_length=64, db_index=True)
    score_a = models.IntegerField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True, db_index=True)
    score_b = models.IntegerField(blank=True, null=True)
    goal = models.CharField(max_length=255, blank=True, null=True)
    hit = models.IntegerField(blank=True, null=True)
    land = models.IntegerField(blank=True, null=True)
    active = models.IntegerField(blank=True, null=True)
    game = models.IntegerField(db_index=True)
    operator = models.CharField(max_length=50, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rpt_goalrecord'

    @property
    def video_url(self):
        score = RptScores.objects.filter(
            matchid = self.matchid,
            game = self.game,
            score = self.score
        ).first()
        if score:
            return score.video
        return ''

    @property
    def is_comment(self):
        if self.video_url:
            comment = VideoComment.objects.filter(
                video_name = os.path.basename(self.video_url)
            ).first()
            if comment:
                return True
        return False

class MarkMatchInfo(models.Model):

    # 标注系统的 match_info 表

    create_time = models.DateTimeField(default=now)
    update_time = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0)
    a1num = models.CharField(max_length=255, blank=True, null=True)
    a2num = models.CharField(max_length=255, blank=True, null=True)
    duration = models.CharField(max_length=255, blank=True, null=True)
    event = models.CharField(max_length=255, blank=True, null=True)
    info = models.CharField(max_length=255, blank=True, null=True)
    level1 = models.CharField(max_length=255, blank=True, null=True)
    level2 = models.CharField(max_length=255, blank=True, null=True)
    match_date = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    num = models.CharField(max_length=255, blank=True, null=True)
    oper_time = models.DateTimeField(blank=True, null=True)
    operator = models.CharField(max_length=255, blank=True, null=True)
    pose = models.CharField(max_length=255, blank=True, null=True)
    result = models.CharField(max_length=255, blank=True, null=True)
    round = models.CharField(max_length=255, blank=True, null=True)
    video = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'match_info'

    @property
    def match_id(self):
        return self.num

    @property
    def match_name(self):
        return self.name

class WorldRanking(models.Model):

    match_type = models.IntegerField(choices=MATCH_TYPE)
    athlete_id = models.CharField(max_length=128, db_index=True)
    ranking = models.IntegerField(db_index=True)
    announcemented_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'world_ranking'
        unique_together = (('match_type', 'athlete_id', 'announcemented_at'),)

    @property
    def athlete(self):
        athlete_ids = self.athlete_id.split()
        athletes = AthleteInfo.objects.filter(athlete_id__in=athlete_ids).order_by("id").all()
        return " ".join([
            athlete.name
            for athlete in athletes
        ])

class OlympicRanking(models.Model):

    match_type = models.IntegerField(choices=MATCH_TYPE)
    athlete_id = models.CharField(max_length=128, db_index=True)
    ranking = models.IntegerField(db_index=True)
    points = models.IntegerField(db_index=True)
    announcemented_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'olympic_ranking'
        unique_together = (('match_type', 'athlete_id', 'announcemented_at'),)

    @property
    def athlete(self):
        athlete_ids = self.athlete_id.split()
        athletes = AthleteInfo.objects.filter(athlete_id__in=athlete_ids).order_by("id").all()
        return " ".join([
            athlete.name
            for athlete in athletes
        ])

class User(AbstractUser):

    USER_ROLE = (
        (0, u'管理员'),
        (1, u'运动员'),
        (2, u'教练'),
    )

    USER_TYPE = (
        (0, u'企业'),
        (1, u'个人'),
    )

    email = models.EmailField(max_length=254, default='')
    user_role = models.IntegerField(choices=USER_ROLE, default=1)
    user_type = models.IntegerField(choices=USER_TYPE, default=1)
    profile_photo = models.ImageField(max_length=128, upload_to="clubstatic/img/profilephoto", default='clubstatic/img/profilephoto/default-user.png')

    def __unicode__(self):
        return self.username

    class Meta(AbstractUser.Meta):
        db_table = 'user_exp'

    @property
    def group(self):
        group = []
        user_groups = UserGroup.objects.filter(user_id = self.id).all()
        for user_group in user_groups:
            group += user_group.group
        return group

class Group(models.Model):
    name = models.CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'groups'

    @property
    def user(self):
        users = []
        user_groups = UserGroup.objects.filter(group_id = self.id).all()
        for user_group in user_groups:
            users += user_group.user
        return users
        
class UserGroup(models.Model):
    user_id = models.IntegerField()
    group_id = models.IntegerField(db_index=True)

    class Meta:
        managed = False
        db_table = 'user_group'
        unique_together = (('user_id', 'group_id'),)

    @property
    def group(self):
        groups = Group.objects.filter(pk = self.group_id).all()
        return [
            collections.OrderedDict((
                ('id', group.id),
                ('name', group.name)
            )) 
            for group in groups]

    @property
    def user(self):
        users = User.objects.filter(pk = self.user_id).all()
        return [
            collections.OrderedDict((
                ('id', user.id),
                ('username', user.username),
            ))
            for user in users
        ]

class Privilege(models.Model):
    privilege_id = models.IntegerField(unique=True)
    name = models.CharField(unique=True, max_length=20)

    class Meta:
        managed = False
        db_table = 'privilege'

class UserResourceLink(models.Model):
    user_id = models.IntegerField(db_index=True)
    user_id_type = models.CharField(max_length=10, choices=USER_ID_TYPE)
    resource_type = models.CharField(max_length=20, db_index=True)
    resource_id = models.IntegerField(db_index=True)
    resource_id_type = models.IntegerField(choices=RESOURCE_ID_TYPE)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_resource_link'

    @property
    def resource_ids(self):
        if self.resource_type.endswith('_group') and \
            self.resource_type in settings.RESOURCE_TYPE_MAP:
            module_name, obj_name = settings.RESOURCE_TYPE_MAP[self.resource_type].rsplit('.', 1)
            module = __import__(module_name, None, None, [obj_name])
            model_obj = getattr(module, obj_name)
            obj = model_obj.objects.filter(pk = self.resource_id).first()
            return obj.resource_ids if obj else []
        else:
            return [self.resource_id]

class UserMenuPrivilegeLink(models.Model):
    user_id = models.IntegerField(db_index=True)
    user_id_type = models.CharField(max_length=10, choices=USER_ID_TYPE)
    menu_module_id = models.CharField(max_length=64, db_index=True)
    privilege_id = models.IntegerField()
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_menu_privilege_link'

    @property
    def menu_module_name(self):
        menu_module = MenuModule.objects.get(menu_module_id = self.menu_module_id)
        return menu_module.name

    @property
    def privilege_name(self):
        privilege = Privilege.objects.get(privilege_id = self.privilege_id)
        return privilege.name

class MenuModule(models.Model):
    menu_module_id = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    level = models.IntegerField(blank=True, null=True, default=1)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'menu_module'
            
class DocLink(models.Model):
    """
    文件关联表
    """

    path = models.CharField(max_length=255, db_index=True)
    module_id = models.CharField(max_length=32, db_index=True)
    match_id_link = models.CharField(max_length=255, default='', db_index=True)
    athlete_id_link = models.CharField(max_length=255, default='', db_index=True)
    match_type_link = models.CharField(max_length=32, default='', db_index=True)
    tags_link = models.CharField(max_length=255, default='', db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doc_link'
        unique_together = (('module_id', 'path'),)

    @property
    def match_id_list(self):
        return list(MatchInfo.objects.values('id', 'match_id', 'match_name').filter(
            match_id__in=self.match_id_link.split(',')
        ).all())

    @property
    def athlete_id_list(self):
        return list(AthleteInfo.objects.values('id', 'athlete_id', 'name').filter(
            athlete_id__in=self.athlete_id_link.split(',')
        ).all())

    @property
    def match_type_list(self):
        if self.match_type_link:
            return [
                {'value': i, 'name': MATCH_TYPE_DICT[int(i)]} 
                for i in self.match_type_link.split(',') if int(i) in MATCH_TYPE_DICT
            ]
        return []

    @property
    def data_path(self):   
        doc_data = DocsData.objects.filter(module_id = self.module_id).get()
        return doc_data.data_path.strip()

    @property
    def full_path(self):
        return os.path.join(settings.HISTORY_DATA_PATH, self.data_path, self.path)

    @property
    def staticurl(self):
        return os.path.join(
            settings.HISTORY_DATA_URL,
            self.data_path,
            self.path
        )

class DocsData(models.Model):
    module_id = models.CharField(unique=True, max_length=32)
    module_name = models.CharField(unique=True, max_length=32)
    data_path = models.CharField(max_length=128)

    class Meta:
        managed = False
        db_table = 'docs_data'

class PhysicalFitnessItems(models.Model):
    item_level1 = models.CharField(max_length=32)
    item_name = models.CharField(max_length=32, db_index=True)
    item_id = models.CharField(unique=True, max_length=32)
    unit = models.CharField(max_length=8)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'physical_fitness_items'

class PhysicalFitnessData(models.Model):
    fitness_item_id = models.CharField(max_length=32, db_index=True)
    fitness_test_date = models.DateTimeField(default=now)
    fitness_test_value = models.FloatField()
    athlete_id = models.CharField(max_length=32)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'physical_fitness_data'
        unique_together = (('athlete_id', 'fitness_item_id', 'fitness_test_date'),)

    @property
    def unit(self):
        item = PhysicalFitnessItems.objects.filter(item_id = self.fitness_item_id).get()
        return item.unit

    @property
    def fitness_item_name(self):
        item = PhysicalFitnessItems.objects.filter(item_id = self.fitness_item_id).get()
        return item.item_name

    @property
    def athlete_name(self):
        athlete = AthleteInfo.objects.filter(athlete_id = self.athlete_id).get()
        return athlete.name

class MyDistance(models.Model):
    match_num = models.CharField(max_length=20, blank=True, null=True)
    a1x = models.CharField(max_length=20, blank=True, null=True)
    jq_a1x = models.CharField(max_length=20, blank=True, null=True)
    jx_a1x = models.CharField(max_length=20, blank=True, null=True)
    a1y = models.CharField(max_length=20, blank=True, null=True)
    jq_a1y = models.CharField(max_length=20, blank=True, null=True)
    jx_a1y = models.CharField(max_length=20, blank=True, null=True)
    a2x = models.CharField(max_length=20, blank=True, null=True)
    jq_a2x = models.CharField(max_length=20, blank=True, null=True)
    jx_a2x = models.CharField(max_length=20, blank=True, null=True)
    a2y = models.CharField(max_length=20, blank=True, null=True)
    jq_a2y = models.CharField(max_length=20, blank=True, null=True)
    jq_xa2y = models.CharField(max_length=20, blank=True, null=True)
    a3x = models.CharField(max_length=20, blank=True, null=True)
    jq_a3x = models.CharField(max_length=20, blank=True, null=True)
    jx_a3x = models.CharField(max_length=20, blank=True, null=True)
    a3y = models.CharField(max_length=20, blank=True, null=True)
    jq_a3y = models.CharField(max_length=20, blank=True, null=True)
    jx_a3y = models.CharField(max_length=20, blank=True, null=True)
    b1x = models.CharField(max_length=20, blank=True, null=True)
    jq_b1x = models.CharField(max_length=20, blank=True, null=True)
    jx_b1x = models.CharField(max_length=20, blank=True, null=True)
    b1y = models.CharField(max_length=20, blank=True, null=True)
    jq_b1y = models.CharField(max_length=20, blank=True, null=True)
    jx_b1y = models.CharField(max_length=20, blank=True, null=True)
    b2x = models.CharField(max_length=20, blank=True, null=True)
    jq_b2x = models.CharField(max_length=20, blank=True, null=True)
    jx_b2x = models.CharField(max_length=20, blank=True, null=True)
    b2y = models.CharField(max_length=20, blank=True, null=True)
    jq_b2y = models.CharField(max_length=20, blank=True, null=True)
    jx_b2y = models.CharField(max_length=20, blank=True, null=True)
    b3x = models.CharField(max_length=20, blank=True, null=True)
    jq_b3x = models.CharField(max_length=20, blank=True, null=True)
    jx_b3x = models.CharField(max_length=20, blank=True, null=True)
    b3y = models.CharField(max_length=20, blank=True, null=True)
    jq_b3y = models.CharField(max_length=20, blank=True, null=True)
    jx_b3y = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'my_distance'

class MyJuli(models.Model):
    matchid = models.CharField(max_length=20, blank=True, null=True)
    game = models.CharField(max_length=20, blank=True, null=True)
    score = models.CharField(max_length=20, blank=True, null=True)
    score_a = models.CharField(max_length=20, blank=True, null=True)
    score_b = models.CharField(max_length=20, blank=True, null=True)
    goal = models.CharField(max_length=20, blank=True, null=True)
    shot = models.CharField(max_length=20, blank=True, null=True)
    t = models.CharField(max_length=20, blank=True, null=True)
    a_juli = models.CharField(max_length=20, blank=True, null=True)
    b_juli = models.CharField(max_length=20, blank=True, null=True)
    a_sudu = models.CharField(max_length=20, blank=True, null=True)
    b_sudu = models.CharField(max_length=20, blank=True, null=True)
    per_a = models.CharField(max_length=1000, blank=True, null=True)
    per_b = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'my_juli'

    """
    @property
    def locus_points(self):
        score = RptScores.objects.filter(matchid = self.matchid).first()
        points_a = []
        points_b = []
        if not score:
            return points_a, points_b
        zbs = MyZb.objects.filter(
            match_num = self.matchid, 
            frame_num__gte = score.frame_start,
            frame_num__lte = score.frame_end).order_by('frame_num').all()
        if not zbs:
            return points_a, points_b
        for zb in zbs:
            if int(zb.people_num) == 1:
                points_a.append({"x": zb.x, "y": zb.y})
            if int(zb.people_num) == 2:
                points_b.append({"x": zb.x, "y": zb.y})
        return points_a, points_b
    """
        
class MyZb(models.Model):
    match_num = models.CharField(max_length=20, blank=True, null=True)
    frame_num = models.CharField(max_length=20, blank=True, null=True)
    people_num = models.CharField(max_length=20, blank=True, null=True)
    x = models.FloatField(blank=True, null=True)
    y = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'my_zb'

class VideoComment(models.Model):
    video_name = models.CharField(db_index=True, max_length=64)
    parent_id = models.IntegerField(db_index=True, default=0)
    content = models.CharField(max_length=800, default='')
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'video_comment'

    @property
    def user(self):
        user = User.objects.filter(pk = self.user_id).first()
        return user

    @property
    def username(self):
        return self.user.username if self.user else ''

    @property
    def profile_photo(self):
        return self.user.profile_photo.url if self.user else ''

class FavoriteFolder(models.Model):
    name = models.CharField(max_length=64)
    parent_id = models.IntegerField(db_index=True, default=0)
    url = models.CharField(max_length=1000, default='')
    record_type = models.IntegerField(db_index=True, choices=FAVORITE_FOLDER_RECORD_TYPE)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'favorite_folder'
        unique_together = (('name', 'parent_id', 'record_type', 'user_id'),)

class VideoBatchShareTasks(models.Model):
    user_id = models.IntegerField(db_index=True)
    task_id = models.CharField(max_length=64, db_index=True)
    video_list = models.CharField(max_length=2048)
    url = models.CharField(max_length=2048)
    state = models.CharField(max_length=16, db_index=True)
    state_name = models.CharField(max_length=16, db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'video_batch_share_tasks'
        unique_together = (('user_id', 'task_id'),)


