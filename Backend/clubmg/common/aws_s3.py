#coding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import re
import datetime
from dateutil import tz
import collections

import boto3
from boto3.s3.transfer import TransferConfig

from django.conf import settings
from django.core.cache import cache
from botocore.exceptions import ClientError

from common.utils import file_size_humanity

s3_client = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION,
                aws_access_key_id=settings.AWS_S3_AK,
                aws_secret_access_key=settings.AWS_S3_SK
            )

s3_report_client = boto3.client(
                's3',
                region_name=settings.AWS_S3_R_REGION,
                aws_access_key_id=settings.AWS_S3_R_AK,
                aws_secret_access_key=settings.AWS_S3_R_SK
            )

s3_resource = boto3.resource(
                's3',
                region_name=settings.AWS_S3_REGION,
                aws_access_key_id=settings.AWS_S3_AK,
                aws_secret_access_key=settings.AWS_S3_SK
              )


GB = 1024 ** 3
trans_config = TransferConfig(multipart_threshold=1*GB, max_concurrency =10)

def get_presigned_url(
        object_name,
        s3_client=s3_client,
        bucket_name=settings.AWS_S3_BUCKET,
        expiration=settings.AWS_S3_OBJ_URL_EXPIRESIN
    ):

    """Generate a presigned URL to share an S3 object

    :param s3_client: settings, default s3 client
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    
    try:
        url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket_name,
                                    'Key': object_name},
                            ExpiresIn=expiration
                        )
    except ClientError as e:
        return None

    return url

def get_presigned_url_withcache(
        object_name,
        s3_client=s3_client,
        bucket_name=settings.AWS_S3_BUCKET,
        expiration=settings.AWS_S3_OBJ_URL_EXPIRESIN
    ):
    """Generate a presigned URL to share an S3 object

    :param s3_client: settings, default s3 client
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    cache_key = "{}:{}".format(bucket_name, object_name)
    url = cache.get(cache_key)
    if url is not None:
        return url
    url = get_presigned_url(object_name, s3_client, bucket_name, expiration)
    if url is not None:
        cache.set(cache_key, url, timeout=expiration)
    return url

if settings.USE_CACHE:
    get_aws_s3_obj_url = get_presigned_url_withcache
else:
    get_aws_s3_obj_url = get_presigned_url

def get_object_key(
        regstr,
        bucket_name=settings.AWS_S3_BUCKET
    ):
    """获取 bucket 中所有的 object
    :param regstr: string, 需要获取 key 的正则字符串
    :param bucket_name: string
    :return: s3 object key list
    """

    obj_key_list = []
    
    reg = re.compile(regstr)
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket_name)
    for prefix in result.search(u"Contents"):
        obj_key = prefix.get('Key')
        if reg.search(obj_key):
            obj_key_list.append(obj_key)
    return obj_key_list

def download_object_from_s3(
        object_name,
        save_path,
        bucket_name=settings.AWS_S3_BUCKET,
    ):

    with open(save_path, 'wb') as data:
        s3_client.download_fileobj(bucket_name, object_name, data, Config=trans_config)

def upload_object_to_s3(
        file_name,
        object_name,
        bucket_name=settings.AWS_S3_BUCKET
    ):

    with open(file_name, 'rb') as data:
        s3_client.upload_fileobj(data, bucket_name, object_name, Config=trans_config)

def copy_boject(
        from_object,
        to_object,
        from_bucket_name=settings.AWS_S3_BUCKET,
        to_bucket_name=settings.AWS_S3_BUCKET
    ):

    copy_source = {
        "Bucket": from_bucket_name,
        "Key": from_object
    }

    bucket = s3_resource.Bucket(to_bucket_name)
    bucket.copy(copy_source, to_object)

def object_exist(object_key, bucket_name=settings.AWS_S3_BUCKET):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            return None
        else:
            raise ex

def s3_video_path_list(prefix='', bucket=settings.AWS_S3_VIDEO_BUCKET):
    obj_key_list = []
    prefix = '' if prefix == '/' else prefix
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket, Prefix=prefix)

    for obj in result.search(u"Contents"):
        obj_key = obj['Key'][len(prefix):]
        name = obj_key.strip('/')
        mtime = obj['LastModified'].astimezone(tz.tzlocal()).strftime("%Y-%m-%dT%H:%M:%S")
        filesize = file_size_humanity(obj['Size'])
        staticurl = ''
        # 目录
        if obj_key.endswith('/') and len(obj_key.strip('/').split('/')) == 1:
            f_type = 'folder'
        # 文件
        elif len(obj_key.split('/')) == 1 and obj_key.find('.') != -1:
            f_type = 'file'
            staticurl = get_aws_s3_obj_url(
                obj['Key'],
                s3_client=s3_client,
                bucket_name=bucket
            )
        else:
            continue
        obj_key_list.append(
            collections.OrderedDict(
                (
                    ('name', name),
                    ('datetime', mtime),
                    ('filesize', filesize),
                    ('type', f_type),
                    ('path', obj['Key']),
                    ('staticurl', staticurl),
                )
            )
        )

    return obj_key_list
    
if __name__ == '__main__':
    regstr = r'{}/{}/{}/{}.*\.(mp4|MP4|mts|MTS)'.format('2019', '0308', '0000', '2019_0308_0000')
    regstr = r'.*'
    videos = get_object_key(regstr, bucket_name=archive.hbang.com.cn)
    print videos
    #download_object_from_s3(videos[0])
