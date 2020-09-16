#coding: utf-8

import re
import collections

MATCH_TYPE = (
    (0, u'男单'),
    (1, u'女单'),
    (2, u'男双'),
    (3, u'女双'),
    (4, u'混双')
)

MATCH_TYPE_DICT = collections.OrderedDict(MATCH_TYPE)

ZONE_NAME_MAP = {
    1: u"正手网前",
    2: u"中路网前",
    3: u"反拍网前",
    4: u"正手接杀",
    5: u"中路",
    6: u"反手接杀",
    7: u"正手后场",
    8: u"中路后场",
    9: u"头顶后场",
    -1: u"正手网前",
    -2: u"中路网前",
    -3: u"反拍网前",
    -4: u"正手接杀",
    -5: u"中路",
    -6: u"反手接杀",
    -7: u"正手后场",
    -8: u"中路后场",
    -9: u"头顶后场",

    0: u"发球失误",
    90: u"过网未过前端线",
    91: u"未过线",
    92: u"出左边线",
    93: u"出右边线",
    94: u"出底线",
    95: u"违例"
}

ZONE_LIST_A = [x for x in range(1, 10)]
ZONE_LIST_B = [x for x in range(-9, 0)]
ZONE_LIST = ZONE_LIST_A + ZONE_LIST_B

FAULT_LIST = [90, 91, 92, 93, 94, 95]

FULL_GAME_LIST = [0, 1, 2, 3]

SINGLE_PLAYER = ['a', 'b']
DOUBLE_PLAYER = ['a1', 'a2', 'b1', 'b2']
DOUBLE_END_ZONE_LIST = [1, 2, 3, 4, 5, 6]
SERVE_ZONE = {
    1: u"左上",
    2: u"右上",
    3: u"左下",
    4: u"右下"
}
SERVE_ZONE_LEFT = [1, 3]
SERVE_ZONE_RIGHT = [2, 4]

LINE_MPA = {
    0: u"全部",
    1: u"直线",
    2: u"斜线"
}

ACTION_MAP = {
    1: u"发球",
    2: u"勾球",
    3: u"吊球",
    4: u"平抽",
    5: u"平推后场",
    6: u"扑球",
    7: u"抽挡",
    8: u"拦吊",
    9: u"挑球",
    10: u"挑球擦网",
    11: u"接吊",
    12: u"接杀",
    13: u"接杀放网",
    14: u"接杀其它",
    15: u"推后场",
    16: u"推挡",
    17: u"推球",
    18: u"放网",
    19: u"杀球",
    20: u"死球",
    21: u"高远球",
    22: u"其它",
}

HEIGHT_MAP = {
    -2: u"被动",
    -1: u"半被动",
    0: u"平衡",
    1: u"半主动",
    2: u"主动"
}

# 被动失误(受迫性失误)
FORCE_MISTAKE_LIST = [-1, -2]
# 主动失误(非受迫性失误)
UNFORCE_MISTAKE_LIST = [0, 1, 2]

def get_match_type(match_type):
    for item in MATCH_TYPE:
        if match_type == item[1]:
            return item
    return MATCH_TYPE[0]


GAME_LIST = (1, 2, 3)
PLAYER_LIST = ('a', 'b')

# 回合时长报表接口相应函数
SECOND_RANGE_LIST = ('0-8', '8-16', '16-24', '24+')
def init_time_table_data():
    data = collections.OrderedDict()
    for game in GAME_LIST:
        data[game] = collections.OrderedDict()
        for player in PLAYER_LIST:
            data[game][player] = collections.OrderedDict()
            for second in SECOND_RANGE_LIST:
                data[game][player][second] = collections.OrderedDict((
                    ('action_score', 0),
                    ('mistake_score', 0),
                    ('total', 0),
                    ('score_pre', '0%'),
                ))
        data[game]['total'] = 0
    return data

def init_second_range_dict():
    data = {}
    for item in SECOND_RANGE_LIST:
        sec_range = [int(i) for i in re.split('-|\+', item) if i]
        for sec in range(sec_range[0]+1, sec_range[-1]+1):
            data[sec] = item
    return data

TIME_TABLE_DATA = init_time_table_data()
SECOND_RANGE_DICT = init_second_range_dict()
def find_sec_key(sec):
    return SECOND_RANGE_DICT.get(sec, '24+')
def get_score_type(zone_start, height):
    if zone_start in ZONE_LIST:
        # 主动得分
        return 'action_score'
    elif (zone_start in FAULT_LIST and
        height in (FORCE_MISTAKE_LIST +
        UNFORCE_MISTAKE_LIST)):
        # 被动得分
        return 'mistake_score'

# 回合击球拍数报表接口相应函数
BEAT_RANGE_LIST = ('0-2', '3-8', '9-16', '17+', 'total')
def init_beat_table_data():
    data = collections.OrderedDict()
    for game in GAME_LIST:
        data[game] = collections.OrderedDict()
        for player in PLAYER_LIST:
            data[game][player] = collections.OrderedDict()
            for beat in BEAT_RANGE_LIST:
                data[game][player][beat] = collections.OrderedDict((
                    ('score', 0),
                    ('score_pre', '0%')
                ))
        data[game]['total'] = 0
    return data

def init_beat_range_dict():
    data = {}
    for item in BEAT_RANGE_LIST[:-1]:
        sec_range = [int(i) for i in re.split('-|\+', item) if i]
        for sec in range(sec_range[0], sec_range[-1]+1):
            data[sec] = item
    return data

BEAT_TABLE_DATA = init_beat_table_data()
BEAT_RANGE_DICT = init_beat_range_dict()
def find_beat_key(beat):
    return BEAT_RANGE_DICT.get(beat, '17+')

# 得分类型报表接口相应函数
TYPE_RANGE_LIST = ('action_score', 'force_mistake_score', 'unforce_mistake_score', 'total')
def init_type_table_data():
    data = collections.OrderedDict()
    for game in GAME_LIST:
        data[game] = collections.OrderedDict()
        for player in PLAYER_LIST:
            data[game][player] = collections.OrderedDict()
            for score_type in TYPE_RANGE_LIST:
                data[game][player][score_type] = {'score': 0, 'score_pre': '0%'}
        data[game]['total'] = 0
    return data

TYPE_TABLE_DATA = init_type_table_data()
def find_type_key(zone_start, height):
    if zone_start in ZONE_LIST:
        # 制胜分
        return 'action_score'
    elif zone_start in FAULT_LIST and \
        height in FORCE_MISTAKE_LIST:
        # 受迫性失误
        return 'force_mistake_score'
    elif zone_start in FAULT_LIST and \
        height in UNFORCE_MISTAKE_LIST:
        # 非受迫性失误
        return 'unforce_mistake_score'

if __name__ == '__main__':
    from pprint import pprint
    pprint(SECOND_RANGE_DICT)
    print(find_sec_key(29))
    pprint(BEAT_RANGE_DICT)
    print(find_beat_key(2))
