#coding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import re
from dateutil import tz
import collections

import boto3
from boto3.s3.transfer import TransferConfig

from botocore.exceptions import ClientError

bk = 'archive.hbang.com.cn'
ak = 'AKIA3VMHMXD2YGXNKXM4'
sk = '/AyZtsCOG0FHXnNJVnMBbnzjPcvWUJkvq+1xujGt'
rg = 'cn-northwest-1'

s3_client = boto3.client(
                's3',
                region_name=rg,
                aws_access_key_id=ak,
                aws_secret_access_key=sk
            )

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

def list_obj(bk=bk, prefix='2019'):
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bk, Prefix=prefix)
    i = 0
    for key in result.search(u"Contents"):
        del key['StorageClass']
        del key['Owner']
        print(key)
        i += 1
        #if i == 20:
        #    break

def s3_video_path_list(module_id, prefix='', bucket=bk):
    obj_key_list = []
    paginator = s3_client.get_paginator('list_objects')
    result = paginator.paginate(Bucket=bucket, Prefix=prefix)

    for obj in result.search(u"Contents"):
        obj_key = obj['Key'][len(prefix):]
        name = obj_key.strip('/')
        mtime = obj['LastModified'].astimezone(tz.tzlocal()).strftime("%Y-%m-%dT%H:%M:%S")
        filesize = file_size_humanity(obj['Size'])
        path = obj_key
        staticurl = ''
        # 目录
        if obj_key.endswith('/') and len(obj_key.strip('/').split('/')) == 1:
            f_type = 'folder'
            print obj_key
        # 文件
        elif len(obj_key.split('/')) == 1 and obj_key.find('.') != -1:
            f_type = 'file'
            print obj_key
            #staticurl = get_aws_s3_obj_url(
            #    obj_key,
            #    s3_client=s3_client,
            #    bucket_name=bucket
            #)  
        else:
            continue
            print obj
        obj_key_list.append(
            collections.OrderedDict(
                (
                    ('module_id', module_id),
                    ('name', name),
                    ('datetime', mtime),
                    ('filesize', filesize),
                    ('type', f_type),
                    ('path', path),
                    ('staticurl', staticurl),
                )
            ) 
        )     
              
    return obj_key_list

    
if __name__ == '__main__':
    #list_obj()
    from pprint import pprint
    pprint(s3_video_path_list('tt', '2019/0917-0922-中国公开赛/'))
