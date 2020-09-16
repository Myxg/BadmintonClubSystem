# coding: utf-8

import sys
import os
import datetime
from collections import OrderedDict
import time
import uuid
import hashlib
import zipfile
import random
import string

import numpy as np
from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


def jwt_response_payload_handler(token, user=None, request=None):
    expires_at = (
        datetime.datetime.now() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
    )
            
    return OrderedDict([
        ('status_code', 0),
        ('username', user.username),
        ('id', user.id),
        ('token', token),
        ('expires_at', expires_at),
        ('issued_at', datetime.datetime.now()),
    ])


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.

    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response

class ModelUpdateSerializer(object):
    def update_is_valid(self):
        errors = {}
        _instance = self.instance
        if self.is_valid():
            return self.errors

        if hasattr(self.Meta, 'foreign_id_fields'):
            _fields = self.Meta.foreign_id_fields
            for item in _fields:
                _foreign_id, _model, _model_foreign_id = item
                _query_dict = {
                    _model_foreign_id: self.initial_data[_foreign_id],
                }
                ins = _model.objects.filter(**_query_dict).all()
                if len(ins) == 0:
                    errors[_foreign_id] = [u"“{}” 不存在外部关联".format(_foreign_id)]

        if hasattr(self.Meta, 'unique_fields'):
            _model = self.Meta.model
            _fields = self.Meta.unique_fields
            for items in _fields:
                _query_dict = {}
                for item in items:
                    _query_dict[item] = self.initial_data.get(item, '')
                ins = _model.objects.filter(**_query_dict)
                if not (len(ins) == 0 or
                    len(ins) == 1 and
                    ins[0].pk == _instance.pk):
                    errors.update(self.errors)
                    return errors
                for error in self.errors:
                    if error == 'non_field_errors':
                        for e in self.errors[error]:
                            if e.code == 'unique':
                                continue
                            else:
                                errors.setdefault(error, []).append(e)
                    else:
                        errors[error] = self.errors[error]
            return errors
        else:
            errors.update(self.errors)
            return errors

    def update_save(self):
        _instance = self.instance
        for item in self.Meta.fields:
            if item in self.initial_data:
                setattr(_instance, item, self.initial_data[item])
        _instance.save()

class CustomPageNumberPagination(PageNumberPagination):
    """
    自定义分页
    """
    # 默认每页 20 个
    page_size = 20
    # 每页最大数量
    max_page_size = 9999
    # ?page=2&size=4,改变默认每页显示的个数
    page_size_query_param = "page_size"
    page_query_param = "page"
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('status_code', 0),
            ('pagination', self.page.paginator.count),
            ('page', self.page.start_index() // self.page.paginator.per_page + 1),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ]))

CeleryState = {
    "PENDING": u"任务等待中",
    "STARTED": u"任务已开始",
    "SUCCESS": u"任务执行成功",
    "FAILURE": u"任务执行失败",
    "RETRY":   u"任务将被重试",
    "REVOKED": u"任务取消",
}

Codes = {
    0: u'成功',
    1001: u'查询失败, 未查询到',
    1002: u'查询失败，查询多于一个结果',
    1003: u'插入失败',
    1004: u'更新失败',
    1005: u'删除失败',
    1006: u'DB 连接失败',
    1007: u'DB 错误，请联系管理员',

    2001: u'参数错误',

    701: u'失败',
    702: u'其他错误，请联系管理员'
}

def return_code(status_code=0, msg='', detail='', data='', **kwargs):
    return_obj = {
        'status_code': status_code,
        'msg': msg or Codes.get(status_code, ''),
        'data': data,
    }
    if status_code != 0:
        return_obj['detail'] = detail or Codes.get(status_code, ''),
    return_obj.update(kwargs)
    return return_obj

def lmd5sum():
    Hash = hashlib.md5()
    task_id = str(time.time()) + str(uuid.uuid4())
    Hash.update(task_id)
    return Hash.hexdigest()

def zip_dir(dirpath, zipfilename):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param zipfilename: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()

def gen_random_str(length=6):
    """
    生成随机字符串，默认长度为 6
    :param length: 随机字符串长度
    :return: 返回生成的随机字符串
    """

    letters = string.ascii_letters
    digital = string.digits
    src = letters + digital
    must = [letters, digital]
    random_str = random.sample(src, length-len(must))
    for m in must:
        random_str += random.sample(m, 1)
    return "".join(random_str)

def file_size_humanity(size):
    if size < 1024:
        return size
    elif 1024 <= size < 1024 * 1024:
        return "{}K".format(round(size / 1024.0, 2))
    elif 1024 * 1024 <= size < 1024 * 1024 * 1024:
        return "{}M".format(round(size / 1024.0 / 1024.0, 2))
    elif 1024 * 1024 * 1024 <= size:
        return "{}G".format(round(size / 1024.0 / 1024.0 / 1024.0, 2))
    else:
        return size

def get_file_mtime(f):
    unix_ts = os.path.getmtime(f)
    return datetime.datetime.fromtimestamp(unix_ts).strftime("%Y-%m-%dT%H:%M:%S")

def get_file_size(f):
    fsize = os.path.getsize(f)
    return file_size_humanity(fsize)

def flip180(matrix):
    """
    矩阵旋转 180°
    """
    new_matrix = matrix.reshape(matrix.size)
    new_matrix = new_matrix[::-1]
    new_matrix = new_matrix.reshape(matrix.shape)
    return new_matrix 

def get_zone_list(zone, line):
    """计算羽毛球飞行线路(直线|斜线)落地点区域列表
    :param zone: int 起始区域
    :param line: int 直线1|斜线2
    """
    # 羽毛球场地 zone 矩阵表示
    pos_zone_m = np.array(([7, 8, 9], [4, 5, 6], [1, 2, 3]))
    neg_zone_m = np.array(([-3, -2, -1], [-6, -5, -4], [-9, -8, -7]))

    if zone > 0:
        matrix_zone = pos_zone_m
    elif zone < 0:
        matrix_zone = neg_zone_m
    else:
        raise

    row, col = matrix_zone.shape

    for i in range(col):
        if zone in matrix_zone[:, i]:
            zone_col = i

    matrix_zone_180 = flip180(matrix_zone)

    # 直线落点区域列表
    z_line = []
    # 斜线落点区域列表
    x_line = []

    for i in range(col):
        if i == zone_col:
            z_line += [-i for i in list(matrix_zone_180[:, i])]
        else:
            x_line += [-i for i in list(matrix_zone_180[:, i])]

    if line == 1:
        return z_line
    elif line == 2:
        return x_line
    else:
        raise   

def _is_date_type(value):
    """
    判断是否为时间，日期类型。
    可接受的类型如下或以下类型的扩展
        datetime.date
        datetime.time
    """
    return isinstance(value, (datetime.date, datetime.time))

def calculate_age(born):
    """
    根据出生日期计算年龄
    """
    if not _is_date_type(born):
        return ''
    today = datetime.datetime.today()
    try: 
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year

def get_video_url(video_path):
    """
    根据视频的相对路径生成静态文件 url
    """

    prefix_path = settings.MATCH_VIDEOS
    return os.path.join(prefix_path, video_path.strip('/'))

class CommentSys(object):

    def __init__(self, comment):
        self.id = comment.id
        self.video_name = comment.video_name
        self.parent_id = comment.parent_id
        self.content = comment.content
        self.user_id = comment.user_id
        self.username = comment.username
        self.profile_photo = comment.profile_photo
        self.created_at = comment.created_at.strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = comment.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        self.child = []

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, item):
        return getattr(self, item)

    def make_dict(self):
        return self.__dict__


def commentlink(comments):
    comment_list = []
    parent_list = []
    for comment in comments:
        cs = CommentSys(comment)
        if cs.parent_id == 0:
            comment_list.append(cs)
            parent_list.append(cs)
        else:
            for parent in parent_list:
                if comment.parent_id == parent.id:
                    parent.child.append(cs)
                    parent_list.append(cs)
                    break
    return comment_list

