#coding: utf-8

LOCAL_SETTINGS = False

from clubmg.settings import *
import datetime

DEBUG = True

DATABASES.update({
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'club',
        'USER': 'club',
        'PASSWORD': 'Passw0rd235',
        #'HOST': 'club.cssit0ss2fi8.rds.cn-northwest-1.amazonaws.com.cn',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    },
    'markdb': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'badminton',
        'USER': 'root',
        'PASSWORD': 'Hbts@1234',
        #'HOST': '172.26.99.70',
	'HOST':'39.98.138.161',
        'PORT': '3306',
    }
})

# 使用 redis 作为缓存
USE_CACHE = True
if USE_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://:redisauth123@127.0.0.1:6379/10",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"max_connections": 100},
                "SOCKET_CONNECT_TIMEOUT": 5,  # in seconds
                "SOCKET_TIMEOUT": 5,  # in seconds
                "IGNORE_EXCEPTIONS": True,
            }
        }
    }

# Celery config
# 消息中间件地址
BROKER_URL = 'redis://:redisauth123@127.0.0.1:6379/11'
# ack 确认收到超时，表示任务发出后在规定的时间内未收到 acknowledge，则重新交个其他 worker 执行。
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 600}
# 任务执行结果存储位置
CELERY_RESULT_BACKEND = 'redis://:redisauth123@127.0.0.1:6379/12'
# 并发 worker 数量，默认为 cpu 核数
#CELERYD_CONCURRENCY = 4
# 每个 worker 执行多少任务任务后销毁，防止内存泄露
CELERYD_MAX_TASKS_PER_CHILD = 100
# 单个任务最长运行时间
CELERYD_TASK_TIME_LIMIT = 60 * 60 * 24
# 序列化格式
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# 时区
CELERY_TIMEZONE = 'Asia/Shanghai'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        #'clubserver.permissions.CustomPermission',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'EXCEPTION_HANDLER': 'common.utils.custom_exception_handler',
}

AUTH_USER_MODEL = 'clubserver.User'

MIDDLEWARE.append('django.middleware.locale.LocaleMiddleware')

LANGUAGES = (
    ('zh-hans', (u'中文简体')),
)

LANGUAGE_COOKIE_NAME='zh-hans'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'rest_framework_jwt/locale'),
)

ALLOWED_HOSTS = ['*']
# 跨域
XS_SHARING_ALLOWED_ORIGINS = '*'
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']
XS_SHARING_ALLOWED_HEADERS = ['Content-Type', '*']
XS_SHARING_ALLOWED_CREDENTIALS = 'true'

# JWT 配置
JWT_AUTH = {
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'common.utils.jwt_response_payload_handler',
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=86400),
}

# aws S3 配置
AWS_S3_AK = 'AKIA3VMHMXD2YGXNKXM4'
AWS_S3_SK = '/AyZtsCOG0FHXnNJVnMBbnzjPcvWUJkvq+1xujGt'
AWS_S3_BUCKET = 'video.hbang.com.cn'
AWS_S3_REGION = 'cn-northwest-1' # 中国宁夏
AWS_S3_OBJ_URL_EXPIRESIN = 3600 # 生成的 url 过期时间

# aws s3 Report 系统配置
AWS_S3_R_AK = 'AKIAOHEQFBAKQH4VLVTQ'
AWS_S3_R_SK = 'sSCs6XcTZZhf/GoMRK0ASQ1JStDfh5Xf0xOxDN2k'
AWS_S3_R_BUCKET = 'badminton'
AWS_S3_R_REGION = 'cn-northwest-1' # 中国宁夏
AWS_S3_R_OBJ_URL_EXPIRESIN = 3600 # 生成的 url 过期时间

# aws s3 视频 bucket
AWS_S3_VIDEO_BUCKET = 'archive.hbang.com.cn'

STATIC_URL = '/clubstatic/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "clubstatic"),
)

# 本地原始视频存放目录
VIDEO_LOCAL_PATH = '/archive/'
# 视频转换过程临时目录
VIDEO_CONV_SAVE_PATH = '/data/tmp/conv/'
# 合成视频存放目录
VIDEO_SAVE_PATH = '/archive/'

# 视频文件 URL
MATCH_VIDEOS = '/matchvideos/'

# 历史数据文件 URL
HISTORY_DATA_URL = '/docs/'
# 理数数据存放目录
HISTORY_DATA_PATH = '/home/ubuntu/docs'

# 打包视频&下载存放目录
COMPRESSED_PACKAGING_DIR = os.path.join(BASE_DIR, 'clubstatic', 'video', 'download')
# 视频打包后下载目录 URL
COMPRESSED_PACKAGING_URL = os.path.join(STATIC_URL, 'video', 'download')
