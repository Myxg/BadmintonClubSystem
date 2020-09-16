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
    User, Group, UserGroup, UserResourceLink, MenuModule, Privilege, UserMenuPrivilegeLink,
    AthleteInfo, AthleteCompany, SportEventExp, MatchInfo, MarkMatchInfo,
    AthleteGroup, AthleteGroupLink, WorldRanking, OlympicRanking, DocsData,
    PhysicalFitnessItems, PhysicalFitnessData, RptHits, RptScores, RptServerecord,
    RptPlaygroundrecord, RptGoalrecord, VideoProcInfo, DocLink, MyJuli, MyZb, MyDistance,
    VideoComment, FavoriteFolder, VideoBatchShareTasks
)
from .serializers import (
    UserSerializer, UserAddSerializer, UserUpdatePhotoSerializer,
    UpdateUserSerializer, UserUpdateEmailSerializer,
    GroupSerializer, NewGroupSerializer, UpdateGroupSerializer, MenuModuleSerializer,
    PrivilegeSerializer,
    AthleteInfoSerializer, UpdateAthleteInfoSerializer, NewAthleteInfoSerializer,
    NewAthleteCompanySerializer, AthleteCompanySerializer, UpdateAthleteCompanySerializer,
    SportEventExpSerializer, UpdateSportEventExpSerializer, NewSportEventExpSerializer,
    AthleteGroupSerializer, NewAthleteGroupSerializer, 
    MatchInfoSerializer, NewMatchInfoSerializer, UpdateMatchInfoSerializer, MarkMatchInfoSerializer,
    RptHitsSerializer, RptScoresSerializer, RptServerecordSerializer, RptPlaygroundrecordSerializer,
    RptGoalrecordSerializer,
    WorldRankingSerializer, NewWorldRankinSerializer, UpdateWorldRankinSerializer,
    OlympicRankingSerializer, NewOlympicRankingSerializer, UpdateOlympicRankingSerializer,
    PhysicalFitnessDataSerializer, NewPhysicalFitnessDataSerializer, UpdatePhysicalFitnessDataSerializer,
    DocLinkSerializer, NewDocLinkSerializer,
    NewVideoCommentSerializer, VideoCommentSerializer,
    NewFavoriteFolderSerializer, FavoriteFolderSerializer,
    VideoProcInfoSerializer,
)
from common.utils import (
    CustomPageNumberPagination, return_code, lmd5sum, get_file_mtime, get_file_size,
    CeleryState, get_zone_list, calculate_age, commentlink, gen_random_str, get_video_url
)
from common.resource import (
    get_resource_by_user, get_resource_by_id, get_match_by_user, get_ranking_by_user,
    get_fitness_by_user, get_doc_link_by_user, get_resource_column_by_user
)
from common.privilege import (
    get_Privilege_by_user
)
from common.pub_map import (
    MATCH_TYPE_DICT, get_match_type,
)
from common.modelquery import (
    model_query, model_query_get, model_query_first, model_query_column_list
)
from common.aws_s3 import get_aws_s3_obj_url, s3_video_path_list
from .tasks import scores_video_proc, hits_video_proc, video_compressed_packaging
from .doclinkopt import DocLinkOpt
from middleware.apilogging import apiLogger

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
            
            # 设置用户密码
            password = request.data.get('password', '').strip()
            if password:
                user.set_password(password)
                user.save()

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

class UserPrivilegeViews(APIView):
    
    def get(self, request):
        data = get_Privilege_by_user(request)
        return Response(return_code(0, data=data))

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

        try:
            with transaction.atomic():
                group_s.update_save()
                if user_ids is not None:
                    UserGroup.objects.filter(group_id=group.id).delete()
                    for uid in user_ids:
                        if User.objects.filter(pk=uid):
                            user_group = UserGroup(user_id=uid, group_id=group.id)
                            user_group.save()
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
        
        try:
            with transaction.atomic():
                group = Group(name=request.data['name'])
                group.save()
                for uid in user_ids:
                    if User.objects.filter(pk=uid):
                        user_group = UserGroup(user_id=uid, group_id=group.id)
                        user_group.save()
            return Response(return_code(0))
        except Exception as e:
            return Response(return_code(1003),
                status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk_id):
        group = get_object_or_404(Group, pk=pk_id)
        try:
            with transaction.atomic():
                UserGroup.objects.filter(group_id = group.id).delete()
                group.delete()
            return Response(return_code(0, msg="删除成功"))
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)
            
class GroupsView(APIView):
    
    def get(self, request):
        queryset = collections.OrderedDict()
        query_like = ['name']

        for q in query_like:
            if request.GET.get(q, '').strip():
                queryset['{}__icontains'.format(q)] = request.GET[q].strip()

        groups = Group.objects.filter(**queryset).order_by('id').all()
        pg = CustomPageNumberPagination()
        page_groups = pg.paginate_queryset(queryset=groups, request=request, view=self)
        group_ser = GroupSerializer(instance=page_groups, many=True)
        return pg.get_paginated_response(group_ser.data)

class ResourceBindView(APIView):
    
    def get(self, request, user_id_type, user_id):
        resources = UserResourceLink.objects.filter(
            user_id = user_id,
            user_id_type = user_id_type,
        ).all()
        data = collections.defaultdict(list)
        for resource in resources:
            data[resource.resource_type].append(resource.resource_id)

        for resource in data:
            data[resource] = get_resource_by_id(resource, data[resource])

        return Response(return_code(0, data=data))

    def post(self, request, user_id_type, user_id):
        try:
            with transaction.atomic():
                UserResourceLink.objects.filter(
                    user_id = user_id,
                    user_id_type = user_id_type,
                ).delete()
                for resource in request.data:
                    for pk_id in request.data[resource]:
                        user_resource = UserResourceLink(
                            user_id = user_id,
                            user_id_type = user_id_type,
                            resource_type = resource,
                            resource_id_type = 1 if resource.endswith('_group') else 0,
                            resource_id = pk_id
                        )
                        user_resource.save()
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(return_code(0))

    def delete(self, request, user_id_type, user_id):
        UserResourceLink.objects.filter(
            user_id = user_id,
            user_id_type = user_id_type,
        ).delete()
        return Response(return_code(0, msg=u'删除成功'))

class MenusView(APIView):
    
    def get(self, request):
        query_set = collections.OrderedDict()
        query_like = ['name']

        for q in query_like:
            if request.GET.get(q, '').strip():
                query_set['{}__icontains'.format(q)] = request.GET[q].strip()

        menus = MenuModule.objects.filter(**query_set).order_by('id').all()
        pg = CustomPageNumberPagination()
        page_menus = pg.paginate_queryset(queryset=menus, request=request, view=self)
        menus_ser = MenuModuleSerializer(instance=page_menus, many=True)
        return pg.get_paginated_response(menus_ser.data)

class PrivilegesViews(APIView):
    def get(self, request):
        privileges = Privilege.objects.order_by('id').all()
        privileges_s = PrivilegeSerializer(instance=privileges, many=True)
        return Response(return_code(0, data=privileges_s.data))

class MenuPrivilegeBindView(APIView):

    def get(self, request, user_id_type, user_id):
        menu_privileges = UserMenuPrivilegeLink.objects.filter(
            user_id = user_id,
            user_id_type = user_id_type,
        ).order_by('id').all()

        data = []
        
        for mp in menu_privileges:
            data.append(
                {
                    'menu_module_id': mp.menu_module_id,
                    'menu_module_name': mp.menu_module_name,
                    'privilege_id': mp.privilege_id,
                    'privilege_name': mp.privilege_name
                }
            )

        return Response(return_code(0, data=data))

    def post(self, request, user_id_type, user_id):
        try:
            with transaction.atomic():
                UserMenuPrivilegeLink.objects.filter(
                    user_id = user_id,
                    user_id_type = user_id_type,
                ).delete()
                for mp in request.data['privileges']:
                    user_mp = UserMenuPrivilegeLink(
                        user_id = user_id,
                        user_id_type = user_id_type,
                        menu_module_id = mp['menu_module_id'],
                        privilege_id = mp['privilege_id']
                    )
                    user_mp.save()
        except Exception as e:
            return Response(return_code(1005),
                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(return_code(0))
        
    def delete(self, request, user_id_type, user_id):
        UserMenuPrivilegeLink.objects.filter(
            user_id = user_id,
            user_id_type = user_id_type,
        ).delete()
        return Response(return_code(0, msg=u'删除成功'))
        
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
                #GroupResource.objects.filter(resource_type='athlete', resource_id=pk_id).delete()
                AthleteGroupLink.objects.filter(athlete_id=pk_id).delete()
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

class AthleteBaseInfoView(APIView):
    """
    根据 athlete id 获取运动员信息
    """

    def get(self, request, athlete_id):
        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, athlete_id=athlete_id)
        query_set = collections.OrderedDict()

        data = collections.OrderedDict((
            ('id', athlete.id),
            ('athlete_id', athlete.athlete_id),
            ('name', athlete.name),
            ('nationality', athlete.nationality),
            ('profile_photo', athlete.profile_photo.url),
            ('company_name', athlete.company_name),
            ('match_type', athlete.sport_project),
            ('birthday', athlete.birthday),
            ('age', calculate_age(athlete.birthday))
        ))

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
        query_is = ['gender', 'nationality']
        query_like = [
            'name', 'first_coach', 'pro_team_coach', 
            'nat_team_coach', 'sport_project',
        ]
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
        group_s = NewAthleteGroupSerializer(instance=group, data=request.data)
        if not group_s.is_valid():
            return Response(return_code(2001, detail=group_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        athlete_ids = request.data.get('athlete_ids', [])

        try:
            with transaction.atomic():
                group_s.save()
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
                group_s.save()
                for aid in athlete_ids:
                    if AthleteInfo.objects.filter(pk=aid):
                        athlete_group = AthleteGroupLink(athlete_id=aid, group_id=group_s.data['id'])
                        athlete_group.save()
            return Response(return_code(0))
        except Exception as e:
            raise
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
        match_info = get_match_by_user(request, MatchInfo)
        match_info = get_object_or_404(match_info, pk = pk_id)
        match_info_s = MatchInfoSerializer(instance=match_info)
        data = match_info_s.data
        match_id = match_info.match_id

        if not match_score:
            yy, md, mid = match_id.split('_')
            video_name = "{}_{}_00_00_00.mp4".format(match_id, match_round)
            video_object_key = os.path.join(yy, md, mid, 'scores', video_name)
            video_comment = model_query_first(VideoComment, query={"video_name": video_name})
            is_comment = True if video_comment else False
            videos_list.append(
                collections.OrderedDict(
                    (
                        ("video", video_name),
                        ("url", get_video_url(video_object_key)),
                        ("is_comment", is_comment)
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
                            ("url", get_video_url(rpt_score.video)),
                            ("is_comment", rpt_score.is_comment),
                            
                        )
                    )
                )
        data['videos_list'] = videos_list
        return Response(return_code(0, data=data))

class MatchVideosSearchView(APIView):

    def get(self, request):
        
        query_key = request.GET.get('key', '').strip().split()
        filter_type = request.GET.get('filter', '').strip()
        
        #match_info = MatchInfo.objects
        match_info = get_match_by_user(request, MatchInfo)

        if filter_type == 'tactics_analyze':
            match_id_list = RptScores.objects.values_list('matchid', flat=True).distinct()
            score_match_id_list = match_info.filter(
                match_id__in = match_id_list).values_list('match_id', flat=True).distinct()
            """
            hit_match_id_list = RptHits.objects.filter(
                matchid__in = score_match_id_list).values_list('matchid', flat=True).distinct()
            serverecord_match_id_list = RptServerecord.objects.filter(
                matchid__in = score_match_id_list).values_list('matchid', flat=True).distinct()
            goalrecord_match_id_list = RptGoalrecord.objects.filter(
                matchid__in = score_match_id_list).values_list('matchid', flat=True).distinct()

            match_id_list = list(
                set(
                    list(hit_match_id_list) + 
                    list(serverecord_match_id_list) + 
                    list(goalrecord_match_id_list)
                )
            )
            """
            match_id_list = []
            for m_id in score_match_id_list:
                is_exist = RptHits.objects.filter(matchid=m_id).first()
                if is_exist:
                    match_id_list.append(m_id)
                    continue
                is_exist = RptServerecord.objects.filter(matchid=m_id).first()
                if is_exist:
                    match_id_list.append(m_id)
                    continue
                is_exist = RptGoalrecord.objects.filter(matchid=m_id).first()
                if is_exist:
                    match_id_list.append(m_id)
                    continue
            match_info = match_info.filter(match_id__in = match_id_list)
        elif filter_type == 'scores':
            match_id_list = RptScores.objects.values_list('matchid', flat=True).distinct()
            match_info = match_info.filter(match_id__in = match_id_list)
        elif filter_type == 'scores_detail':
            match_id_list = MyJuli.objects.values_list('matchid', flat=True).distinct()
            match_info = match_info.filter(match_id__in = match_id_list)
        elif filter_type == 'match_distance':
            match_id_list = MyDistance.objects.values_list('match_num', flat=True).distinct()
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


        athlete = get_resource_by_user(request, 'athlete')
        athlete = get_object_or_404(athlete, pk=pk_id)
        athlete_id = athlete.athlete_id

        match_info = MatchInfo.objects
        match_info = match_info.filter(match_id__in = match_id_list)

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

        #match_infos = MatchInfo.objects.filter(**query_set)
        # 过滤当前登陆用户有权限的运动员相关的比赛
        match_infos = get_match_by_user(request, MatchInfo).filter(**query_set)

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
        matchids = RptScores.objects.using('markdb').values_list('matchid', flat=True).distinct()
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
        match_infos = get_match_by_user(request, MatchInfo)
        match_infos = match_infos.filter(
            **query_set
        ).order_by('id').values_list('match_name', flat=True)
        match_infos = list(set(match_infos))
        return Response(return_code(0, data=match_infos))

class MatchInfoView(APIView):
    
    def get(self, request, pk_id):
        match_info = get_match_by_user(request, MatchInfo)
        match_info = get_object_or_404(match_info, pk=pk_id)
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
        match_info = get_match_by_user(request, MatchInfo)
        match_info = get_object_or_404(match_info, pk=pk_id)
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
        match_info = get_match_by_user(request, MatchInfo)
        match_info = get_object_or_404(match_info, pk=pk_id)
        match_info.delete()
        return Response(return_code(0, msg="删除成功"))

class MatchLevel2NameView(APIView):
    def get(self, request):
        level2_list = MatchInfo.objects.values_list('level2', flat=True)
        level2_list = [level for level in set(level2_list) if level]
        return Response(return_code(0, data=level2_list))

class WorldRankingListView(APIView):
    def get(self, request):
        world_rankings = get_ranking_by_user(request, WorldRanking)
        world_rankings = world_rankings.order_by('-id').all()
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
        world_ranking = get_ranking_by_user(request, WorldRanking)
        world_ranking = get_object_or_404(world_ranking, pk=pk_id)
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
        world_ranking = get_ranking_by_user(request, WorldRanking)
        world_ranking = get_object_or_404(world_ranking, pk=pk_id)
        world_ranking.delete()
        return Response(return_code(0, msg="删除成功"))

class OlympicRankingListView(APIView):
    def get(self, request):

        olympic_rankings = get_ranking_by_user(request, OlympicRanking)
        olympic_rankings = olympic_rankings.order_by('-id').all()

        pg = CustomPageNumberPagination()
        page_olympic_rankings = pg.paginate_queryset(
            queryset=olympic_rankings, request=request, view=self)
        olympic_rankings_s = OlympicRankingSerializer(instance=page_olympic_rankings, many=True)
        return pg.get_paginated_response(olympic_rankings_s.data)

class OlympicRankingView(APIView):
    
    def get(self, request, pk_id):
        olympic_ranking = get_ranking_by_user(request, OlympicRanking)
        olympic_ranking = get_object_or_404(olympic_ranking, pk=pk_id)
        olympic_ranking_s = OlympicRankingSerializer(instance=olympic_ranking)
        return Response(return_code(0, data=olympic_ranking_s.data))

    def post(self, request, pk_id):
        olympic_ranking = get_ranking_by_user(request, OlympicRanking)
        olympic_ranking = get_object_or_404(olympic_ranking, pk=pk_id)
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
        olympic_ranking = get_ranking_by_user(request, OlympicRanking)
        olympic_ranking = get_object_or_404(olympic_ranking, pk=pk_id)
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

        fitnessdatas = get_fitness_by_user(request, PhysicalFitnessData)

        if 'category' in request.GET and request.GET['category']:
            category = request.GET['category']

            fitness_items = PhysicalFitnessItems.objects.filter(
                item_level1 = category
            ).values_list('item_id', flat=True)

            fitnessdatas = fitnessdatas.filter(
                fitness_item_id__in = fitness_items
            )

        else:
            for q in query_is:
                if q in request.GET and request.GET[q]:
                    query_set[q] = request.GET[q]

            fitnessdatas = fitnessdatas.filter(**query_set)

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
        fitnessdata = get_fitness_by_user(request, PhysicalFitnessData)
        fitnessdata = get_object_or_404(fitnessdata, pk = pk_id)
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
        fitnessdata = get_fitness_by_user(request, PhysicalFitnessData)
        fitnessdata = get_object_or_404(fitnessdata, pk = pk_id)
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
        fitnessdata = get_fitness_by_user(request, PhysicalFitnessData)
        fitnessdata = get_object_or_404(fitnessdata, pk = pk_id)
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
        query_dir = request.GET.get('dir', '').strip().strip('/')

        # 增加视频使用 aws s3 逻辑判断
        #if module_id == 'Videoinfo':
        #    query_dir = query_dir + '/'
        #    obj_list = s3_video_path_list(prefix=query_dir)
        #    for obj in obj_list:
        #        if obj['type'] == 'file':
        #            doc_link = DocLinkOpt(module_id, obj['path'])
        #            obj['islink'] = doc_link.is_linked

        #    data = collections.OrderedDict((
        #        ('id', doc_data.id),
        #        ('module_name', doc_data.module_name),
        #        ('data', obj_list)
        #    ))

        #    return Response(return_code(0, data = data))
               

        data_path = doc_data.data_path.strip()
        data_root_path = os.path.join(settings.HISTORY_DATA_PATH, data_path)

        if not os.path.isdir(data_root_path):
            raise Http404()
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
                f_r_path = os.path.join(
                    query_dir,
                    f
                )
                doc_link = DocLinkOpt(module_id, f_r_path)

                if request.user.username != 'admin':
                    if not doc_link.is_linked:
                        continue
                    else:
                        # 获取当前用户关联的所有运动员的 athlete_id
                        athlete_ids = get_resource_column_by_user(request, 'athlete', 'athlete_id')
                        # 获取文件关联的运动员 athlete_id
                        link_athlete_ids = doc_link.doc_link.athlete_id_link.strip().split(',')
                        # 没有交集的话说明没有关联
                        if not set(athlete_ids) & set(link_athlete_ids):
                            continue

                file_info['type'] = 'file'
                file_info['path'] = f_r_path
                file_info['staticurl'] = os.path.join(
                    settings.HISTORY_DATA_URL,
                    data_path,
                    query_dir,
                    f
                )
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
            "goalrecord": {
                "db": "markdb",
                "model": RptGoalrecord,
                "serializer": RptGoalrecordSerializer,
                "order_by": ["score"]
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
            "goalrecord": {
                "from": {
                    "db": "markdb",
                    "model": RptGoalrecord,
                },
                "to": {
                    "db": "default",
                    "model": RptGoalrecord,
                },
                "require": {
                    "db": "default",
                    "model": RptScores,
                    "filter": {"matchid": match_id}
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
                return Response(return_code(701, msg=u"同步 rpt_{} 表之前请先同步 rpt_scores 表".format(name)),
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
            if task.state in ('STARTED', 'RETRY') and not video_proc_info.task_is_failured:
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
        elif name in ('serverecord', 'playgroundrecord', 'goalrecord'):
            return Response(return_code(0, msg="同步数据成功"))

        if video_proc_info:
            video_proc_info.init = 1
            video_proc_info.state = 0
            video_proc_info.error_code = ''
            video_proc_info.error_info = ''
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
        if task.state in ('STARTED', 'RETRY') and not video_proc_info.task_is_failured:
            data = {
                "task_id": task.task_id,
                "state": task.state,
                "state_name": CeleryState.get(task.state, "")
            }
            return Response(return_code(701, msg=u"任务正在运行...", data=data),
                status=status.HTTP_400_BAD_REQUEST)

        # 将表记录标记为未初始化状态
        video_proc_info.init = 0
        video_proc_info.error_code = ''
        video_proc_info.error_info = ''
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

class MarkDataSyncTasksView(APIView):
    
    def get(self, request):
        video_proc_tasks = model_query(VideoProcInfo, order_by=['-created_at'])
        pg = CustomPageNumberPagination()
        page_video_proc_tasks = pg.paginate_queryset(queryset=video_proc_tasks, request=request, view=self)
        video_proc_tasks_s = VideoProcInfoSerializer(instance=page_video_proc_tasks, many=True)
        return pg.get_paginated_response(video_proc_tasks_s.data)

class MarkDataSyncTaskView(APIView):

    def get(self, request, name, match_id):
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

        video_proc_tasks_s = VideoProcInfoSerializer(video_proc_info)
        return Response(return_code(0, data=video_proc_tasks_s.data))

class VideoCommentView(APIView):
    """
    视频评论
    """

    def post(self, request, pk_id):
        video_comment = get_object_or_404(VideoComment, pk=pk_id, user_id=request.user.id)
        content = request.data.get('content')
        if content:
            video_comment.content = content
            video_comment.save()
            video_comment = model_query_get(VideoComment, query={'pk': video_comment.id})
        video_comment_s = VideoCommentSerializer(video_comment)
        return Response(return_code(0, data=video_comment_s.data))

    def put(self, request, pk_id):
        post_data = request.data
        post_data['user_id'] = request.user.id
        
        video_comment_s = NewVideoCommentSerializer(data=post_data)

        if video_comment_s.is_valid():
            video_comment_s.save()
            video_comment = model_query_get(VideoComment, query={'pk': video_comment_s.data['id']})
            video_comment_s = VideoCommentSerializer(video_comment)
            return Response(return_code(0, data=video_comment_s.data))
        return Response(return_code(2001, detail=video_comment_s.errors),
            status=status.HTTP_400_BAD_REQUEST) 

    def delete(self, request, pk_id):
        video_comment = model_query_first(VideoComment, query={'id': pk_id, 'user_id': request.user.id})
        if not video_comment:
            return Response(return_code(0, msg='删除成功'))

        parent_ids = [video_comment.id]
        all_ids = []
        all_ids += parent_ids
        while True:
            child_ids = model_query_column_list(VideoComment, query={'parent_id__in': parent_ids})
            if not child_ids:
                break
            all_ids += child_ids
            parent_ids = child_ids

        model_query(VideoComment, query={'id__in': all_ids}).delete()
        return Response(return_code(0, msg='删除成功'))

class VideoCommentLinkView(APIView):
    """
    获取全部的评论
    """

    def get(self, request):
        errors = collections.defaultdict(list)
        query_set = collections.OrderedDict()

        video_name = request.GET.get('video_name')
        if video_name:
            query_set['video_name'] = video_name
        else:
            errors["video_name"].append(u"必须参数")

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        video_comments = model_query(VideoComment, query=query_set)
        if not video_comments:
            return Response(return_code(0, data=[]))

        data = commentlink(video_comments)

        return Response(return_code(0, data=data))

class FavoriteFolderView(APIView):
    """
    收藏夹接口
    """

    def get(self, request, pk_id):
        favorite = model_query_first(FavoriteFolder, query={'pk': pk_id, 'user_id': request.user.id})
        if not favorite:
            return Response(return_code(0, data={}))
        favorite_folder_childs = model_query(
            FavoriteFolder,
            query={'parent_id': pk_id, 'record_type': 0, 'user_id': request.user.id},
            order_by=['name', 'id']
        )
        favorite_url_childs = model_query(
            FavoriteFolder,
            query={'parent_id': pk_id, 'record_type': 1, 'user_id': request.user.id},
            order_by=['name', 'id']
        )

        favorite_s = FavoriteFolderSerializer(favorite)

        favorite_folder_childs_s = FavoriteFolderSerializer(favorite_folder_childs, many=True)
        favorite_url_childs_s = FavoriteFolderSerializer(favorite_url_childs, many=True)
        
        data = favorite_s.data
        data['folder_childs'] = favorite_folder_childs_s.data
        data['url_childs'] = favorite_url_childs_s.data

        return Response(return_code(0, data=data))
            
    def put(self, request, pk_id):
        errors = collections.defaultdict(list)

        post_data = request.data
        post_data['user_id'] = request.user.id

        if post_data['record_type'] == 0:
            post_data['url'] = ''

        if post_data['parent_id'] != 0:
            favorite = model_query_first(FavoriteFolder, query={'pk': post_data['parent_id']})
            if not favorite:
                errors['parent_id'].append(u'parent_id 不存在')  
            elif favorite.record_type == 1:
                errors['parent_id'].append(u'父收藏类型 record_type 必须为 0')

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        favorite_s = NewFavoriteFolderSerializer(data=post_data)
        if not favorite_s.is_valid():
            return Response(return_code(2001, detail=favorite_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        favorite_s.save()
        favorite = model_query_get(FavoriteFolder, query={'pk': favorite_s.data['id']})
        favorite_s = FavoriteFolderSerializer(favorite)
        return Response(return_code(0, data=favorite_s.data))

    def post(self, request, pk_id):
        favorite = get_object_or_404(FavoriteFolder, pk=pk_id, user_id=request.user.id)

        name = request.data.get('name')
        url = request.data.get('url')
        parent_id = request.data.get('parent_id')

        if favorite.name != name and name:
            favorite.name = name
        if favorite.parent_id != parent_id and parent_id is not None:
            # 当移动收藏时，判断移动到父收藏夹是否合法
            errors = collections.defaultdict(list)
            if parent_id != 0:
                favorite_father = model_query_first(FavoriteFolder, query={'pk': parent_id, 'user_id': request.user.id})
                if not favorite_father:
                    errors['parent_id'].append(u'parent_id 不存在')  
                elif favorite_father.record_type == 1:
                    errors['parent_id'].append(u'父收藏类型 record_type 必须为 0')
            if errors:
                return Response(return_code(2001, detail=errors),
                    status=status.HTTP_400_BAD_REQUEST)

            favorite.parent_id = parent_id
        if favorite.record_type == 1 and favorite.url != url and url:
            favorite.url = url

        favorite.save()

        favorite = model_query_get(FavoriteFolder, query={'pk': pk_id})
        favorite_s = FavoriteFolderSerializer(favorite)
        return Response(return_code(0, data=favorite_s.data))

    def delete(self, request, pk_id):
        favorite = model_query_first(FavoriteFolder, query={'pk': pk_id, 'user_id': request.user.id})
        if not favorite:
            return Response(return_code(0, msg='删除成功'))

        parent_ids = [favorite.id]
        all_ids = []
        all_ids += parent_ids

        while True:
            child_ids = model_query_column_list(FavoriteFolder, query={'parent_id__in': parent_ids, 'user_id': request.user.id})
            if not child_ids:
                break
            all_ids += child_ids
            parent_ids = child_ids

        model_query(FavoriteFolder, query={'id__in': all_ids}).delete()
        return Response(return_code(0, msg='删除成功'))

class FavoriteRootFoldersView(APIView):
    """
    获取所有 root 级别收藏夹和收藏内容
    """

    def get(self, request):
        favorites = model_query(FavoriteFolder, query={'parent_id': 0, 'user_id': request.user.id})
        favorites_s = FavoriteFolderSerializer(favorites, many=True)
        return Response(return_code(0, data=favorites_s.data))

class VideoBatchShare(APIView):
    """
    批量视频打包下载
    """

    def post(self, request):
        match_id = request.data.get('match_id').strip()
        video_list = request.data.get('video_list')
        suffix = gen_random_str()

        dt = now().strftime("%Y%m%d")
        # zip file
        zipfile_name = "{}_{}.zip".format(match_id.strip(), suffix)
        zipfile = os.path.join(
            settings.COMPRESSED_PACKAGING_DIR,
            dt,
            zipfile_name
        )

        video_name_list = ",".join([video['video'] for video in video_list])
        url = os.path.join(
            settings.COMPRESSED_PACKAGING_URL,
            dt,
            zipfile_name
        )

        task = video_compressed_packaging.delay(
            match_id,
            video_list,
            dt,
            zipfile
        )

        batch_pkg_task = VideoBatchShareTasks(
            user_id = request.user.id,
            task_id = task.task_id,
            video_list = video_name_list,
            url = url,
            state = task.state,
            state_name = CeleryState.get(task.state, "")
        )

        batch_pkg_task.save()

        data = {
            "task_id": task.task_id,
            "state": task.state,
            "state_name": CeleryState.get(task.state, ""),
            "url": url
        }
        return Response(return_code(0, msg="视频批量下载压缩任务开始", data=data))

class VideoBatchPkgTasksStatusView(APIView):
    """
    视频批量下载打包任务状态
    """
    def get(self, request, task_id):
        batch_pkg_task = model_query_first(
            VideoBatchShareTasks,
            query = {
                "task_id": task_id,
                "user_id": request.user.id
            }
        )

        if not batch_pkg_task:
            return Response(return_code(0, data={}))

        task = AsyncResult(batch_pkg_task.task_id)

        batch_pkg_task.state = task.state
        batch_pkg_task.state_name = CeleryState.get(task.state, "")
        batch_pkg_task.save()

        data = {
            "task_id": task.task_id,
            "state": task.state,
            "state_name": CeleryState.get(task.state, ""),
            "url": batch_pkg_task.url
        }
        return Response(return_code(0, data=data))


class BatchFavorites(APIView):
    """
    批量收藏
    """

    def put(self, request):

        errors = collections.defaultdict(list)

        parent_id = request.data.get('parent_id')
        collect_list = request.data.get('collect_list')

        if 'parent_id' != 0:
            favorite = model_query_first(FavoriteFolder, query={'pk': parent_id})
            if not favorite:
                errors['parent_id'].append(u'parent_id 不存在')
            elif favorite.record_type == 1:
                errors['parent_id'].append(u'父收藏类型 record_type 必须为 0')

        if errors:
            return Response(return_code(2001, detail=errors),
                status=status.HTTP_400_BAD_REQUEST)

        collect_list = [
            FavoriteFolder(
                user_id=request.user.id,
                name=collect['name'].strip().split('.', 1)[0],
                url=collect['url'],
                parent_id=parent_id,
                record_type=1
            ) for collect in collect_list]
        # 批量插入收藏数据
        try:
            with transaction.atomic():
                FavoriteFolder.objects.bulk_create(collect_list)
        except Exception as e:
            return Response(return_code(1007, err=str(e)),
                status=status.HTTP_400_BAD_REQUEST)

        return Response(return_code(0, msg="批量收藏成功"))

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

