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
        'HOST': 'club.cssit0ss2fi8.rds.cn-northwest-1.amazonaws.com.cn',
        'PORT': '3306',
    },
    'markdb': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'badminton',
        'USER': 'root',
        'PASSWORD': 'Hbts@1234',
        'HOST': 'mark.hbang.com.cn',
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
        'clubserver.permissions.CustomPermission',
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

STATIC_URL = '/clubstatic/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "clubstatic"),
)

# 视频下载存放目录
VIDEO_DOWNLOAD_PATH = '/data/tmp'
# 视频转换后存放的目录
VIDEO_CONV_SAVE_PATH = '/data/tmp/conv/'

# api url 前缀
API_PREFIX = 'api/v1/'

# 资源id 与 资源对应关系字典
RESOURCE_TYPE_MAP = {
    'athlete':  'clubserver.models.AthleteInfo', #'运动员信息'
#    'company': 'clubserver.models.AthleteCompany' #'来源单位信息'
}

# 视频文件 URL
MATCH_VIDEOS = '/matchvideos/'

# 历史数据文件 URL
HISTORY_DATA_URL = '/docs/'
# 理数数据存放目录
HISTORY_DATA_PATH = '/home/ubuntu/docs'


