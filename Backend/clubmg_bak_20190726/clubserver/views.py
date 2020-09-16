# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import os
import datetime
import collections
import json
import shutil

from django.conf import settings
from django.http import Http404
from django.utils.timezone import now
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult

from .models import (
    User, Group, UserGroup, Operation, GroupPermission, GroupResource,
    Permission, AthleteInfo, AthleteCompany, SportEventExp, MatchInfo, MarkMatchInfo,
    AthleteGroup, AthleteGroupLink, MatchVideos, WorldRanking, OlympicRanking, DocsData,
    PhysicalFitnessItems, PhysicalFitnessData, RptHits, RptScores, RptServerecord,
    RptPlaygroundrecord, VideoProcInfo, DocLink
)
from .serializers import (
    UserSerializer, UserAddSerializer, UserUpdatePhotoSerializer,
    UpdateUserSerializer, UserUpdateEmailSerializer,
    GroupSerializer, NewGroupSerializer, UpdateGroupSerializer,
    OperationSerializer, PermissionSerializer,
    AthleteInfoSerializer, UpdateAthleteInfoSerializer, NewAthleteInfoSerializer,
    NewAthleteCompanySerializer, AthleteCompanySerializer, UpdateAthleteCompanySerializer,
    SportEventExpSerializer, UpdateSportEventExpSerializer, NewSportEventExpSerializer,
    AthleteGroupSerializer, NewAthleteGroupSerializer, UpdateAthleteGroupSerializer,
    MatchInfoSerializer, NewMatchInfoSerializer, UpdateMatchInfoSerializer, MarkMatchInfoSerializer,
    RptHitsSerializer, RptScoresSerializer, RptServerecordSerializer, RptPlaygroundrecordSerializer,
    WorldRankingSerializer, NewWorldRankinSerializer, UpdateWorldRankinSerializer,
    OlympicRankingSerializer, NewOlympicRankingSerializer, UpdateOlympicRankingSerializer,
    PhysicalFitnessDataSerializer, NewPhysicalFitnessDataSerializer, UpdatePhysicalFitnessDataSerializer,
    DocLinkSerializer, NewDocLinkSerializer,
)
from common.utils import (
    CustomPageNumberPagination, return_code, lmd5sum, get_file_mtime, get_file_size,
    CeleryState, get_zone_list, calculate_age, get_resource_by_user
)
from common.pub_map import (
    MATCH_TYPE_DICT, get_match_type,
)
from common.aws_s3 import get_aws_s3_obj_url
from .tasks import scores_video_proc, hits_video_proc
from .doclinkopt import DocLinkOpt

# Create your views here.

class UserAdd(APIView):

    def put(self, request):
        user_s = UserAddSerializer(data = request.data)
        if not user_s.is_valid():
            return Response(return_code(2001, detail=user_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        username = request.data.get('username', '')
        password = request.data.get('password', '123456').strip()
        email = request.data.get('email', '')
        user_role = request.data.get('user_role', 1)
        user_type = request.data.get('user_type', 1)

        user = User()
        user.username = username
        user.set_password(password)
        user.email = email
        user.user_role = user_role
        user.user_type = user_type
        user.save()

        user = User.objects.get(pk=user.id)
        user_s = UserSerializer(user)

        return Response(return_code(0, data=user_s.data),
            status=status.HTTP_201_CREATED)

class EditUserView(APIView):

    def get(self, request, user_id, format=None):
        user = get_object_or_404(User, pk=user_id)
        user_ser = UserSerializer(instance=user)
        return Response(return_code(0, data=user_ser.data))

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user_ser = UpdateUserSerializer(user, data=request.data)
        if user_ser.is_valid():
            user_ser.update(user, request.data)
            user = get_object_or_404(User, pk=user_id)
            user_ser = UserSerializer(instance=user)
            return Response(return_code(0, data=user_ser.data))
        return Response(return_code(2001, detail=user_ser.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        try:
            with transaction.atomic():
                for group in user.group:
                    UserGroup.objects.filter(group_id = group['id']).delete()
                user.delete()
            return Response(return_code(0, msg="删除成功"))
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)


class UpdatePassword(APIView):

    def post(self, request):
        password = request.data.get('password', '')
        original_password = request.data.get('original_password', '')
        if not all((password, original_password)):
            return Response(return_code(2001, detail='密码不能为空'),
                status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(pk=request.user.id)
        if not check_password(original_password, user.password):
            return Response(return_code(701, detail="原始密码不正确"),
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response(return_code(0, msg='修改成功'))

class UpdateEmail(APIView):
    
    def post(self, request):
        user_ser = UserUpdateEmailSerializer(data=request.data)
        if user_ser.is_valid():
            user = get_object_or_404(User, pk=request.user.id)
            user_ser.update(user, request.data)
            user_ser = UserSerializer(instance=user)
            return Response(return_code(0, data=user_ser.data))
        return Response(return_code(2001, detail=user_ser.errors),
            status=status.HTTP_400_BAD_REQUEST)

class UpdatePhoto(APIView):
    
    def post(self, request):
        user_ser = UserUpdatePhotoSerializer(data=request.data)
        if user_ser.is_valid():
            user = get_object_or_404(User, pk=request.user.id)
            user_ser.update(user, request.data)
            user_ser = UserSerializer(instance=user)
            return Response(return_code(0, data=user_ser.data))
        return Response(return_code(2001, detail=user_ser.errors),
            status=status.HTTP_400_BAD_REQUEST)
        
class UserView(APIView):

    def get(self, request, format=None):
        user = get_object_or_404(User, pk=request.user.id)
        user_ser = UserSerializer(instance=user)
        return Response(return_code(0, data=user_ser.data))

class UsersView(APIView):

    def get(self, request):
        queryset = collections.OrderedDict()
        query_is = ['user_role', 'user_type']
        query_like = ['username']

        for q in query_is:
            if request.GET.get(q, '').strip():
                queryset[q] = request.GET[q].strip()
        for q in query_like:
            if request.GET.get(q, '').strip():
                queryset['{}__icontains'.format(q)] = request.GET[q].strip()

        users = User.objects.filter(**queryset).order_by('id').all()
        pg = CustomPageNumberPagination()
        page_users = pg.paginate_queryset(queryset=users, request=request, view=self)
        users_ser = UserSerializer(instance=page_users, many=True)
        return pg.get_paginated_response(users_ser.data)
        

class GroupView(APIView):
    
    def get(self, request, pk_id):
        group = get_object_or_404(Group, pk=pk_id)
        group_s = GroupSerializer(instance=group)
        return Response(return_code(0, data=group_s.data))

    def post(self, request, pk_id):
        group = get_object_or_404(Group, pk=pk_id)
        group_s = UpdateGroupSerializer(instance=group, data=request.data)
        errors = group_s.update_is_valid()
        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        user_ids = request.data.get('user_ids')
        permission_ids = request.data.get('permission_ids')

        try:
            with transaction.atomic():
                group_s.update_save()
                if user_ids is not None:
                    UserGroup.objects.filter(group_id=group.id).delete()
                    for uid in user_ids:
                        if User.objects.filter(pk=uid):
                            user_group = UserGroup(user_id=uid, group_id=group.id)
                            user_group.save()
                if permission_ids is not None:
                    GroupPermission.objects.filter(group_id=group.id).delete()
                    for pid in permission_ids:
                        if Permission.objects.filter(pk=pid):
                            group_permission = GroupPermission(group_id=group.id, permission_id=pid)
                            group_permission.save()
                for resource_type in settings.RESOURCE_TYPE_MAP:
                    resource_ids = request.data.get('{}_ids'.format(resource_type))
                    if resource_ids is not None:
                        GroupResource.objects.filter(group_id=group.id, resource_type=resource_type).delete()
                        for rid in resource_ids:
                            group_resource = GroupResource(group_id=group.id, resource_type=resource_type,
                                resource_id=rid)
                            group_resource.save()
            return Response(return_code(0))
        except Exception as e:
            return Response(return_code(1004),
                status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        group_s = NewGroupSerializer(data=request.data)
        if not group_s.is_valid():
            return Response(return_code(2001, detail=group_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        user_ids = request.data.get('user_ids', [])
        permission_ids = request.data.get('permission_ids', [])
        
        try:
            with transaction.atomic():
                group = Group(name=request.data['name'])
                group.save()
                for uid in user_ids:
                    if User.objects.filter(pk=uid):
                        user_group = UserGroup(user_id=uid, group_id=group.id)
                        user_group.save()
                for pid in permission_ids:
                    if Permission.objects.filter(pk=pid):
                        group_permission = GroupPermission(group_id=group.id, permission_id=pid)
                        group_permission.save()

                for resource_type in settings.RESOURCE_TYPE_MAP:
                    resource_ids = request.data.get('{}_ids'.format(resource_type))
                    if resource_ids:
                        GroupResource.objects.filter(group_id=group.id, resource_type=resource_type).delete()
                        for rid in resource_ids:
                            group_resource = GroupResource(group_id=group.id, resource_type=resource_type,
                                resource_id=rid)
                            group_resource.save()
            return Response(return_code(0))
        except Exception as e:
            return Response(return_code(1003),
                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        group = get_object_or_404(Group, pk=pk_id)
        try:
            with transaction.atomic():
                UserGroup.objects.filter(group_id = group.id).delete()
                GroupPermission.objects.filter(group_id = group.id).delete()
                GroupResource.objects.filter(group_id = group.id).delete()
                group.delete()
            return Response(return_code(0, msg="删除成功"))
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)
            
class GroupsView(APIView):
    
    def get(self, request):
        groups = Group.objects.order_by('id').all()
        groups_s = GroupSerializer(instance=groups, many=True)
        return Response(return_code(0, data=groups_s.data))


class OperationsView(APIView):
    
    def get(self, request):
        operations = Operation.objects.order_by('id').all()
        operations_s = OperationSerializer(instance=operations, many=True)
        return Response(return_code(0, data=operations_s.data))

class PermissionsView(APIView):

    def get(self, request):
        all_permissions = Permission.objects.order_by('id').all()
        permissions_s = PermissionSerializer(instance=all_permissions, many=True)
        return Response(return_code(0, data=permissions_s.data))

class AthleteView(APIView):
    
    def get(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        athlete_s = AthleteInfoSerializer(athlete)
        return Response(return_code(0, data=athlete_s.data))

    def post(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        athlete_s = UpdateAthleteInfoSerializer(instance=athlete, data=request.data)
        errors = athlete_s.update_is_valid()
        if not errors:
            athlete_s.update_save()
            athlete = AthleteInfo.objects.get(pk=athlete.id)
            athlete_s = AthleteInfoSerializer(athlete)
            return Response(return_code(0, data=athlete_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):

        athlete_s = NewAthleteInfoSerializer(data=request.data)
        if athlete_s.is_valid():
            athlete_s.save()
            athlete = AthleteInfo.objects.get(pk=athlete_s.data['id'])
            athlete_s = AthleteInfoSerializer(athlete)
            return Response(return_code(0, data=athlete_s.data))
        return Response(return_code(2001, detail=athlete_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        try:
            with transaction.atomic():
                SportEventExp.objects.filter(athlete_id=athlete.athlete_id).delete()
                GroupResource.objects.filter(resource_type='athlete', resource_id=pk_id).delete()
                AthleteGroup.objects.filter(athlete_id=pk_id).delete()
                athlete.delete()
            return Response(return_code(0, msg="删除成功"))
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)

class AthleteOverViewView(APIView):
    """
    运动员概览视图
    """

    def get(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        query_set = collections.OrderedDict()
        query_set['match_type'] = get_match_type(athlete.sport_project)[0]
        query_set['athlete_id__icontains'] = athlete.athlete_id
        data = collections.OrderedDict((
            ('id', athlete.id),
            ('athlete_id', athlete.athlete_id),
            ('name', athlete.name),
            ('nationality', athlete.nationality),
            ('profile_photo', athlete.profile_photo.url),
            ('world_ranking', '-'),
            ('olympic_ranking', '-'),
            ('company_name', athlete.company_name),
            ('match_type', athlete.sport_project),
            ('birthday', athlete.birthday),
            ('age', calculate_age(athlete.birthday))
        ))
        world_ranking = WorldRanking.objects.filter(
            **query_set
        ).order_by('-announcemented_at').first()
        olympic_ranking = OlympicRanking.objects.filter(
            **query_set
        ).order_by('-announcemented_at').first()
        if world_ranking:
            data['world_ranking'] = world_ranking.ranking
        if olympic_ranking:
            data['olympic_ranking'] = olympic_ranking.ranking

        return Response(return_code(0, data=data))

class AthleteDocLinkView(APIView):
    """
    运动员关联的文档
    """

    def get(self, request, pk_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        module_id = [mid for mid in set(request.GET.get('module_id', '').strip().split(',')) if mid]
        doc_links = DocLink.objects.filter(
            module_id__in = module_id,
            athlete_id_link__icontains = athlete.athlete_id
        ).order_by('module_id').order_by('path').all()

        data = []
        for doc_link in doc_links:
            data.append(
                collections.OrderedDict(
                    (
                        ('module_id', doc_link.module_id),
                        ('name', os.path.basename(doc_link.path)),
                        ('datetime', get_file_mtime(doc_link.full_path)),
                        ('filesize', get_file_size(doc_link.full_path)),
                        ('type', 'file'),
                        ('path', doc_link.path),
                        ('staticurl', doc_link.staticurl),
                    )
                )
            )

        return Response(return_code(0, data=data))

class AthletesView(APIView):
    def get(self, request):
        query_is = ['gender', 'sport_project']
        query_like = ['name', 'first_coach', 'pro_team_coach', 'nat_team_coach']
        query_range = ['birthday']

        query_set = collections.OrderedDict()
        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        for q in query_like:
            if q in request.GET:
                query_set['{}__icontains'.format(q)] = request.GET[q]
        
        for q in query_range:
            if '{}_from'.format(q) in request.GET:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]

        athlete = get_resource_by_user(request, 'athlete')
        athletes = athlete.filter(**query_set).order_by('id').all()

        pg = CustomPageNumberPagination()
        page_athletes = pg.paginate_queryset(queryset=athletes, request=request, view=self)
        athletes_s = AthleteInfoSerializer(instance=page_athletes, many=True)
        return pg.get_paginated_response(athletes_s.data)

class AthleteGroupView(APIView):
    def get(self, request, pk_id):
        group = get_object_or_404(AthleteGroup, pk=pk_id)
        group_s = AthleteGroupSerializer(group)
        return Response(return_code(0, data=group_s.data))

    def post(self, request, pk_id):
        group = get_object_or_404(AthleteGroup, pk=pk_id)
        group_s = UpdateAthleteGroupSerializer(instance=group, data=request.data)
        errors = group_s.update_is_valid()
        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        athlete_ids = request.data.get('athlete_ids')

        try:
            with transaction.atomic():
                group_s.update_save()
                if athlete_ids is not None:
                    AthleteGroupLink.objects.filter(group_id=group.id).delete()
                    for aid in athlete_ids:
                        if AthleteInfo.objects.filter(pk=aid):
                            athlete_group = AthleteGroupLink(athlete_id=aid, group_id=group.id)
                            athlete_group.save()
            return Response(return_code(0))
        except Exception as e:
            return Response(return_code(1004),
                status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        group_s = NewAthleteGroupSerializer(data=request.data)
        if not group_s.is_valid():
            return Response(return_code(2001, detail=group_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        athlete_ids = request.data.get('athlete_ids', [])
        
        try:
            with transaction.atomic():
                group = AthleteGroup(name=request.data['name'])
                group.save()
                for aid in athlete_ids:
                    if AthleteInfo.objects.filter(pk=aid):
                        athlete_group = AthleteGroupLink(athlete_id=aid, group_id=group.id)
                        athlete_group.save()
            return Response(return_code(0))
        except Exception as e:
            return Response(return_code(1003),
                status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk_id):
        group = get_object_or_404(AthleteGroup, pk=pk_id)
        try:
            with transaction.atomic():
                AthleteGroupLink.objects.filter(group_id = group.id).delete()
                group.delete()
            return Response(return_code(0, msg="删除成功"))
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)

class AthleteGroupsView(APIView):

    def get(self, request):
        query_like = ['name']
        query_set = collections.OrderedDict()
        for q in query_like:
            if q in request.GET:
                query_set['{}__icontains'.format(q)] = request.GET[q]
        groups = AthleteGroup.objects.filter(**query_set).order_by('id').all()

        pg = CustomPageNumberPagination()
        page_groups = pg.paginate_queryset(queryset=groups, request=request, view=self)
        groups_s = AthleteGroupSerializer(instance=page_groups, many=True)
        return pg.get_paginated_response(groups_s.data)

class AthleteCompanyView(APIView):
    
    def get(self, request, pk_id):
        company = get_object_or_404(AthleteCompany, pk=pk_id)
        company_s = AthleteCompanySerializer(company)
        return Response(return_code(0, data=company_s.data))

    def post(self, request, pk_id):
        company = get_object_or_404(AthleteCompany, pk=pk_id)
        company_s = UpdateAthleteCompanySerializer(instance=company, data=request.data)
        errors = company_s.update_is_valid()
        if not errors:
            company_s.update_save()
            company = get_object_or_404(AthleteCompany, pk=pk_id)
            company_s = AthleteCompanySerializer(company)
            return Response(return_code(0, data=company_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        company_s = NewAthleteCompanySerializer(data=request.data)
        if company_s.is_valid():
            company_s.save()
            company = AthleteCompany.objects.get(pk=company_s.data['id'])
            company_s = AthleteCompanySerializer(company)
            return Response(return_code(0, data=company_s.data))
        return Response(return_code(2001, detail=company_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        company = get_object_or_404(AthleteCompany, pk=pk_id)
        company.delete()
        return Response(return_code(0, msg="删除成功"))

class AthleteCompanysView(APIView):
    def get(self, request):
        query_like = ['company_name', 'author_rep', 'credit_code']
        query_set = collections.OrderedDict()
        for q in query_like:
            if q in request.GET:
                query_set['{}__icontains'.format(q)] = request.GET[q]
        companys = AthleteCompany.objects.filter(**query_set).order_by('id').all()
        pg = CustomPageNumberPagination()
        page_companys = pg.paginate_queryset(queryset=companys, request=request, view=self)
        companys_s = AthleteCompanySerializer(instance=page_companys, many=True)
        return pg.get_paginated_response(companys_s.data)

class CompanysListView(APIView):
    
    def get(self, request):
        companys = AthleteCompany.objects.order_by('id').all()
        data = [
            collections.OrderedDict((
                ('id', company.id),
                ('company_id', company.company_id),
                ('company_name', company.company_name)
            ))
        for company in companys]
        return Response(return_code(0, data=data))

class SportEventExpView(APIView):
    
    def get(self, request, pk_id):
        sport_event = get_object_or_404(SportEventExp, pk=pk_id)
        sport_event_s = SportEventExpSerializer(instance=sport_event)
        return Response(return_code(0, data=sport_event_s.data))

    def post(self, request, pk_id):
        sport_event = get_object_or_404(SportEventExp, pk=pk_id)
        sport_event_s = UpdateSportEventExpSerializer(instance=sport_event, data=request.data)
        errors = sport_event_s.update_is_valid()
        if not errors:
            sport_event_s.update_save()
            sport_event = get_object_or_404(SportEventExp, pk=pk_id)
            sport_event_s = SportEventExpSerializer(sport_event)
            return Response(return_code(0, data=sport_event_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        sport_event_s = NewSportEventExpSerializer(data=request.data)
        if sport_event_s.is_valid():
            sport_event_s.save()
            sport_event = SportEventExp.objects.get(pk=sport_event_s.data['id'])
            sport_event_s = SportEventExpSerializer(sport_event)
            return Response(return_code(0, data=sport_event_s.data))
        return Response(return_code(2001, detail=sport_event_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        sport_event = get_object_or_404(SportEventExp, pk=pk_id)
        sport_event.delete()
        return Response(return_code(0, msg="删除成功"))

class MatchVideoView(APIView):

    def get(self, request, pk_id):
        match_round = request.GET.get('round', 0)
        match_score = request.GET.get('score')

        videos_list = []
        match_info = get_object_or_404(MatchInfo, pk = pk_id)
        match_info_s = MatchInfoSerializer(instance=match_info)
        data = match_info_s.data
        match_id = match_info.match_id

        if not match_score:
            yy, md, mid = match_id.split('_')
            video_name = "{}_{}_00_00_00.mp4".format(match_id, match_round)
            video_object_key = os.path.join(yy, md, mid, 'scores', video_name)
            videos_list.append(
                collections.OrderedDict(
                    (
                        ("video", video_name),
                        ("url", get_aws_s3_obj_url(video_object_key))
                    )
                )
            )
            data['videos_list'] = videos_list
            return Response(return_code(0, data=data))

        if match_score.strip().endswith('+'):
            match_score = match_score[:-1]
        match_score = [int(score) for score in match_score.strip().split('-')]
        if len(match_score) == 1:
            score_low, score_high = match_score[0] + 1, 100
        else:
            score_low, score_high = match_score

        rpt_scores = RptScores.objects.filter(
            matchid = match_info.match_id,
            game = match_round,
        ).order_by('score').all()

        for rpt_score in rpt_scores:
            if (rpt_score.video and 
                score_low <= max(rpt_score.score_a, rpt_score.score_b) <= score_high):
                videos_list.append(
                    collections.OrderedDict(
                        (
                            ("video", os.path.basename(rpt_score.video)),
                            ("url", get_aws_s3_obj_url(rpt_score.video))
                            
                        )
                    )
                )
        data['videos_list'] = videos_list
        return Response(return_code(0, data=data))

class MatchVideoView01(APIView):

    def get(self, request, pk_id):
        match_round = request.GET.get('round', 0)
        match_score = request.GET.get('score')

        videos_list = []
        match_info = get_object_or_404(MatchInfo, pk = pk_id)

        match_videos = MatchVideos.objects.filter(
            match_id = match_info.match_id
        )

        match_videos = match_videos.filter(
            match_round = match_round
        )

        match_videos = match_videos.order_by('video').all()

        if match_score:
            match_score = [int(score) for score in match_score.strip().split('-')]
            if len(match_score) == 1:
                score_low, score_high = match_score[0] + 1, 10000
            else:
                score_low, score_high = match_score
            for video in match_videos:
                video_info, suffix = video.video.strip().split('.')
                video_info = video_info.strip().split('_')
                if len(video_info) == 7 and \
                    score_low <= max(int(video_info[5]), int(video_info[6])) <= score_high:

                    videos_list.append(
                        os.path.join(
                            settings.MATCH_VIDEOS,
                            video_info[0],
                            video_info[1],
                            video_info[2],
                            "{}".format(video.video)
                        )
                    )
        else:
            for video in match_videos:
                video_info, suffix = video.video.strip().split('.')
                video_info = video_info.strip().split('_')
                if match_round:
                    if len(video_info) == 4:
                        videos_list.append(
                            os.path.join(
                                settings.MATCH_VIDEOS,
                                video_info[0],
                                video_info[1],
                                video_info[2],
                                "{}".format(video.video)
                            )
                        )
                else:
                    if len(video_info) == 3:
                        videos_list.append(
                            os.path.join(
                                settings.MATCH_VIDEOS,
                                video_info[0],
                                video_info[1],
                                video_info[2],
                                "{}".format(video.video)
                            )
                        )

        match_info_s = MatchInfoSerializer(instance=match_info)
        data = match_info_s.data
        data['videos_list'] = videos_list
        return Response(return_code(0, data=data))

class MatchVideosSearchView(APIView):

    def get(self, request):
        
        query_key = request.GET.get('key', '').strip().split()
        filter_type = request.GET.get('filter', '').strip()
        
        match_info = MatchInfo.objects

        if filter_type == 'tactics_analyze':
            match_id_list = RptHits.objects.values_list('matchid', flat=True).distinct()
            match_info = match_info.filter(match_id__in = match_id_list)
        elif filter_type == 'scores':
            match_id_list = RptScores.objects.values_list('matchid', flat=True).distinct()
            match_info = match_info.filter(match_id__in = match_id_list)

        match_result_map = {
            u'胜': 1,
            u'负': 2
        }

        match_result = ''
        query_like = []
        for key in query_key[:3]:
            if key.strip() in (u'胜', u'负'):
                match_result = match_result_map[key.strip()]
            else:
                query_like.append(key.strip())

        for key in query_like:
            match_info = match_info.filter(
                Q(match_name__icontains = key) |
                Q(player_a__icontains = key) |
                Q(player_b__icontains = key)
            )

        if match_result:
            match_info = match_info.filter(match_result = match_result)

        match_info = match_info.order_by('-match_date').all()

        pg = CustomPageNumberPagination()
        page_match_info = pg.paginate_queryset(queryset=match_info, request=request, view=self)
        match_result_s = MatchInfoSerializer(instance=page_match_info, many=True)
        return pg.get_paginated_response(match_result_s.data)

class AthleteMatchVideosSearchView(APIView):
    """
    针对单个运动员的视频检索

    """

    def get(self, request, pk_id):

        errors = collections.defaultdict(list)

        query_key = request.GET.get('key', '').strip().split()
        filter_type = request.GET.get('filter', '').strip()
        

        if filter_type == 'tactics_analyze':
            match_id_list = RptHits.objects.values_list('matchid', flat=True).distinct()
        elif filter_type == 'scores':
            match_id_list = RptScores.objects.values_list('matchid', flat=True).distinct()
        else:
            errors['filter_type'].append(u"不可为空，取值为：tactics_analyze 或 scores")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        match_info = MatchInfo.objects
        match_info = match_info.filter(match_id__in = match_id_list)
        athlete_id = AthleteInfo.objects.filter(id = pk_id).first().athlete_id

        match_info = match_info.filter(
            Q(player_a_id__icontains = athlete_id) |
            Q(player_b_id__icontains = athlete_id)
        )

        match_result_map = {
            u'胜': 1,
            u'负': 2
        }

        match_result = ''
        query_like = []
        for key in query_key[:2]:
            if key.strip() in (u'胜', u'负'):
                match_result = match_result_map[key.strip()]
            else:
                query_like.append(key.strip())

        for key in query_like:
            match_info = match_info.filter(
                Q(match_name__icontains = key)
            )

        if match_result:
            match_info = match_info.filter(match_result = match_result)

        match_info = match_info.order_by('-match_date')[:10]

        pg = CustomPageNumberPagination()
        page_match_info = pg.paginate_queryset(queryset=match_info, request=request, view=self)
        match_result_s = MatchInfoSerializer(instance=page_match_info, many=True)
        return pg.get_paginated_response(match_result_s.data)

class MatchInfosView(APIView):
    def get(self, request):
        query_like = ['match_name']
        query_or = ['player']
        query_is = ['match_type', 'match_date']
        query_set = collections.OrderedDict()
        for q in query_like:
            if q in request.GET:
                query_set['{}__icontains'.format(q)] = request.GET[q]

        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        match_infos = MatchInfo.objects.filter(**query_set)

        for q in query_or:
            if q in request.GET:
                match_infos = match_infos.filter(
                    Q(player_a__icontains = request.GET[q]) |
                    Q(player_b__icontains = request.GET[q])
                )
        
        match_infos = match_infos.order_by('-created_at').all()

        pg = CustomPageNumberPagination()
        page_match_infos = pg.paginate_queryset(queryset=match_infos, request=request, view=self)
        match_info_s = MatchInfoSerializer(instance=page_match_infos, many=True)
        return pg.get_paginated_response(match_info_s.data)

class MarkMatchInfosView(APIView):

    # 标注系统比赛列表获取接口    

    def get(self, request):
        matchids = RptHits.objects.using('markdb').values_list('matchid', flat=True).distinct()
        match_infos = MarkMatchInfo.objects.using('markdb').filter(
            num__in = matchids
        ).order_by('-create_time').all()
        pg = CustomPageNumberPagination()
        page_match_infos = pg.paginate_queryset(queryset=match_infos, request=request, view=self)
        match_info_s = MarkMatchInfoSerializer(instance=page_match_infos, many=True)
        return pg.get_paginated_response(match_info_s.data)

class MatchListView(APIView):
    def get(self, request):
        query_like = ['match_name']
        query_set = collections.OrderedDict()
        for q in query_like:
            if q in request.GET:
                query_set['{}__icontains'.format(q)] = request.GET[q]
        match_infos = MatchInfo.objects.filter(
            **query_set
        ).order_by('id').values_list('match_name', flat=True)
        match_infos = list(set(match_infos))
        return Response(return_code(0, data=match_infos))

class MatchInfoView(APIView):
    
    def get(self, request, pk_id):
        match_info = get_object_or_404(MatchInfo, pk=pk_id)
        match_info_s = MatchInfoSerializer(instance=match_info)
        return Response(return_code(0, data=match_info_s.data))

    def put(self, request, pk_id):
        match_info_s = NewMatchInfoSerializer(data=request.data)
        if match_info_s.is_valid():
            match_info_s.save()
            match_info = MatchInfo.objects.get(pk=match_info_s.data['id'])
            match_info_s = MatchInfoSerializer(match_info)
            return Response(return_code(0, data=match_info_s.data))
        return Response(return_code(2001, detail=match_info_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk_id):
        match_info = get_object_or_404(MatchInfo, pk=pk_id)
        match_info_s = UpdateMatchInfoSerializer(instance=match_info, data=request.data)
        errors = match_info_s.update_is_valid()
        if not errors:
            match_info_s.update_save()
            match_info = MatchInfo.objects.get(pk=pk_id)
            match_info_s = MatchInfoSerializer(match_info)
            return Response(return_code(0, data=match_info_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        match_info = get_object_or_404(MatchInfo, pk=pk_id)
        match_info.delete()
        return Response(return_code(0, msg="删除成功"))

class MatchLevel2NameView(APIView):
    def get(self, request):
        level2_list = MatchInfo.objects.values_list('level2', flat=True)
        level2_list = [level for level in set(level2_list) if level]
        return Response(return_code(0, data=level2_list))

class WorldRankingListView(APIView):
    def get(self, request):
        world_rankings = WorldRanking.objects.order_by('-id').all()
        pg = CustomPageNumberPagination()
        page_world_rankings = pg.paginate_queryset(
            queryset=world_rankings, request=request, view=self)
        world_rankings_s = WorldRankingSerializer(instance=page_world_rankings, many=True)
        return pg.get_paginated_response(world_rankings_s.data)

class WorldRankingView(APIView):

    def get(self, request, pk_id):
        world_ranking = get_object_or_404(WorldRanking, pk=pk_id)
        world_ranking_s = WorldRankingSerializer(world_ranking)
        return Response(return_code(0, data=world_ranking_s.data))

    def post(self, request, pk_id):
        world_ranking = get_object_or_404(WorldRanking, pk=pk_id)
        world_ranking_s = UpdateWorldRankinSerializer(instance=world_ranking, data=request.data)
        errors = world_ranking_s.update_is_valid()
        if not errors:
            world_ranking_s.update_save()
            world_ranking = WorldRanking.objects.get(pk=pk_id)
            world_ranking_s = WorldRankingSerializer(world_ranking)
            return  Response(return_code(0, data=world_ranking_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        world_ranking_s = NewWorldRankinSerializer(data=request.data)
        if world_ranking_s.is_valid():
            world_ranking_s.save()
            world_ranking = WorldRanking.objects.get(pk=world_ranking_s.data['id'])
            world_ranking_s = WorldRankingSerializer(instance=world_ranking)
            return Response(return_code(0, data=world_ranking_s.data))
        return Response(return_code(2001, detail=world_ranking_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        world_ranking = get_object_or_404(WorldRanking, pk=pk_id)
        world_ranking.delete()
        return Response(return_code(0, msg="删除成功"))

class OlympicRankingListView(APIView):
    def get(self, request):
        olympic_rankings = OlympicRanking.objects.order_by('-id').all()
        pg = CustomPageNumberPagination()
        page_olympic_rankings = pg.paginate_queryset(
            queryset=olympic_rankings, request=request, view=self)
        olympic_rankings_s = OlympicRankingSerializer(instance=page_olympic_rankings, many=True)
        return pg.get_paginated_response(olympic_rankings_s.data)

class OlympicRankingView(APIView):
    
    def get(self, request, pk_id):
        olympic_ranking = get_object_or_404(OlympicRanking, pk=pk_id)
        olympic_ranking_s = OlympicRankingSerializer(instance=olympic_ranking)
        return Response(return_code(0, data=olympic_ranking_s.data))

    def post(self, request, pk_id):
        olympic_ranking = get_object_or_404(OlympicRanking, pk=pk_id)
        olympic_ranking_s = UpdateOlympicRankingSerializer(
            instance=olympic_ranking,
            data=request.data)
        errors = olympic_ranking_s.update_is_valid()
        if not errors:
            olympic_ranking_s.update_save()
            olympic_ranking = OlympicRanking.objects.get(pk=pk_id)
            olympic_ranking_s = OlympicRankingSerializer(olympic_ranking)
            return Response(return_code(0, data=olympic_ranking_s.data))
        return Response(return_code(2001, detail=olympic_ranking_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk_id):
        olympic_ranking_s = NewOlympicRankingSerializer(data=request.data)
        if olympic_ranking_s.is_valid():
            olympic_ranking_s.save()
            olympic_ranking = OlympicRanking.objects.get(pk=olympic_ranking_s.data['id'])
            olympic_ranking_s = OlympicRankingSerializer(instance=olympic_ranking)
            return Response(return_code(0, data=olympic_ranking_s.data))
        return Response(return_code(2001, detail=olympic_ranking_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        olympic_ranking = get_object_or_404(OlympicRanking, pk=pk_id)
        olympic_ranking.delete()
        return Response(return_code(0, msg="删除成功"))

class FitnessItemsView(APIView):
    def get(self, request):
        items = PhysicalFitnessItems.objects.order_by('id').all()
        data = collections.defaultdict(list)
        for item in items:
            data[item.item_level1].append(
                collections.OrderedDict((
                    ("item_name", item.item_name),
                    ("item_id", item.item_id),
                    ("unit", item.unit)
                ))
            )
        return Response(return_code(0, data=data))

class FitnessDatasView(APIView):
    def get(self, request):
        query_is = ['athlete_id', 'fitness_item_id']
        query_set = collections.OrderedDict()

        datas = {}

        if 'category' in request.GET and request.GET['category']:
            category = request.GET['category']

            fitness_items = PhysicalFitnessItems.objects.filter(
                item_level1 = category
            ).values_list('item_id', flat=True)

            fitnessdatas = PhysicalFitnessData.objects.filter(
                fitness_item_id__in = fitness_items
            )

        else:
            for q in query_is:
                if q in request.GET and request.GET[q]:
                    query_set[q] = request.GET[q]

            fitnessdatas = PhysicalFitnessData.objects.filter(**query_set)

        if 'fitness_item_id' in query_set and 'athlete_id' in query_set:
            fitnessdatas = fitnessdatas.order_by('fitness_test_date').all()
            fitnessitem = PhysicalFitnessItems.objects.filter(item_id = query_set['fitness_item_id']).get()
            datas["unit"] = fitnessitem.unit
            datas["values"] = [
                collections.OrderedDict((
                    ('fitness_item_id', data.fitness_item_id),
                    ('fitness_test_date', data.fitness_test_date),
                    ('fitness_test_value', data.fitness_test_value),
                ))
            for data in fitnessdatas]
            return Response(return_code(0, data=datas))
        else:
            fitnessdatas = fitnessdatas.order_by('id').all()
            pg = CustomPageNumberPagination()
            page_fitnessdatas = pg.paginate_queryset(queryset=fitnessdatas, request=request, view=self)
            fitnessdatas_s = PhysicalFitnessDataSerializer(instance=page_fitnessdatas, many=True)
            return pg.get_paginated_response(fitnessdatas_s.data)
            
class FitnessDataView(APIView):
    def get(self, request, pk_id):
        fitnessdata = get_object_or_404(PhysicalFitnessData, pk = pk_id)
        fitnessdata_s = PhysicalFitnessDataSerializer(instance=fitnessdata)
        return Response(return_code(0, data=fitnessdata_s.data))

    def put(self, request, pk_id):
        fitnessdata_s = NewPhysicalFitnessDataSerializer(data=request.data)
        if fitnessdata_s.is_valid():
            fitnessdata_s.save()
            fitnessdata = PhysicalFitnessData.objects.get(pk=fitnessdata_s.data['id'])
            fitnessdata_s = PhysicalFitnessDataSerializer(fitnessdata)
            return Response(return_code(0, data=fitnessdata_s.data))
        return Response(return_code(2001, detail=fitnessdata_s.errors),
            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk_id):
        fitnessdata = get_object_or_404(PhysicalFitnessData, pk=pk_id)
        fitnessdata_s = UpdatePhysicalFitnessDataSerializer(instance=fitnessdata, data=request.data)
        errors = fitnessdata_s.update_is_valid()
        if not errors:
            fitnessdata_s.update_save()
            fitnessdata = PhysicalFitnessData.objects.get(pk=pk_id)
            fitnessdata_s = PhysicalFitnessDataSerializer(fitnessdata)
            return Response(return_code(0, data=fitnessdata_s.data))
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        fitnessdata = get_object_or_404(PhysicalFitnessData, pk=pk_id)
        fitnessdata.delete()
        return Response(return_code(0, msg=u"删除成功"))

class DocLinkView(APIView):

    def get(self, request, module_id):
        errors = collections.defaultdict(list)
        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)
        if not os.path.isdir(data_root_path):
            raise Http404()

        link_file = request.GET.get('path', '').strip().strip('/')
        if not link_file:
            errors['path'].append(u"该字段是必填项")
            
        link_file_path = os.path.join(data_root_path, link_file)
        if not os.path.isfile(link_file_path):
            errors['path'].append(u"关联必须是文件")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        doc_link = DocLink.objects.filter(path = link_file).first()
        doc_link_s = DocLinkSerializer(doc_link)
        return Response(return_code(0, data=doc_link_s.data))

    def post(self, request, module_id):
        errors = collections.defaultdict(list)

        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)
        if not os.path.isdir(data_root_path):
            raise Http404()

        link_file = request.data.get('path', '').strip().strip('/')
        link_file_path = os.path.join(data_root_path, link_file)
        if not os.path.isfile(link_file_path):
            errors['path'].append(u"关联必须是文件")

        match_type = request.data.get('match_type_link', '').strip()
        if match_type:
            for i in match_type.split(','):
                try:
                    if int(i) not in MATCH_TYPE_DICT:
                        errors['match_type_link'].append(
                            u"取值不在范围: {}".format(MATCH_TYPE_DICT.keys())
                         )
                        break
                except Exception as e:
                    errors['match_type_link'].append(
                        u"取值不在范围: {}".format(MATCH_TYPE_DICT.keys())
                     )
                    break

        if not any((
            request.data.get('match_id_link'), 
            request.data.get('athlete_id_link'),
            request.data.get('match_type_link'),
            request.data.get('tags_link')
            )):
            errors['match_id_link, athlete_id_link, match_type_link, tags_link'].append(
                u"必须有一项不为空"
            )

        doc_link = DocLink.objects.filter(module_id=module_id, path = link_file).first()
        data = request.data
        data['module_id'] = module_id
        doc_link_s = NewDocLinkSerializer(instance=doc_link, data=data)
        if doc_link_s.is_valid() and not errors:
            doc_link = doc_link_s.save()
            doc_link_s = DocLinkSerializer(doc_link)
            return Response(return_code(0, data=doc_link_s.data))
        errors.update(doc_link_s.errors)
        return Response(return_code(2001, detail=errors),
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, module_id):
        link_file = request.data.get('path', '').strip().strip('/')
        doc_link = DocLink.objects.filter(module_id=module_id, path = link_file).first()
        if doc_link:
            doc_link.delete()
        return Response(return_code(0, msg=u"删除成功"))
        
class DocsView(APIView):
    def get(self, request, module_id):
        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)

        if not os.path.isdir(data_root_path):
            raise Http404()

        query_dir = request.GET.get('dir', '').strip()
        if query_dir:
            data_root_path = os.path.join(data_root_path, query_dir)
            if not os.path.isdir(data_root_path):
                raise Http404()

        dir_list = []
        file_list = []
        
        path_list = os.listdir(data_root_path)
        path_list.sort()

        for f in path_list:
            if f.startswith('.'):
                continue
            f_path = os.path.join(data_root_path, f)

            file_info = collections.OrderedDict((
                ('name', f),
                ('datetime', get_file_mtime(f_path)),
                ('filesize', get_file_size(f_path)),
            ))
            if os.path.isdir(f_path):
                file_info['type'] = 'folder'
                file_info['path'] = os.path.join(
                    query_dir,
                    f
                )
                dir_list.append(file_info)
            elif os.path.isfile(f_path):
                file_info['type'] = 'file'
                file_info['path'] = os.path.join(
                    query_dir,
                    f
                )
                file_info['staticurl'] = os.path.join(
                    settings.HISTORY_DATA_URL,
                    data_path,
                    query_dir,
                    f
                )
                doc_link = DocLinkOpt(module_id, file_info['path'])
                file_info['islink'] = doc_link.is_linked
                file_list.append(file_info)
            else:
                continue

        data = collections.OrderedDict((
            ('id', doc_data.id),
            ('module_name', doc_data.module_name),
            ('data', (file_list + dir_list))
        ))

        return Response(return_code(0, data = data))

    def post(self, request, module_id):
        """
        文件重命名，新建目录
        """

        def rename(src, dst):
            
            _src, _dst = src, dst
            
            src = os.path.join(data_root_path, _src.strip().strip('/'))
            dst = os.path.join(
                os.path.dirname(src),
                dst.strip().strip('/'))

            if not (os.path.isdir(src) or os.path.isfile(src)):
                errors['src'].append(u"{} 目录或文件不存在".format(_src))

            if os.path.isdir(dst) or os.path.isfile(dst):
                errors['dst'].append(u"{} 目录或文件已存在".format(_dst))

            if errors:
                return Response(return_code(2001, detail=errors),
                    status=status.HTTP_400_BAD_REQUEST)

            doc_link = DocLinkOpt(module_id, _src.strip().strip('/'))
            doc_link.rename(
                os.path.join(
                    os.path.dirname(_src.strip().strip('/')),
                    _dst.strip().strip('/')
                )
            )

            os.rename(src, dst)
            return Response(return_code(0, msg=u"重命名成功", data={"src": _src, "dst": _dst}))
                

        def newdir(dir, newdir):
            _dir = dir
            _newdir = newdir
            basedir = os.path.join(data_root_path, dir.strip().strip('/'))
            newdir = os.path.join(basedir, newdir.strip().strip('/'))
            
            if os.path.isfile(basedir):
                errors['dir'].append(u"已存在文件：{}，无法创建目录：{}".format(_dir, _newdir))

            if os.path.isfile(newdir):
                errors['newdir'].append(u"已存在文件：{}，无法创建目录".format(_newdir))
            if os.path.isdir(newdir):
                errors['newdir'].append(u"已存在目录：{}，无法创建目录".format(_newdir))

            if errors:
                return Response(return_code(2001, detail=errors),
                    status=status.HTTP_400_BAD_REQUEST)

            os.makedirs(newdir)
            return Response(
                return_code(
                    0,
                    msg=u"目录创建成功", 
                    data={
                        "newdir": os.path.join(_dir.strip().strip('/'), _newdir.strip().strip('/'))
                    }
                )
            )

        
        OPTION_TYPE_MAP = {
            'rename': {
                'func': rename,
                'args': [
                    'src',
                    'dst'
                ]
            },
            'newdir': {
                'func': newdir,
                'args': [
                    'dir',
                    'newdir'
                ]
            }
        }

        errors = collections.defaultdict(list)

        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)

        if not os.path.isdir(data_root_path):
            raise Http404()

        opt = request.data.get('opt')
        if not opt or opt not in OPTION_TYPE_MAP:
            errors['opt'].append(u"操作类型取值不在范围: {}".format(OPTION_TYPE_MAP.keys()))
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        args = []
        for arg in  OPTION_TYPE_MAP[opt]['args']:
            if request.data.get(arg) is None:
                errors[arg].append(u"参数不可为空")
            else:
                args.append(request.data.get(arg))

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        return OPTION_TYPE_MAP[opt]['func'](*args)


    def delete(self, request, module_id):
        """
        文件删除
        """
        errors = collections.defaultdict(list)
        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)

        if not os.path.isdir(data_root_path):
            raise Http404()

        query_dir = request.data.get('dir', '').strip().strip('/')
        if not query_dir:
            errors['dir'].append(u"参数不可为空")
        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        delete_path = os.path.join(data_root_path, query_dir)
        if os.path.isdir(delete_path):
            shutil.rmtree(delete_path)
        elif os.path.isfile(delete_path):
            os.remove(delete_path)
            doc_link = DocLinkOpt(module_id, query_dir)
            doc_link.delete()
        else:
            raise Http404()

        return Response(return_code(0, msg="删除成功", data={'dir': query_dir}))

    def put(self, request, module_id):
        """
        文件上传
        """
        errors = collections.defaultdict(list)

        doc_data = get_object_or_404(DocsData, module_id = module_id)
        data_path = doc_data.data_path.strip()

        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)

        if not os.path.isdir(data_root_path):
            raise Http404()

        query_dir = request.data.get('dir', '').strip().strip('/')
        if query_dir:
            data_root_path = os.path.join(data_root_path, query_dir)
            if not os.path.isdir(data_root_path):
                raise Http404()

        upload_file =request.FILES.get('file', None)
        if upload_file:
            file_path = os.path.join(data_root_path, upload_file.name)
        else:
            errors['file'].append(u"上传文件不能为空")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        with open(file_path, 'wb') as fd:
            for chunk in upload_file.chunks():
                fd.write(chunk)

        file_info = collections.OrderedDict(
            (
                ('name', upload_file.name),
                ('datetime', get_file_mtime(file_path)),
                ('filesize', get_file_size(file_path)),
                ('type', 'file'),
                ('path', os.path.join(
                            query_dir,
                            upload_file.name
                        )
                ),
                ('staticurl', os.path.join(
                            settings.HISTORY_DATA_URL,
                            data_path,
                            query_dir,
                            upload_file.name
                         )
                )
            )
        )

        data = collections.OrderedDict((
            ('id', doc_data.id),
            ('module_name', doc_data.module_name),
            ('data', file_info)
        ))

        return Response(return_code(0, data = data))
        
class MarkDataShow(APIView):

    def get(self, request, name, match_id):
        name_table_map = {
            "hits": {
                "db": "markdb",
                "model": RptHits,
                "serializer": RptHitsSerializer,
                "order_by": ["frame_hit"],
            },
            "scores": {
                "db": "markdb",
                "model": RptScores,
                "serializer": RptScoresSerializer,
                "order_by": ["frame_start"],
            },
            "serverecord": {
                "db": "markdb",
                "model": RptServerecord,
                "serializer": RptServerecordSerializer,
                "order_by": ["game", "score", "score_a", "score_b"],
            },
            "playgroundrecord": {
                "db": "markdb",
                "model": RptPlaygroundrecord,
                "serializer": RptPlaygroundrecordSerializer,
                "order_by": ["normal"],
            },
        }

        if name not in name_table_map:
            return Response(return_code(2001),
                status=status.HTTP_400_BAD_REQUEST)

        use_db = name_table_map[name]["db"]
        model = name_table_map[name]["model"]
        order_by = name_table_map[name]["order_by"]
        serializer = name_table_map[name]["serializer"]

        datas = model.objects.using(use_db).filter(
            matchid = match_id
        ).order_by(*order_by).all()
        pg = CustomPageNumberPagination()
        page_datas = pg.paginate_queryset(queryset=datas, request=request, view=self)
        datas_s = serializer(instance=page_datas, many=True)
        return pg.get_paginated_response(datas_s.data)

class MarkDataSync(APIView):
    def post(self, request, name, match_id):
        name_table_map = {
            "hits": {
                "from": {
                    "db": "markdb",
                    "model": RptHits,
                },
                "to": {
                    "db": "default",
                    "model": RptHits,
                },
                "require": {
                    "db": "default",
                    "model": RptScores,
                    "filter": {"matchid": match_id}
                }
            },
            "scores": {
                "from": {
                    "db": "markdb",
                    "model": RptScores,
                },
                "to": {
                    "db": "default",
                    "model": RptScores,
                }
            },
            "serverecord": {
                "from": {
                    "db": "markdb",
                    "model": RptServerecord,
                },
                "to": {
                    "db": "default",
                    "model": RptServerecord,
                }
            },
            "playgroundrecord": {
                "from": {
                    "db": "markdb",
                    "model": RptPlaygroundrecord,
                },
                "to": {
                    "db": "default",
                    "model": RptPlaygroundrecord,
                }
            },
        }

        if name not in name_table_map:
            return Response(return_code(2001),
                status=status.HTTP_400_BAD_REQUEST)

        # 同步数据的 match_id 必须在俱乐部系统的 match_info 表
        try:
            match_info = MatchInfo.objects.get(match_id=match_id)
        except MatchInfo.DoesNotExist:
            return Response(return_code(701, msg=u"比赛：{} 在俱乐部系统中未录入".format(match_id)),
                status=status.HTTP_400_BAD_REQUEST)

        # 同步击球表之前必须先同步得分表
        if name_table_map[name].get("require"):
            require_db = name_table_map[name]["require"]["db"]
            require_model = name_table_map[name]["require"]["model"]
            query_set = name_table_map[name]["require"]["filter"]
            require_datas = require_model.objects.using(require_db).filter(**query_set).all()

            if not require_datas:
                return Response(return_code(701, msg=u"同步 rpt_hits 表之前请先同步 rpt_scores 表"),
                    status=status.HTTP_400_BAD_REQUEST)
                
        # 判断是否有视频抽取任务正在处理
        video_proc_info = VideoProcInfo.objects.filter(
            match_id=match_id,
            tb_name=name
        ).first()

        if video_proc_info:
            task_id = video_proc_info.task_id
            task = AsyncResult(task_id)
            #if task.state in ('SUCCESS', 'FAILURE', 'REVOKED'):
            #if task.state in ('PENDING', 'STARTED', 'RETRY'):
            if task.state in ('STARTED', 'RETRY'):
                data = {
                    "task_id": task.task_id,
                    "state": task.state,
                    "state_name": CeleryState.get(task.state, "")
                }
                return Response(return_code(701, msg=u"任务正在运行...", data=data),
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                # 将表记录标记为未初始化状态
                video_proc_info.init = 0
                video_proc_info.save()

        from_db = name_table_map[name]["from"]["db"]
        from_model = name_table_map[name]["from"]["model"]
        from_datas = from_model.objects.using(from_db).filter(matchid = match_id)
        
        to_db = name_table_map[name]["to"]["db"]
        to_model = name_table_map[name]["to"]["model"]
        to_datas = to_model.objects.using(to_db).filter(matchid = match_id)
        
        # 删目标 db.table 数据，并插入新数据，是一个事务
        try:
            with transaction.atomic():
                to_datas.delete()
                to_model.objects.using(to_db).bulk_create(list(from_datas))
        except Exception as e:
            return Response(return_code(1007),
                status=status.HTTP_400_BAD_REQUEST)

        # 异步执行视频抽取任务
        if name == "scores":
            task = scores_video_proc.delay(match_id, name)
        elif name == 'hits':
            task = hits_video_proc.delay(match_id, name)
        elif name == 'serverecord' or name == 'playgroundrecord':
            return Response(return_code(0, msg="同步数据成功"))

        if video_proc_info:
            video_proc_info.init = 1
            video_proc_info.state = 0
            video_proc_info.task_id = task.task_id
        else:
            video_proc_info = VideoProcInfo()
            video_proc_info.match_id = match_id
            video_proc_info.task_id = task.task_id
            video_proc_info.tb_name = name
            video_proc_info.init = 1
            video_proc_info.state = 0

        video_proc_info.save()
        data = {
            "task_id": task.task_id,
            "state": task.state,
            "state_name": CeleryState.get(task.state, "")
        }
        return Response(return_code(0, msg="同步数据成功，视频处理任务开始", data=data))

class MarkDataSyncRetry(APIView):
    def post(self, request, name, match_id):
        name_table_list = [
            "hits",
            "scores"
        ]
        if name not in name_table_list:
            return Response(return_code(2001),
                status=status.HTTP_400_BAD_REQUEST)

        # 获取当前是否有视频抽取任务正在处理
        try:
            video_proc_info = VideoProcInfo.objects.get(
                match_id=match_id,
                tb_name=name
            )
        except VideoProcInfo.DoesNotExist:
            return Response(return_code(2001),
                status=status.HTTP_400_BAD_REQUEST)

        task_id = video_proc_info.task_id
        task = AsyncResult(task_id)

        #if task.state in ('PENDING', 'STARTED', 'RETRY'):
        if task.state in ('STARTED', 'RETRY'):
            data = {
                "task_id": task.task_id,
                "state": task.state,
                "state_name": CeleryState.get(task.state, "")
            }
            return Response(return_code(701, msg=u"任务正在运行...", data=data),
                status=status.HTTP_400_BAD_REQUEST)

        # 将表记录标记为未初始化状态
        video_proc_info.init = 0
        video_proc_info.save()
        # 异步执行视频抽取任务
        if name == "scores":
            task = scores_video_proc.delay(match_id, name)
        elif name == 'hits':
            task = hits_video_proc.delay(match_id, name)

        video_proc_info.init = 1
        video_proc_info.task_id = task.task_id
        video_proc_info.save()
        data = {
            "task_id": task.task_id,
            "state": task.state,
            "state_name": CeleryState.get(task.state, "")
        }
        return Response(return_code(0, msg="视频处理任务开始", data=data))
    

class ManagerAthletesView(APIView):
    pass


class NewSN(APIView):
    
    def get(self, request, type_id):
        type_model_map = {
            'athleteinfo': (AthleteInfo, 'athlete_id'),
            'athletecompany': (AthleteCompany, 'company_id'),
            'sportevent': (SportEventExp, 'sport_event_id')
        }

        model, item = type_model_map.get(type_id, (None, None))
        if not model:
            return Response(
                return_code(701,
                    detail="sn/<type_id>，type_id 只能在{}中选择".format(type_model_map.keys())),
                status=status.HTTP_400_BAD_REQUEST
            )

        while True:
            sn = lmd5sum()
            if not model.objects.filter(**{item: sn}).all():
                return Response(return_code(0, data={"sn": sn}))


class Test(APIView):
    def get(self, request):
        from .tasks import add
        
        task = add.delay(100, 200)

        return Response(return_code(0, data={"task_id": task.task_id}))

