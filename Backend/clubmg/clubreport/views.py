# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import os
import copy
import datetime
import collections
import logging

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from clubserver.models import (
    RptHits, RptScores, RptServerecord, WorldRanking, OlympicRanking, AthleteInfo,
    MyJuli, MyZb, MyDistance, MatchInfo, RptGoalrecord
)

from common.utils import (
    return_code, get_zone_list, get_video_url
)

from common.resource import get_resource_by_user

from common.pub_map import (
    get_match_type,
)

from common.aws_s3 import get_aws_s3_obj_url, s3_report_client
from common.pub_map import (
    ZONE_NAME_MAP, ZONE_LIST_A, ZONE_LIST_B, ZONE_LIST, FAULT_LIST, ACTION_MAP,
    FULL_GAME_LIST, LINE_MPA, TIME_TABLE_DATA, BEAT_TABLE_DATA, TYPE_TABLE_DATA, 
    SINGLE_PLAYER, DOUBLE_PLAYER, SERVE_ZONE, SERVE_ZONE_LEFT, SERVE_ZONE_RIGHT,
    DOUBLE_END_ZONE_LIST, find_sec_key, find_beat_key, find_type_key, get_score_type,
    SPEED_DATA, find_speed_key, find_shot_key,
    SERVERECORD_DATA,
    ACTION_SCORE_ZONE, WINSCORE_DATA
)

from common.modelquery import (
    model_query, model_query_get, model_query_first, model_query_column_list
)

from middleware.apilogging import apiLogger

# Create your views here.

def ranking_change(ranking_this_time, ranking_last_time):
    diff = int(ranking_this_time) - int(ranking_last_time)
    if diff > 0:
        return u"降"
    elif diff < 0:
        return u"升"
    else:
        return u"-"

class WorldRankingReportView(APIView):

    def get(self, request):
        datas = {
            "table": {},
            "chart": {},
        }
        # 所有日期并集
        date_set = set()
        match_type = get_match_type(
            request.GET.get("match_type", '').strip()
        )

        datas["table"][match_type[1]] = []
        datas["chart"][match_type[1]] = {}
        rank_this = WorldRanking.objects.filter(
            match_type = match_type[0]
        ).order_by("-announcemented_at")[:1]
        if rank_this:
            announcemented_at = rank_this[0].announcemented_at
        else:
            return Response(return_code(0, data=datas))
        # 获取绑定的运动员
        athlete = get_resource_by_user(request, 'athlete')
        athlete_ids = athlete.values_list('athlete_id', flat=True)
        # 表格显示前10名
        ranks = WorldRanking.objects.filter(
            match_type = match_type[0],
            announcemented_at= announcemented_at
        ).order_by("ranking")[:10]
        for rank in ranks:
            if not set(rank.athlete_id.split()) & set(athlete_ids):
                continue
            # 计算运动员世界排名变化
            rank_last = WorldRanking.objects.filter(
                match_type = rank.match_type,
                athlete_id = rank.athlete_id,
                announcemented_at__lt = rank.announcemented_at
            ).order_by("-announcemented_at")[:1]
            rank_info = {
                "match_type": match_type[1],
                "athlete_id": rank.athlete_id,
                "athlete": rank.athlete,
                "ranking_this_time": rank.ranking,
                "ranking_last_time": u"-",
                "ranking_change": u"-"
            }
            if rank_last:
                rank_info["ranking_last_time"] = rank_last[0].ranking
                rank_info["ranking_change"] = ranking_change(
                    rank.ranking, rank_last[0].ranking
                )
            datas["table"][match_type[1]].append(rank_info)
            # 运动员最近 1 年世界排名数据
            rank_last_year = WorldRanking.objects.filter(
                match_type = rank.match_type,
                athlete_id = rank.athlete_id,
                announcemented_at__gte = (
                    datetime.datetime.now() + 
                    datetime.timedelta(days=-365))
            ).order_by('announcemented_at')
            datas["chart"][match_type[1]][rank.athlete_id] = {
                "name": rank.athlete,
                "rank": {},
                "items": [],
                "date": []
            }
            for rank in rank_last_year:
                datas["chart"][match_type[1]][rank.athlete_id]["rank"][rank.announcemented_at.strftime("%Y-%m-%d")] = rank.ranking
                date_set.add(rank.announcemented_at.strftime("%Y-%m-%d"))

            # 横坐标日期列表
            date_list = list(date_set)
            date_list.sort()

            for ath in datas['chart'][match_type[1]]:
                datas['chart'][match_type[1]][ath]["date"] = date_list
                for date in date_list:
                    datas['chart'][match_type[1]][ath]["items"].append(
                        datas['chart'][match_type[1]][ath]["rank"].get(date, 20)
                    )

        return Response(return_code(0, data=datas))


class AthleteRankingReportView(APIView):
    
    def get(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)

        data = collections.OrderedDict((
            ('id', athlete.id),
            ('athlete_id', athlete.athlete_id),
            ('name', athlete.name),
            ('world_ranking', '-'),
            ('olympic_ranking', '-'),
            ('chart', collections.OrderedDict((
                    ('world_ranking', {'date': [], 'items': []}),
                    ('olympic_ranking', {'date': [], 'items': []}),
                ))
            )
        ))

        query_set = collections.OrderedDict()
        match_type = get_match_type(athlete.sport_project)
        query_set['match_type'] = match_type[0]
        query_set['athlete_id__icontains'] = athlete.athlete_id
        query_set['announcemented_at__gte'] = (datetime.datetime.now() + 
            datetime.timedelta(days=-365))

        world_rankings = WorldRanking.objects.filter(
            **query_set
        ).order_by('announcemented_at').all()
        olympic_rankings = OlympicRanking.objects.filter(
            **query_set
        ).order_by('announcemented_at').all()
        for rank in world_rankings:
            data['chart']['world_ranking']['date'].append(rank.announcemented_at)
            data['chart']['world_ranking']['items'].append(rank.ranking)
        for rank in  olympic_rankings:
            data['chart']['olympic_ranking']['date'].append(rank.announcemented_at)
            data['chart']['olympic_ranking']['items'].append(rank.ranking)

        if data['chart']['world_ranking']['items']:
            data['world_ranking'] = data['chart']['world_ranking']['items'][-1]
        if data['chart']['olympic_ranking']['items']:
            data['olympic_ranking'] = data['chart']['olympic_ranking']['items'][-1]

        return Response(return_code(0, data=data))

class OlympicRankingReportView(APIView):

    def get(self, request):
        datas = {
            "table": {},
            "chart": {},
        }
        # 所有日期并集 
        date_set = set()
        match_type = get_match_type(
            request.GET.get("match_type", '').strip()
        )

        datas["table"][match_type[1]] = []
        datas["chart"][match_type[1]] = {}

        rank_this = OlympicRanking.objects.filter(
            match_type = match_type[0]
        ).order_by("-announcemented_at")[:1]
        if rank_this:
            announcemented_at = rank_this[0].announcemented_at
        else:
            return Response(return_code(0, data=datas))
        # 获取绑定的运动员
        athlete = get_resource_by_user(request, 'athlete')
        athlete_ids = athlete.values_list('athlete_id', flat=True)
        # 表格显示前10名
        ranks = OlympicRanking.objects.filter(
            match_type = match_type[0],
            announcemented_at= announcemented_at
        ).order_by("ranking")[:10]
        for rank in ranks:
            if not set(rank.athlete_id.split()) & set(athlete_ids):
                continue
            # 计算运动员奥林匹克排名变化
            rank_last = OlympicRanking.objects.filter(
                match_type = rank.match_type,
                athlete_id = rank.athlete_id,
                announcemented_at__lt = rank.announcemented_at
            ).order_by("-announcemented_at")[:1]
            rank_info = {
                "match_type": match_type[1],
                "athlete_id": rank.athlete_id,
                "athlete": rank.athlete,
                "ranking_this_time": rank.ranking,
                "ranking_last_time": u"-",
                "ranking_change": u"-"
            }
            if rank_last:
                rank_info["ranking_last_time"] = rank_last[0].ranking
                rank_info["ranking_change"] = ranking_change(
                    rank.ranking, rank_last[0].ranking
                )
            datas["table"][match_type[1]].append(rank_info)
            # 运动员最近 1 年奥林匹克排名数据
            rank_last_year = OlympicRanking.objects.filter(
                match_type = rank.match_type,
                athlete_id = rank.athlete_id,
                announcemented_at__gte = (
                    datetime.datetime.now() + 
                    datetime.timedelta(days=-365))
            ).order_by('announcemented_at')
            datas["chart"][match_type[1]][rank.athlete_id] = {
                "name": rank.athlete,
                "rank": {},
                "items": [],
                "date": [],
            }
            for rank in rank_last_year:
                datas["chart"][match_type[1]][rank.athlete_id]["rank"][rank.announcemented_at.strftime("%Y-%m-%d")] = rank.ranking
                date_set.add(rank.announcemented_at.strftime("%Y-%m-%d"))
            # 横坐标日期列表
            date_list = list(date_set)
            date_list.sort()

            for ath in datas['chart'][match_type[1]]:
                datas['chart'][match_type[1]][ath]["date"] = date_list
                for date in date_list:
                    datas['chart'][match_type[1]][ath]["items"].append(
                        datas['chart'][match_type[1]][ath]["rank"].get(date, 20)
                    )

        return Response(return_code(0, data=datas))
        

class MatchHitsSumView(APIView):
    def get(self, request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        if "match_id" in request.GET and request.GET["match_id"]:
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if "player" in request.GET and request.GET["player"]:
            player = request.GET["player"]
            if player not in ['a', 'b']:
                errors["game"].append(u"运动员取值范围: ['a', 'b']")
        else:
            player = "all"

        if "game" in request.GET and request.GET["game"]:
            try:
                game = int(request.GET["game"])
                if game not in FULL_GAME_LIST:
                    errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
            except Exception as e:
                errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
        else:
            game = 0

        if "action" in request.GET and request.GET["action"]:
            try:
                action = int(request.GET["action"])
                if action in ACTION_MAP:
                    query_set["action"] = ACTION_MAP[action]
            except Exception as e:
                errors["action"].append(u"动作取值范围: {}".format(ACTION_MAP))

        if "line" in request.GET and request.GET["line"]:
            try:
                line = int(request.GET["line"])
                if line not in LINE_MPA:
                    errors["line"].append(u"线路取值范围: {}".format(LINE_MPA))
            except Exception as e:
                errors["line"].append(u"参数必须为整数")
        else:
            line = 0

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        if game:
            rpt_scores = RptScores.objects.filter(
                matchid = query_set["matchid"],
                game = game
            ).order_by("frame_start").order_by("frame_end").values_list("frame_start", "frame_end")

            rpt_scores = list(rpt_scores)

            if rpt_scores:
                query_set["frame_hit__gte"] = rpt_scores[0][0]
                query_set["frame_hit__lte"] = rpt_scores[-1][1]
        
        data = collections.OrderedDict(
            (
                ('a', collections.OrderedDict(
                    (
                        (
                            ("start_zone_sum", {"all": 0, "data": []}),
                            ("end_zone_sum", {"all": 0, "data": []}),
                        )
                    )
                )),
                ('b', collections.OrderedDict(
                    (
                        ("start_zone_sum", {"all": 0, "data": []}),
                        ("end_zone_sum", {"all": 0, "data": []}),
                    )
                )),
            )
        )

        start_zone_dict = collections.OrderedDict(
            (
                ('a', collections.defaultdict(int)),
                ('b', collections.defaultdict(int)),
            )
        )
        start_zone_dict['a']["all"] = 0
        start_zone_dict['b']["all"] = 0
        end_zone_dict = collections.OrderedDict(
            (
                ('a', collections.defaultdict(int)),
                ('b', collections.defaultdict(int)),
            )
        )
        end_zone_dict['a']["all"] = 0
        end_zone_dict['b']["all"] = 0

        if player == 'a' or player == 'all':
            rpt_hits_a = RptHits.objects.filter(player__startswith = 'a').filter(
                **query_set
            ).order_by('zone_start').order_by('zone_end').all()

        if player == 'b' or player == 'all':
            rpt_hits_b = RptHits.objects.filter(player__startswith = 'b').filter(
                **query_set
            ).order_by('zone_start').order_by('zone_end').all()

        if player == 'a' or player == 'all':
            frame_prev_list_a = set([-1])
            for hit in rpt_hits_a:


                # player a 击球数量
                if hit.zone_start in ZONE_LIST_A and \
                    hit.zone_end in ZONE_LIST_B:

                    # 判断羽毛球线路是否符合查询条件
                    if line == 1 or line == 2:
                        zone_list = get_zone_list(hit.zone_start, line)
                        if hit.zone_end not in zone_list:
                            continue

                    start_zone_dict['a'][hit.zone_start] += 1
                    start_zone_dict['a']["all"] += 1
                    
                    frame_prev_list_a.add(hit.frame_prev)

                # player a 击球数量(交换场地)
                elif hit.zone_start in ZONE_LIST_B and \
                    hit.zone_end in ZONE_LIST_A:

                    # 判断羽毛球线路是否符合查询条件
                    if line == 1 or line == 2:
                        zone_list = get_zone_list(hit.zone_start, line)
                        if hit.zone_end not in zone_list:
                            continue

                    start_zone_dict['a'][-hit.zone_start] += 1
                    start_zone_dict['a']["all"] += 1

                    frame_prev_list_a.add(hit.frame_prev)

            # 根据 frame_prev_list_a 过滤对阵运动员击球帧记录
            frame_prev_list = list(frame_prev_list_a)
            rpt_hits_b_a = RptHits.objects.filter(
                matchid = query_set["matchid"],
                player__startswith = 'b'
            ).filter(
                frame_hit__in = frame_prev_list
            ).all()

            for hit in rpt_hits_b_a:
                if hit.zone_end in ZONE_LIST_A:
                     end_zone_dict['a'][hit.zone_end] += 1
                elif hit.zone_end in ZONE_LIST_B:
                     end_zone_dict['a'][-hit.zone_end] += 1
                end_zone_dict['a']["all"] += 1

        if player == 'b' or player == 'all':
            frame_prev_list_b = set([-1])
            for hit in rpt_hits_b:
                # player b 击球数量
                if hit.zone_start in ZONE_LIST_B and \
                    hit.zone_end in ZONE_LIST_A:

                    # 计算羽毛球线路落地点区域列表 get_zone_list 
                    if line == 1 or line == 2:
                        zone_list = get_zone_list(hit.zone_start, line)
                        if hit.zone_end not in zone_list:
                            continue

                    start_zone_dict['b'][hit.zone_start] += 1
                    start_zone_dict['b']["all"] += 1

                    frame_prev_list_b.add(hit.frame_prev)

                # player b 击球数量(交换场地)
                elif hit.zone_start in ZONE_LIST_A and \
                    hit.zone_end in ZONE_LIST_B:

                    # 计算羽毛球线路落地点区域列表 get_zone_list 
                    if line == 1 or line == 2:
                        zone_list = get_zone_list(hit.zone_start, line)
                        if hit.zone_end not in zone_list:
                            continue

                    start_zone_dict['b'][-hit.zone_start] += 1
                    start_zone_dict['b']["all"] += 1

                    frame_prev_list_b.add(hit.frame_prev)

            # 根据 frame_prev_list_b 过滤对阵运动员击球帧记录
            frame_prev_list = list(frame_prev_list_b)
            rpt_hits_a_b = RptHits.objects.filter(
                matchid = query_set["matchid"],
                player__startswith = 'a'
            ).filter(
                frame_hit__in = frame_prev_list
            ).all()

            for hit in rpt_hits_a_b:
                if hit.zone_end in ZONE_LIST_A:
                     end_zone_dict['b'][hit.zone_end] += 1
                elif hit.zone_end in ZONE_LIST_B:
                     end_zone_dict['b'][-hit.zone_end] += 1
                end_zone_dict['b']["all"] += 1

        for _player in start_zone_dict:
            start_zone_all = start_zone_dict[_player].pop("all")
            data[_player]["start_zone_sum"]["all"] = start_zone_all
            for _zone in start_zone_dict[_player]:
                data[_player]["start_zone_sum"]["data"].append(
                    collections.OrderedDict((
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("sum", start_zone_dict[_player][_zone])
                    ))
                )

        for _player in end_zone_dict:
            end_zone_all = end_zone_dict[_player].pop("all")
            data[_player]["end_zone_sum"]["all"] = end_zone_all
            for _zone in end_zone_dict[_player]:
                data[_player]["end_zone_sum"]["data"].append(
                    collections.OrderedDict((
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("sum", end_zone_dict[_player][_zone])
                    ))
                )

        return Response(return_code(0, data=data))

class MatchHitsView(APIView):
    def get(self ,request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        # 参数验证&设置默认值
        if request.GET.get("match_id", '').strip():
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")
        if request.GET.get("player", '').strip():
            query_set["player__startswith"] = request.GET["player"]
        else:
            query_set["player__startswith"] = 'a'
        if request.GET.get("game"):
            try:
                game = int(request.GET["game"])
                if game not in FULL_GAME_LIST:
                    errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
            except Exception as e:
                errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
        else:
            game = 0
        if request.GET.get("zone"):
            try:
                zone = int(request.GET["zone"])
                if zone not in ZONE_LIST:
                    errors["zone"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
            except Exception as e:
                errors["zone"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
        else:
            zone = 1

        if request.GET.get("action", '').strip():
            try:
                action = int(request.GET["action"])
                if action in ACTION_MAP:
                    query_set["action"] = ACTION_MAP[action]
            except Exception as e:
                errors["action"].append(u"动作取值范围: {}".format(ACTION_MAP))

        if request.GET.get("line"):
            try:
                line = int(request.GET["line"])
                if line not in LINE_MPA:
                    errors["line"].append(u"线路取值范围: {}".format(LINE_MPA))
            except Exception as e:
                errors["line"].append(u"线路取值范围: {}".format(LINE_MPA))
        else:
            line = 0

        # 来球区域参数 zone_start 表示对手的起始区域
        if request.GET.get("zone_start"):
            try:
                zone_start = int(request.GET["zone_start"])
                if zone_start not in ZONE_LIST:
                    errors["zone_start"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
            except Exception as e:
                errors["zone_start"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
        else:
            zone_start = None

        # 落球区域参数 zone_end 表示自己击球的落地区域
        if request.GET.get("zone_end"):
            try:
                zone_end = int(request.GET["zone_end"])
                if zone_end not in ZONE_LIST:
                    errors["zone_end"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
            except Exception as e:
                errors["zone_end"].append(u"区域取值不在范围: {}".format(ZONE_LIST))
        else:
            zone_end = None


        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        # 计算场次
        if game:
            rpt_scores = RptScores.objects.filter(
                matchid = query_set["matchid"],
                game = game
            ).order_by("frame_start").order_by("frame_end").values_list("frame_start", "frame_end")
            rpt_scores = list(rpt_scores)
            if rpt_scores:
                query_set["frame_hit__gte"] = rpt_scores[0][0]
                query_set["frame_hit__lte"] = rpt_scores[-1][1]

        # 计算羽毛球线路落地点区域列表 get_zone_list 
        if line == 1 or line == 2:
            zone_list = get_zone_list(zone, line)
        else: # 所有线路
            if zone in ZONE_LIST_A:
                zone_list = ZONE_LIST_B
            elif zone in ZONE_LIST_B:
                zone_list = ZONE_LIST_A

        # 根据 zone 来规范 zone_start 和 zone_end 正负
        if zone_start:
            if zone > 0:
                zone_start = -abs(zone_start)
            elif zone < 0:
                zone_start = abs(zone_start)
        if zone_end:
            if zone > 0:
                zone_end = -abs(zone_end)
            elif zone < 0:
                zone_end = abs(zone_end)

        # 指定击球落地区域
        if zone_end:
            zone_list = [zone_end]

        # Player one (此处 one 代表查询运动员)
        rpt_hits_one = RptHits.objects.filter(
            **query_set
        ).filter(
            Q(zone_start = zone) & Q(zone_end__in = zone_list) | 
            Q(zone_start = -zone) & Q(zone_end__in = [-x for x in zone_list]) | 
            Q(zone_end__in = FAULT_LIST) & Q(zone_start__in = (zone, -zone))
        )

        # frame_prev 所有查询运动员击球记录的前一帧，即对手击球帧
        frame_prev_list = set([-1])
        for hit in rpt_hits_one:
            if hit.zone_end not in FAULT_LIST:
                frame_prev_list.add(hit.frame_prev)

        # 根据 frame_prev_list 过滤对阵运动员击球帧记录
        frame_prev_list = list(frame_prev_list)
        rpt_hits_two = RptHits.objects.filter(
            matchid = query_set["matchid"]
        ).filter(
            ~Q(player__startswith = query_set["player__startswith"])
        ).filter(frame_hit__in = frame_prev_list)
    
        # 来球区域参数 zone_start 表示对手的起始区域    
        if zone_start:
            rpt_hits_two = rpt_hits_two.filter(
                Q(zone_start = zone_start) |
                Q(zone_start = -zone_start)
            )
            frame_next_list = set([-1])
            for hit in rpt_hits_two:
                frame_next_list.add(hit.frame_next)
            # 根据来球区域参数再次过滤 Player one 击球统计
            rpt_hits_one = rpt_hits_one.filter(
                frame_hit__in = list(frame_next_list)
            )
        rpt_hits_one = rpt_hits_one.order_by("frame_hit").all()
        rpt_hits_two = rpt_hits_two.all()
        
        data = collections.OrderedDict(
            (
                ("start_zone_per", {"all": 0, "data": []}),
                ("end_zone_per", {"all": 0, "data": []}),
                ("start_zone_action", {"all": 0, "data": []}),
                ("end_zone_action", {"all": 0, "data": []}),
                ("fault", {"all": 0, "data": []}),
                ("video_list", [])
            )
        )

        #if not rpt_hits_one or not rpt_hits_two:
        #    return Response(return_code(0, data=data))

        # 在赛场区域(比如区域 1)击球, 落点区域分布统计字典
        start_zone_dict = collections.defaultdict(int)
        start_zone_dict["all"] = 0
        # 在赛场区域(比如区域 1), 对手击球区域(来球区域)分布统计字典
        end_zone_dict = collections.defaultdict(int)
        end_zone_dict["all"] = 0
        # 在赛场区域(比如区域 1)击球动作的统计
        start_zone_action = collections.defaultdict(int)
        start_zone_action["all"] = 0
        # 在赛场区域(比如区域 1), 对手击球落到这个区域时的动作统计
        end_zone_action = collections.defaultdict(int)
        end_zone_action["all"] = 0
        # 在赛场区域(比如区域 1), 击球失误的统计
        fault = collections.defaultdict(int)
        fault["all"] = 0

        for hit in rpt_hits_one:
            if hit.zone_start == zone:
                if hit.zone_end in zone_list:
                    # 击球落点区域分布
                    start_zone_dict[hit.zone_end] += 1
                    # 起点击球动作
                    start_zone_action[hit.action] += 1
                    start_zone_action["all"] += 1

                    # 击球视频帧
                    if hit.video:
                        data["video_list"].append(
                            collections.OrderedDict(
                                (
                                    ("video", os.path.basename(hit.video)),
                                    ("url", get_video_url(hit.video)),
                                    ("is_comment", hit.is_comment)
                                )
                            )
                        )

                    start_zone_dict["all"] += 1

                # 击球失误统计
                if hit.zone_end in FAULT_LIST:
                    fault[hit.zone_end] += 1
                    fault["all"] += 1

            elif hit.zone_start == -zone:
                if hit.zone_end in [-x for x in zone_list]:
                    # 击球落点区域分布(交换场地)
                    start_zone_dict[-hit.zone_end] += 1
                    # 起点击球动作(交换场地)
                    start_zone_action[hit.action] += 1
                    start_zone_action["all"] += 1

                    # 击球视频帧
                    if hit.video:
                        data["video_list"].append(
                            collections.OrderedDict(
                                (
                                    ("video", os.path.basename(hit.video)),
                                    ("url", get_video_url(hit.video)),
                                    ("is_comment", hit.is_comment)
                                )
                            )
                        )

                    start_zone_dict["all"] += 1

                # 击球失误统计
                if hit.zone_end in FAULT_LIST:
                    fault[hit.zone_end] += 1
                    fault["all"] += 1

        for hit in rpt_hits_two:
            if hit.zone_end == zone:
                # 对手击球区域分布(相当于自己来说是来球区域分布)
                end_zone_dict[hit.zone_start] += 1
            elif hit.zone_end == -zone:
                # 对手击球区域分布(相当于自己来说是来球区域分布)
                end_zone_dict[-hit.zone_start] += 1

            # 对手击球动作
            end_zone_action[hit.action] += 1
            end_zone_action["all"] += 1
            end_zone_dict["all"] += 1

        start_zone_all = start_zone_dict.pop("all")
        data["start_zone_per"]["all"] = start_zone_all
        _data_list_len = len(start_zone_dict)
        _percent_total = 0
        for _zone in start_zone_dict:
            percent = round(start_zone_dict[_zone] / start_zone_all, 3) * 100
            if _data_list_len == 1:
                if _percent_total + percent > 100:
                    percent = 100 - _percent_total
                data["start_zone_per"]["data"].append(collections.OrderedDict(
                    (
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("percent", "{}%".format(percent)),
                        ("count", start_zone_dict[_zone])
                    )
                ))
            else:
                _percent_total += percent
                data["start_zone_per"]["data"].append(collections.OrderedDict(
                    (
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("percent", "{}%".format(percent)),
                        ("count", start_zone_dict[_zone])
                    )
                ))
            _data_list_len -= 1

        end_zone_all = end_zone_dict.pop("all")
        data["end_zone_per"]["all"] = end_zone_all
        _data_list_len = len(end_zone_dict)
        _percent_total = 0
        for _zone in end_zone_dict:
            percent = round(end_zone_dict[_zone] / end_zone_all, 3) * 100
            if _data_list_len == 1:
                if _percent_total + percent > 100:
                    percent = 100 - _percent_total
                data["end_zone_per"]["data"].append(collections.OrderedDict(
                    (
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("percent", "{}%".format(percent)),
                        ("count", end_zone_dict[_zone])
                    )
                ))
            else:
                _percent_total += percent
                data["end_zone_per"]["data"].append(collections.OrderedDict(
                    (
                        ("zone", _zone),
                        ("name", ZONE_NAME_MAP[_zone]),
                        ("percent", "{}%".format(percent)),
                        ("count", end_zone_dict[_zone])
                    )
                ))
            _data_list_len -= 1
        
        data["start_zone_action"]["all"] = start_zone_action.pop("all")
        for _action in start_zone_action:
            data["start_zone_action"]["data"].append(collections.OrderedDict(
                (
                    ("name", _action),
                    ("value", start_zone_action[_action])
                )
            ))

        data["end_zone_action"]["all"] = end_zone_action.pop("all")
        for _action in end_zone_action:
            data["end_zone_action"]["data"].append(collections.OrderedDict(
                (
                    ("name", _action),
                    ("value", end_zone_action[_action])
                )
            ))

        data["fault"]["all"] = fault.pop("all")
        for _fault in fault:
            data["fault"]["data"].append(collections.OrderedDict(
                (
                    ("zone_start", _fault),
                    ("name", ZONE_NAME_MAP[_fault]),
                    ("value", fault[_fault])
                )
            ))

        return Response(return_code(0, data=data))

class DoubleMatchServeView(APIView):

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)
        
        # 参数验证&设置默认值
        if request.GET.get("match_id", '').strip():
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")
        player = request.GET.get("player", 'a').strip()
        if player in DOUBLE_PLAYER:
            query_set["serve"] = player
        elif player in SINGLE_PLAYER:
            query_set["serve__startswith"] = player
        else:
            query_set["serve__startswith"] = 'a'

        game = request.GET.get("game", 1)
        try:
            game = int(game)
        except Exception as e:
            game = 1
        if game not in FULL_GAME_LIST:
            game = 1
        if game != 0:
            query_set["game"] = game

        start_zone = request.GET.get("start_zone", 'left')
        if start_zone == 'left':
            query_set['hit__in'] = SERVE_ZONE_LEFT
        elif start_zone == 'right':
            query_set['hit__in'] = SERVE_ZONE_RIGHT
        
        end_zone = request.GET.get("end_zone", '')
        try:
            end_zone = int(end_zone)
            if end_zone in DOUBLE_END_ZONE_LIST:
                query_set['land__endswith'] = end_zone
            elif end_zone in FAULT_LIST:
                query_set['land'] = end_zone
        except Exception as e:
            pass
        

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        data = {
            'left': 0,
            'right': 0,
            'fault': {},
            'end_zone': {
                'left': {},
                'right': {}
            },
            'video_list': []
        }

        for zone in DOUBLE_END_ZONE_LIST:
            data['end_zone']['left'][zone] = 0
            data['end_zone']['right'][zone] = 0
        for fault in FAULT_LIST:
            data['fault'][fault] = 0

        serves = RptServerecord.objects.filter(**query_set).order_by('score').all()

        for serve in serves:
            if serve.hit in SERVE_ZONE_LEFT:
                data['left'] += 1
            elif serve.hit in SERVE_ZONE_RIGHT:
                data['right'] += 1
            land_zone_position = serve.land // 10
            land_zone = serve.land % 10
            if serve.land in FAULT_LIST:
                data['fault'][serve.land] += 1
            elif land_zone_position in SERVE_ZONE_LEFT:
                data['end_zone']['left'][land_zone] += 1
            elif land_zone_position in SERVE_ZONE_RIGHT:
                data['end_zone']['right'][land_zone] += 1
            if serve.video_url:
                data['video_list'].append(
                    {
                        "video": os.path.basename(serve.video_url),
                        "url": get_video_url(serve.video_url),
                        "is_comment": serve.is_comment
                    }
                )

        return Response(return_code(0, data=data))


class MatchStart5BeatReportView(APIView):

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)
        
        # 参数验证&设置默认值
        if request.GET.get("match_id", '').strip():
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")
        player = request.GET.get("player", 'a1').strip()
        player = player if player in DOUBLE_PLAYER else 'a1'

        game = request.GET.get("game", 1)
        try:
            game = int(game)
        except Exception as e:
            game = 1
        if game not in FULL_GAME_LIST:
            game = 1
        if game != 0:
            query_set["game"] = game

        beat = request.GET.get('beat', 2)
        try:
            beat = int(beat)
        except Exception as e:
            beat = 2
        if beat not in [2, 3, 4, 5]:
            beat = 2

        zone_start, zone_end = None, None
        try:
            _zone_start = int(request.GET.get("zone_start"))
        except:
            pass
        else:
            if _zone_start in ZONE_LIST:
                zone_start = abs(_zone_start)
        try:
            _zone_end = int(request.GET.get("zone_end"))
        except:
            pass
        else:
            if _zone_end in ZONE_LIST:
                zone_end = abs(_zone_end)
            
        data = {
            'zone_start': {},
            'zone_end': {},
            'video_list': []
        }

        for zone in ZONE_LIST_A:
            data['zone_start'][zone] = 0
            data['zone_end'][zone] = 0

        scores = RptScores.objects.filter(**query_set).order_by('game', 'score').all()
        
        for score in scores:
            hits = RptHits.objects.filter(
                matchid = query_set["matchid"],
                frame_hit__gte = score.frame_start,
                frame_hit__lte = score.frame_end
            )[beat-1:beat]

            for hit in hits:
                plus_zone_start = abs(hit.zone_start)
                plus_zone_end = abs(hit.zone_end)

                if hit.player != player:
                    continue

                if zone_start and plus_zone_start != zone_start:
                    continue

                if zone_end and plus_zone_end != zone_end:
                    continue

                if plus_zone_start in ZONE_LIST_A:
                    data['zone_start'][plus_zone_start] += 1

                if hit.zone_start in ZONE_LIST_A and \
                    hit.zone_end in ZONE_LIST_B or \
                    hit.zone_start in ZONE_LIST_B and \
                    hit.zone_end in ZONE_LIST_A:
                    data['zone_end'][plus_zone_end] += 1
                if hit.video:
                    data['video_list'].append(
                        {
                            "video": os.path.basename(hit.video),
                            "url": get_video_url(hit.video),
                            "is_comment": hit.is_comment
                        }
                    )
                
        return Response(return_code(0, data=data))

class MatchScoresReportView(APIView):

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)
        # 参数验证
        if request.GET.get("match_id", "").strip():
            query_set['matchid'] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if request.GET.get("game", "").strip():
            try:
                game = int(request.GET["game"])
                if game not in (1, 2, 3):
                    query_set["game"] = 1
                else:
                    query_set["game"] = game
            except Exception as e:
                query_set["game"] = 1
        else:
            query_set["game"] = 1

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        data = {
            "score_a": [],
            "score_b": [],
            "score_total": [],
            "score_a:b": ":"
        }

        scores = RptScores.objects.filter(
            **query_set).order_by("game").order_by("score").all()

        if not scores:
            return Response(return_code(0, data=data))

        for score in scores:
            data["score_a"].append(score.score_a)
            data["score_b"].append(score.score_b)
            data["score_total"].append(score.score)
        data["score_a:b"] = "{}:{}".format(
            data["score_a"][-1], data['score_b'][-1])

        return Response(return_code(0, data=data))
            

class MatchBeatsReportView(APIView):

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)
        # 参数验证
        if request.GET.get("match_id", "").strip():
            query_set['matchid'] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if request.GET.get("game", "").strip():
            try:
                game = int(request.GET["game"])
                if game not in FULL_GAME_LIST:
                    errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
            except Exception as e:
                errors["game"].append(u"场次取值范围: {}".format(FULL_GAME_LIST))
        else:
            game = 0

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        if game != 0:
            query_set["game"] = game
        
        data = {
            "beat_counts": [],
            "beat_pre": []
        }
        scores = RptScores.objects.filter(
            **query_set).order_by("game").order_by("score").all()

        # 统计没分击球数字典
        beat_counts_dict = collections.defaultdict(int)
        # 记录得分最大击球数
        max_beat_count = 0
        for score in scores:
            beat_count = RptHits.objects.filter(
                matchid = score.matchid,
                frame_hit__gte = score.frame_start,
                frame_hit__lte = score.frame_end
            ).count()
            if beat_count > 0:
                beat_counts_dict[beat_count - 1] += 1
                if beat_count - 1 > max_beat_count:
                    max_beat_count = beat_count - 1

        beat_count_list = range(1, max_beat_count+1)
        # 击球拍数总和
        beat_counts_sum = sum(beat_counts_dict.values())
        for beat in beat_count_list:
            data["beat_pre"].append(
                str(round(beat_counts_dict.get(beat, 0) / beat_counts_sum, 4) * 100) + "%"
            )
        data["beat_counts"] = beat_count_list
        
        return Response(return_code(0, data=data))


class MatchScoresReportTableView(APIView):

    def get(self, request):

        def beat_table(match_id):
            data = copy.deepcopy(BEAT_TABLE_DATA)
            for game in data:
                scores = RptScores.objects.filter(
                    matchid = match_id,
                    game=game).order_by("score").all()
                # 初始化本场运动员得分 0 
                score_a = score_b = 0
                for score in scores:
                    if score.is_mark_error:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，frame_start[{}] >= frame_end[{}]，标记错误".format(
                                match_id, game, score.score_a, score.score_b, score.frame_start, score.frame_end
                            )
                        )
                        continue
                    beat_count = RptHits.objects.filter(
                        matchid = score.matchid,
                        frame_hit__gte = score.frame_start,
                        frame_hit__lte = score.frame_end
                    ).count() - 1
                    if beat_count < 0:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，击球回合数为 0 ，标记错误".format(
                                match_id, game, score.score_a, score.score_b
                            )
                        )
                        continue
                    # 回合得分运动员
                    win_player = 'a' if score.score_a > score_a else 'b'
                    score_a, score_b = score.score_a, score.score_b
                    data[game][win_player][find_beat_key(beat_count)]['score'] += 1
                    data[game][win_player]['total']['score'] += 1
                    data[game]['total'] += 1

            for game in data:
                for player in data[game]:
                    if player == 'total':
                        continue
                    if data[game]['total'] > 0:
                        for beat in data[game][player]:
                            data[game][player][beat]['score_pre'] = "{}%".format(
                                round(data[game][player][beat]['score'] / data[game]['total'], 4) * 100
                            )
            return Response(return_code(0, data=data))

        def type_table(match_id):
            data = copy.deepcopy(TYPE_TABLE_DATA)

            for game in data:
                scores = RptScores.objects.filter(
                    matchid = match_id,
                    game=game).order_by("score").all()
                # 初始化本场运动员得分 0 
                score_a = score_b = 0
                for score in scores:
                    if score.is_mark_error:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，frame_start[{}] >= frame_end[{}]，标记错误".format(
                                match_id, game, score.score_a, score.score_b, score.frame_start, score.frame_end
                            )
                        )
                        continue
                    # 死球记录
                    dead_beat = RptHits.objects.filter(
                        matchid = score.matchid,
                        frame_hit__gte = score.frame_start,
                        frame_hit__lte = score.frame_end,
                        action = u"死球"
                    ).order_by('-frame_hit').first()
                    if not dead_beat:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，无死球记录，标记错误".format(
                                match_id, game, score.score_a, score.score_b
                            )
                        )
                        continue
                    # 回合得分运动员
                    win_player = 'a' if score.score_a > score_a else 'b'
                    score_a, score_b = score.score_a, score.score_b
                    score_type = find_type_key(dead_beat.zone_start, dead_beat.height)
                    if not score_type:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，死球记录 zone_start[{}] height[{}]，无法计算得分类型，标记错误".format(
                                match_id, game, score.score_a, score.score_b, dead_beat.zone_start, dead_beat.height
                            )
                        )
                        continue
                    data[game][win_player][score_type]['score'] += 1
                    data[game][win_player]['total']['score'] += 1
                    data[game]['total'] += 1

            for game in data:
                for player in data[game]:
                    if player == 'total':
                        continue
                    if data[game]['total'] > 0:
                        for score_type in data[game][player]:
                            data[game][player][score_type]['score_pre'] = "{}%".format(
                                round(data[game][player][score_type]['score'] / data[game]['total'], 4) * 100
                            )
            return Response(return_code(0, data=data))

        def time_table(match_id):
            data = copy.deepcopy(TIME_TABLE_DATA)

            for game in data:
                scores = RptScores.objects.filter(
                    matchid = match_id,
                    game=game).order_by("score").all()
                # 初始化本场运动员得分 0 
                score_a = score_b = 0
                for score in scores:
                    if score.is_mark_error:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，frame_start[{}] >= frame_end[{}]，标记错误".format(
                                match_id, game, score.score_a, score.score_b, score.frame_start, score.frame_end
                            )
                        )
                        continue
                    # 死球记录
                    dead_beat = RptHits.objects.filter(
                        matchid = score.matchid,
                        frame_hit__gte = score.frame_start,
                        frame_hit__lte = score.frame_end,
                        action = u"死球"
                    ).order_by('-frame_hit').first()

                    if not dead_beat:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，无死球记录，标记错误".format(
                                match_id, game, score.score_a, score.score_b
                            )
                        )
                        continue
                    score_type = get_score_type(dead_beat.zone_start, dead_beat.height)
                    if not score_type:
                        apiLogger.error(
                            "比赛 {} 第 {} 局，比分[{}:{}]，死球记录 zone_start[{}] height[{}]，无法计算得分类型，标记错误".format(
                                match_id, game, score.score_a, score.score_b, dead_beat.zone_start, dead_beat.height
                            )
                        )
                        continue
                    # 回合秒数
                    seconds = (score.frame_end - score.frame_start) / 24
                    # 回合得分运动员
                    win_player = 'a' if score.score_a > score_a else 'b'
                    score_a, score_b = score.score_a, score.score_b
                    data[game][win_player][find_sec_key(seconds)][score_type] += 1
                    data[game][win_player][find_sec_key(seconds)]['total'] += 1
                    data[game]['total'] += 1

            for game in data:
                for player in data[game]:
                    if player == 'total':
                        continue
                    for second in data[game][player]:
                        if data[game][player][second]['total'] > 0:
                            data[game][player][second]['score_pre'] = "{}%".format(
                                round(data[game][player][second]['total'] / data[game]['total'], 4) * 100
                            )
            return Response(return_code(0, data=data))

        TABLE_TYPE_MAP = {
            "beat": beat_table,
            "type": type_table,
            "time": time_table,
        }
    
        errors = collections.defaultdict(list)
        # 参数验证
        if request.GET.get("match_id", "").strip():
            match_id = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        table_type = request.GET.get("table_type", "").strip()

        return TABLE_TYPE_MAP.get(table_type, beat_table)(match_id)

class ScoreDetailsReportView(APIView):
    
    def get(self, request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        if "match_id" in request.GET and request.GET["match_id"]:
            query_set["matchid"] = request.GET["match_id"]
            match_id = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST) 

        if "game" in request.GET and request.GET["game"]:
            games = request.GET["game"].strip(',')
            games = [game.strip() for game in games.split(',')]
        else:
            games = [1]

        query_set["game__in"] = games

        match_julis = model_query(MyJuli, query=query_set, order_by=['game', 'score']).all()

        if not match_julis:
            return Response(return_code(0, data={}))


        data = collections.OrderedDict()
        for game in games:
            data[game] = collections.OrderedDict()

        #data/2018/0110/0000/routes/route_2018_0110_0000_1_01_00_01.png
        yy, mm, dd = match_id.split('_')
        for score in match_julis:
            s3_obj = "data/{}/{}/{}/routes/route_{}_{}_{}_{}_{}.png".format(
                yy,
                mm,
                dd,
                match_id,
                score.game,
                score.score.zfill(2),
                score.score_a.zfill(2),
                score.score_b.zfill(2)
            )
            data[str(score.game)][score.score] = {
                "score_a": score.score_a,
                "score_b": score.score_b,
                "goal": score.goal,
                "a_juli": score.a_juli,
                "b_juli": score.b_juli,
                "a_sudu": score.a_sudu,
                "b_sudu": score.b_sudu,
                "t": score.t,
                "shot": score.shot,
                "locus_p_url": get_aws_s3_obj_url(
                    s3_obj,
                    s3_client=s3_report_client,
                    bucket_name=settings.AWS_S3_R_BUCKET
                )
            }

        return Response(return_code(0, data=data))

class MatchDistanceReportView(APIView):

    def get(self, request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        if "match_id" in request.GET and request.GET["match_id"]:
            query_set["match_num"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST) 

        if "game" in request.GET and request.GET["game"]:
            games = request.GET["game"].strip(',')
            games = [game.strip() for game in games.split(',') if int(game.strip()) in FULL_GAME_LIST[1:]]
        else:
            games = ["1"]
        
        match_distance = model_query_first(MyDistance, query=query_set)
        if not match_distance:
            return Response(return_code(0, data={}))
            
        data = collections.OrderedDict()
        data = {
            "a": {
                "gt8": collections.defaultdict(float),
                "lt8": collections.defaultdict(float),
            },
            "b": {
                "gt8": collections.defaultdict(float),
                "lt8": collections.defaultdict(float),
            }
        }

        for game in games:
            data["a"]["gt8"]["ay"] += float(getattr(match_distance, "a{}y".format(game)))
            data["a"]["gt8"]["jq_ay"] += float(getattr(match_distance, "jq_a{}y".format(game)))
            data["a"]["gt8"]["jx_ay"] += float(getattr(match_distance, "jx_a{}y".format(game)) if hasattr(match_distance, "jx_a{}y".format(game)) else getattr(match_distance, "jq_xa{}y".format(game)))
            data["a"]["lt8"]["ax"] += float(getattr(match_distance, "a{}x".format(game)))
            data["a"]["lt8"]["jq_ax"] += float(getattr(match_distance, "jq_a{}x".format(game)))
            data["a"]["lt8"]["jx_ax"] += float(getattr(match_distance, "jx_a{}x".format(game)))
            data["b"]["gt8"]["by"] += float(getattr(match_distance, "b{}y".format(game)))
            data["b"]["gt8"]["jq_by"] += float(getattr(match_distance, "jq_b{}y".format(game)))
            data["b"]["gt8"]["jx_by"] += float(getattr(match_distance, "jx_b{}y".format(game)))
            data["b"]["lt8"]["bx"] += float(getattr(match_distance, "b{}x".format(game)))
            data["b"]["lt8"]["jq_bx"] += float(getattr(match_distance, "jq_b{}x".format(game)))
            data["b"]["lt8"]["jx_bx"] += float(getattr(match_distance, "jx_b{}x".format(game)))

        return Response(return_code(0, data=data))

class DistanceScoreReportView(APIView):

    def get(self, request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        if "match_id" in request.GET and request.GET["match_id"]:
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST) 

        if "game" in request.GET and request.GET["game"]:
            games = request.GET["game"].strip(',')
            games = [game.strip() for game in games.split(',')]
        else:
            games = ["1"]

        query_set["game__in"] = games

        match_julis = model_query(MyJuli, query=query_set, order_by=['game', 'score']).all()

        data = collections.OrderedDict()

        data = {
            "lt8": {
                "a": {
                    "score_a": 0,
                    "score_agtb": 0,
                    "score_altb": 0,
                    "agtb_d": 0.0,
                    "blta_d": 0.0,
                    "altb_d": 0.0,
                    "bgta_d": 0.0
                },
                "b": {
                    "score_b": 0,
                    "score_bgta": 0,
                    "score_blta": 0,
                    "bgta_d": 0.0,
                    "altb_d": 0.0,
                    "blta_d": 0.0,
                    "agtb_d": 0.0,
                }
            },
            "gt8": {
                "a": {
                    "score_a": 0,
                    "score_agtb": 0,
                    "score_altb": 0,
                    "agtb_d": 0.0,
                    "blta_d": 0.0,
                    "altb_d": 0.0,
                    "bgta_d": 0.0
                },
                "b": {
                    "score_b": 0,
                    "score_bgta": 0,
                    "score_blta": 0,
                    "bgta_d": 0.0,
                    "altb_d": 0.0,
                    "blta_d": 0.0,
                    "agtb_d": 0.0,
                }
            }
        }


        for score in match_julis:
            if int(score.shot) <= 8:
                if score.goal == "a":
                    data["lt8"]["a"]["score_a"] += 1
                    if score.a_juli >= score.b_juli:
                        data["lt8"]["a"]["score_agtb"] += 1
                        data["lt8"]["a"]["agtb_d"] += float(score.a_juli)
                        data["lt8"]["a"]["blta_d"] += float(score.b_juli)
                    else:
                        data["lt8"]["a"]["score_altb"] += 1
                        data["lt8"]["a"]["altb_d"] += float(score.a_juli)
                        data["lt8"]["a"]["bgta_d"] += float(score.b_juli)
                else:
                    data["lt8"]["b"]["score_b"] += 1
                    if score.b_juli >= score.a_juli:
                        data["lt8"]["b"]["score_bgta"] += 1
                        data["lt8"]["b"]["bgta_d"] += float(score.a_juli)
                        data["lt8"]["b"]["altb_d"] += float(score.b_juli)
                    else:
                        data["lt8"]["b"]["score_blta"] += 1
                        data["lt8"]["b"]["blta_d"] += float(score.a_juli)
                        data["lt8"]["b"]["agtb_d"] += float(score.b_juli)
            else:
                if score.goal == "a":
                    data["gt8"]["a"]["score_a"] += 1
                    if score.a_juli >= score.b_juli:
                        data["gt8"]["a"]["score_agtb"] += 1
                        data["gt8"]["a"]["agtb_d"] += float(score.a_juli)
                        data["gt8"]["a"]["blta_d"] += float(score.b_juli)
                    else:
                        data["gt8"]["a"]["score_altb"] += 1
                        data["gt8"]["a"]["altb_d"] += float(score.a_juli)
                        data["gt8"]["a"]["bgta_d"] += float(score.b_juli)
                else:
                    data["gt8"]["b"]["score_b"] += 1
                    if score.b_juli >= score.a_juli:
                        data["gt8"]["b"]["score_bgta"] += 1
                        data["gt8"]["b"]["bgta_d"] += float(score.a_juli)
                        data["gt8"]["b"]["altb_d"] += float(score.b_juli)
                    else:
                        data["gt8"]["b"]["score_blta"] += 1
                        data["gt8"]["b"]["blta_d"] += float(score.a_juli)
                        data["gt8"]["b"]["agtb_d"] += float(score.b_juli)
        data["lt8"]["a"]["score_agtb_ret"] = "{} : 1".format(round(data["lt8"]["a"]["agtb_d"] / (data["lt8"]["a"]["blta_d"] or 1), 2))
        data["lt8"]["a"]["score_altb_ret"] = "{} : 1".format(round(data["lt8"]["a"]["altb_d"] / (data["lt8"]["a"]["bgta_d"] or 1), 2))
        data["lt8"]["b"]["score_bgta_reg"] = "{} : 1".format(round(data["lt8"]["b"]["bgta_d"] / (data["lt8"]["b"]["altb_d"] or 1), 2))
        data["lt8"]["b"]["score_blta_reg"] = "{} : 1".format(round(data["lt8"]["b"]["blta_d"] / (data["lt8"]["b"]["agtb_d"] or 1), 2))
        data["gt8"]["a"]["score_agtb_ret"] = "{} : 1".format(round(data["gt8"]["a"]["agtb_d"] / (data["gt8"]["a"]["blta_d"] or 1), 2))
        data["gt8"]["a"]["score_altb_ret"] = "{} : 1".format(round(data["gt8"]["a"]["altb_d"] / (data["gt8"]["a"]["bgta_d"] or 1), 2))
        data["gt8"]["b"]["score_bgta_reg"] = "{} : 1".format(round(data["gt8"]["b"]["bgta_d"] / (data["gt8"]["b"]["altb_d"] or 1), 2))
        data["gt8"]["b"]["score_blta_reg"] = "{} : 1".format(round(data["gt8"]["b"]["blta_d"] / (data["gt8"]["b"]["agtb_d"] or 1), 2))
        del data["lt8"]["a"]["agtb_d"]
        del data["lt8"]["a"]["blta_d"]
        del data["lt8"]["a"]["altb_d"]
        del data["lt8"]["a"]["bgta_d"]
        del data["lt8"]["b"]["bgta_d"]
        del data["lt8"]["b"]["altb_d"]
        del data["lt8"]["b"]["blta_d"]
        del data["lt8"]["b"]["agtb_d"]
        del data["gt8"]["a"]["agtb_d"]
        del data["gt8"]["a"]["blta_d"]
        del data["gt8"]["a"]["altb_d"]
        del data["gt8"]["a"]["bgta_d"]
        del data["gt8"]["b"]["bgta_d"]
        del data["gt8"]["b"]["altb_d"]
        del data["gt8"]["b"]["blta_d"]
        del data["gt8"]["b"]["agtb_d"]

        return Response(return_code(0, data=data))

class MatchSpeedReportView(APIView):

    def get(self, request):

        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        if "match_id" in request.GET and request.GET["match_id"]:
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST) 

        if "game" in request.GET and request.GET["game"]:
            games = request.GET["game"].strip(',')
            games = [game.strip() for game in games.split(',')]
        else:
            games = ["1"]

        query_set["game__in"] = games

        match_julis = model_query(MyJuli, query=query_set, order_by=['game', 'score']).all()

        data = copy.deepcopy(SPEED_DATA)

        total_score_a = 0
        total_score_b = 0
        
        for score in match_julis:
            shot = find_shot_key(score.shot)
            data[shot]["a"]["total_avg"].append(float(score.a_sudu))
            data[shot]["b"]["total_avg"].append(float(score.b_sudu))
            # 每一分记录 a, b 运动员速度是否有分布
            a_speed_set = set([])
            b_speed_set = set([])
            for speed_a in score.per_a.split(','):
                speed = find_speed_key(speed_a)
                data[shot]["a"][speed]['count'] += 1
                a_speed_set.add(speed)
            for speed_b in score.per_b.split(','):
                speed = find_speed_key(speed_b)
                data[shot]["b"][speed]['count'] += 1
                b_speed_set.add(speed)
            for speed in a_speed_set:
                data[shot]['a'][speed]['score'] += 1
            for speed in b_speed_set:
                data[shot]['b'][speed]['score'] += 1

        for shot in data:
            for player in data[shot]:
                for speed in data[shot][player]:
                    if speed == 'total_avg':
                        data[shot][player][speed] = round(sum(data[shot][player][speed]) / len(data[shot][player][speed]), 2)
                    else:
                        data[shot][player][speed] = 0.00 if data[shot][player][speed]['score'] == 0 else round(data[shot][player][speed]['count'] / data[shot][player][speed]['score'], 2)

        return Response(return_code(0, data=data))
        

class MatchServeReportView(APIView):
    """
    发球统计报表
    """

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)

        # 参数验证&设置默认值
        if request.GET.get("match_id", '').strip():
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        # 比赛
        match = model_query_get(MatchInfo, query={'match_id': query_set["matchid"]})

        # 运动员id
        player_a_id = match.player_a_id.strip().split()
        player_b_id = match.player_b_id.strip().split()

        # 运动员
        player = request.GET.get("player", 'a').strip()
        # 单打运动员为 a, b
        if match.match_type in (0, 1):
            query_set["serve"] = player if player in SINGLE_PLAYER else 'a'
            # 单打运动员id
            player_id = getattr(match, "player_{}_id".format(query_set["serve"]))
        # 单打运动员为 a, b, a1, a2, b1, b2
        else:
            if player in DOUBLE_PLAYER:
                query_set["serve"] = player
                # 双打运动员之一 id
                player_id = getattr(match, "player_{}_id".format(player[0]))
                player_id = player_id.strip().split()[int(player[1]) - 1]
            elif player in SINGLE_PLAYER:
                query_set["serve__startswith"] = player
                # 双打运动员2个运动员 id
                player_id = getattr(match, "player_{}_id".format(player))
            else:
                query_set["serve"] = 'a1'
                player_id = match.player_a_id.strip().split()[0]

        # 包含运动员的最近 10 场比赛
        match_last_10 = MatchInfo.objects.filter(
            Q(player_a_id__icontains = player_id) |
            Q(player_b_id__icontains = player_id)
        ).order_by('match_date').values_list(
            'match_id', flat=True
        )[:10]

        # 包含运动员A的所有比赛
        match_all = MatchInfo.objects.filter(
            Q(player_a_id__icontains = player_id) |
            Q(player_b_id__icontains = player_id)
        ).values_list(
            'match_id', flat=True
        ).all()

        # 所有当前比赛运动员对打比赛
        match_same_players = MatchInfo.objects.filter(
            Q(player_a_id = match.player_a_id) &
            Q(player_b_id = match.player_b_id) |
            Q(player_a_id = match.player_a_id) &
            Q(player_b_id = match.player_b_id)
        ).values_list(
            'match_id', flat=True
        )

        # 场次
        game = request.GET.get("game", 1)
        try:
            game = int(game)
        except Exception as e:
            game = 1
        if game not in FULL_GAME_LIST:
            game = 1
        if game != 0:
            query_set["game"] = game

        # 单双发球
        start_zone = request.GET.get("serve_type", 'single')
        if start_zone == 'single':
            query_set['hit__in'] = SERVE_ZONE_LEFT
        elif start_zone == 'double':
            query_set['hit__in'] = SERVE_ZONE_RIGHT

        data = copy.deepcopy(SERVERECORD_DATA)

        # 本场比赛统计
        serves = model_query(RptServerecord, query=query_set)

        for serve in serves:
            one, two = [int(num) for num in str(serve.land)]
            if one != 9:
                serve_end_zone = two
            else:
                serve_end_zone = serve.land
            data[serve_end_zone]['num'] += 1
            if serve.video_url:
                video = {
                    "video": os.path.basename(serve.video_url),
                    "url": get_video_url(serve.video_url),
                    "is_comment": serve.is_comment
                }
                data[serve_end_zone]['video_list'].append(video)

        def __make_data(serves):
            _data = collections.defaultdict(int)
            for serve in serves:
                one, two = [int(num) for num in str(serve.land)]
                if one != 9:
                    serve_end_zone = two
                else:
                    serve_end_zone = serve.land
                _data[serve_end_zone] += 1
            return _data

        def __cal_avg(listdata):
            if listdata:
                return round(
                    sum(listdata) / 
                    float(len(listdata)),
                    2
                )
            return 0.00
            
        # 最近10场平均值统计
        for match_id in match_last_10:
            query_set['matchid'] = match_id
            serves = model_query(RptServerecord, query=query_set)
            _data = __make_data(serves)
            for zone in _data:
                data[zone]['last_10_avg'].append(_data[zone])

        # 所有比赛平均值统计
        for match_id in match_all:
            query_set['matchid'] = match_id
            serves = model_query(RptServerecord, query=query_set)
            _data = __make_data(serves)
            for zone in _data:
                data[zone]['all_avg'].append(_data[zone])

        # 所有当前比赛运动员对抗的比赛平均值统计
        for match_id in match_same_players:
            query_set['matchid'] = match_id
            serves = model_query(RptServerecord, query=query_set)
            _data = __make_data(serves)
            for zone in _data:
                data[zone]['same_player_avg'].append(_data[zone])

        for zone in data:
            data[zone]['last_10_avg'] = __cal_avg(data[zone]['last_10_avg'])
            data[zone]['all_avg'] = __cal_avg(data[zone]['all_avg'])
            data[zone]['same_player_avg'] = __cal_avg(data[zone]['same_player_avg'])

        return Response(return_code(0, data=data))

class MatchWinScoreReportView(APIView):
    """
    得分统计报表接口
    主动得分
    对方失误被动得分
    """

    def get(self, request):
        query_set = collections.OrderedDict()
        errors = collections.defaultdict(list)

        # 参数验证&设置默认值
        if request.GET.get("match_id", '').strip():
            query_set["matchid"] = request.GET["match_id"]
        else:
            errors["match_id"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        # 场次
        game = request.GET.get("game", 1)
        try:
            game = int(game)
        except Exception as e:
            game = 1
        if game not in FULL_GAME_LIST:
            game = 1
        if game != 0:
            query_set["game"] = game

        # 比赛
        match = model_query_get(MatchInfo, query={'match_id': query_set["matchid"]})

        # 得分运动员
        goal = request.GET.get("goal", 'a').strip()
        # 单打运动员为 a, b
        if match.match_type in (0, 1):
            query_set["goal"] = goal if goal in SINGLE_PLAYER else 'a'
            # 单打运动员id
            player_id = getattr(match, "player_{}_id".format(query_set["goal"]))
        # 单打运动员为 a, b, a1, a2, b1, b2
        else:
            if goal in DOUBLE_PLAYER:
                query_set["goal"] = goal 
                # 双打运动员之一 id
                player_id = getattr(match, "player_{}_id".format(goal[0]))
                player_id = player_id.strip().split()[int(goal[1]) - 1]
            elif goal in SINGLE_PLAYER:
                query_set["goal__startswith"] = goal
                # 双打运动员2个运动员 id
                player_id = getattr(match, "player_{}_id".format(goal))
            else:
                query_set["goal"] = 'a1'
                player_id = match.player_a_id.strip().split()[0]

        # 包含运动员的最近 10 场比赛
        match_last_10 = MatchInfo.objects.filter(
            Q(player_a_id__icontains = player_id) |
            Q(player_b_id__icontains = player_id)
        ).order_by('match_date').values_list(
            'match_id', flat=True
        )[:10]

        # 包含运动员A的所有比赛
        match_all = MatchInfo.objects.filter(
            Q(player_a_id__icontains = player_id) |
            Q(player_b_id__icontains = player_id)
        ).values_list(
            'match_id', flat=True
        ).all()

        # 所有当前比赛运动员对打比赛
        match_same_players = MatchInfo.objects.filter(
            Q(player_a_id = match.player_a_id) &
            Q(player_b_id = match.player_b_id) |
            Q(player_a_id = match.player_b_id) &
            Q(player_b_id = match.player_a_id)
        ).values_list(
            'match_id', flat=True
        )
        
        data = copy.deepcopy(WINSCORE_DATA)

        # 当前比赛统计
        goalrecords = model_query(RptGoalrecord, query=query_set)

        for score in goalrecords:
            score_type = 'action_score' if score.land in ACTION_SCORE_ZONE else 'unaction_score'
            data[score_type]['num'] += 1
            if score.video_url:
                video = {
                    "video": os.path.basename(score.video_url),
                    "url": get_video_url(score.video_url),
                    "is_comment": score.is_comment
                }
                data[score_type]['video_list'].append(video)

        def __make_data(goalrecords):
            _data = collections.defaultdict(int)
            for score in goalrecords:
                score_type = 'action_score' if score.land in ACTION_SCORE_ZONE else 'unaction_score'
                _data[score_type] += 1
            return _data

        def __cal_avg(listdata):
            if listdata:
                return round(
                    sum(listdata) / 
                    float(len(listdata)),
                    2
                )
            return 0.00
            

        # 最近 10 场比赛统计
        for match_id in match_last_10:
            query_set['matchid'] = match_id
            goalrecords = model_query(RptGoalrecord, query=query_set)
            _data = __make_data(goalrecords)
            for score_type in _data:
                data[score_type]['last_10_avg'].append(_data[score_type])

        # 所有比赛平均值统计
        for match_id in match_all:
            query_set['matchid'] = match_id
            goalrecords = model_query(RptGoalrecord, query=query_set)
            _data = __make_data(goalrecords)
            for score_type in _data:
                data[score_type]['all_avg'].append(_data[score_type])

        # 所有当前比赛运动员对抗的比赛平均值统计
        for match_id in match_same_players:
            query_set['matchid'] = match_id
            goalrecords = model_query(RptGoalrecord, query=query_set)
            _data = __make_data(goalrecords)
            for score_type in _data:
                data[score_type]['same_player_avg'].append(_data[score_type])

        for score_type in data:
            data[score_type]['last_10_avg'] = __cal_avg(data[score_type]['last_10_avg'])
            data[score_type]['all_avg'] = __cal_avg(data[score_type]['all_avg'])
            data[score_type]['same_player_avg'] = __cal_avg(data[score_type]['same_player_avg'])

        return Response(return_code(0, data=data))



