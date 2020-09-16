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

from common.resource import (
    get_resource_by_user, get_resource_column_by_user
)
from common.modelquery import (
    model_query, model_query_get, model_query_first, model_query_column_list
)
from common.utils import (
    CustomPageNumberPagination, return_code, lmd5sum
)
from .models import (
    TrainContent, TrainPlanAthleteLink, ProjectTrainContent,
    AthgroupTrainContent,
    AmountExerciseTrainContent
)
from .serializers import (
    TrainContentSerializer, NewTrainContentSerializer,
    ProjectTrainContentSerializer, NewProjectTrainContentSerializer,
    AmountExerciseTrainContentSerializer, NewAmountExerciseTrainContentSerializer,
    AthgroupTrainContentSerializer, NewAthgroupTrainContentSerializer
)

# Create your views here.

class TrainPlanAthleteView(APIView):
    
    def get(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        train_plan_link = model_query_first(TrainPlanAthleteLink, query={'athlete_id': athlete_id, 'day': day})
        if not train_plan_link:
            return Response(return_code(0, data={}))
        train_content = model_query_first(TrainContent, query={'id': train_plan_link.train_content_id})
        if not train_content:
            return Response(return_code(0, data={}))
        train_content_s = TrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def put(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        post_data = request.data
        post_data['user_id'] = request.user.id
        train_content_s = NewTrainContentSerializer(data=post_data)
        if not train_content_s.is_valid():           
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            train_content_s.save()
            train_plan_link = TrainPlanAthleteLink(
                train_content_id = train_content_s.data['id'],
                day = day,
                athlete_id = athlete_id
            )
            train_plan_link.save()
        train_content = model_query_get(TrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = TrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def post(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        train_plan_link = model_query_get(TrainPlanAthleteLink, query={'athlete_id': athlete_id, 'day': day})
        train_content = model_query_get(TrainContent, query={'id': train_plan_link.train_content_id})

        post_data = request.data
        post_data['user_id'] = train_content.user_id
        train_content_s = NewTrainContentSerializer(instance=train_content, data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)
        train_content_s.save()
        train_content = model_query_get(TrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = TrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

        
    def delete(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        train_plan_link = model_query_first(TrainPlanAthleteLink, query={'athlete_id': athlete_id, 'day': day})
        if train_plan_link:
            train_content = model_query_first(TrainContent, query={'id': train_plan_link.train_content_id})
            if train_content:
                train_content.delete()
            train_plan_link.delete()
        return Response(return_code(0, u'删除成功'))

class TrainPlanOverViewView(APIView):

    def get(self, request):
        query_is = ['athlete_id']
        query_range = ['day']
        query_set = collections.OrderedDict()

        is_details = request.GET.get('is_details')

        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        for q in query_range:
            if '{}_from'.format(q) in request.GET and request.GET['{}_from'.format(q)]:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET and request.GET['{}_to'.format(q)]:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]

        train_plan_links = model_query(TrainPlanAthleteLink, query=query_set, order_by=['day'])
        pg = CustomPageNumberPagination()
        page_datas = pg.paginate_queryset(queryset=train_plan_links, request=request, view=self)
        data = collections.OrderedDict()
        if is_details == 'true':
            fields = TrainContentSerializer.Meta.fields
            for tpl in page_datas:
                train_content = model_query_first(TrainContent, query={"id": tpl.train_content_id})
                if train_content:
                    tmp = collections.OrderedDict()
                    for item in fields:
                        tmp[item] = getattr(train_content, item)
                    data[tpl.day_str] = tmp
        else:
            for tpl in page_datas:
                data[tpl.day_str] = True

        return pg.get_paginated_response(data)

class TrainPlanEmpty(APIView):

    def delete(self, request, athlete_id):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        
        query_range = ['day']
        query_set = collections.OrderedDict()

        for q in query_range:
            if '{}_from'.format(q) in request.GET and request.GET['{}_from'.format(q)]:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET and request.GET['{}_to'.format(q)]:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]

        train_plan_links = model_query(TrainPlanAthleteLink, query=query_set, order_by=['day'])
        train_plan_ids = [tpl.train_content_id for tpl in train_plan_links]

        train_contents = model_query(TrainContent, query={'id__in': train_plan_ids})
        
        with transaction.atomic():
            train_plan_links.delete()
            train_contents.delete()

        return Response(return_code(0, msg=u'删除成功'))

class TrainPlanProjectView(APIView):

    def get(self, request, project, day):
        query = {
            'day': day,
            'project': project,
            #'user_id': request.user.id
        }
        train_content = model_query_first(ProjectTrainContent, query=query)
        if not train_content:
            return Response(return_code(0, data={}))
        train_content_s = ProjectTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))        


    def put(self, request, project, day):
        post_data = request.data
        post_data['day'] = day
        post_data['user_id'] = request.user.id
        post_data['project'] = project
        
        train_content_s = NewProjectTrainContentSerializer(data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        train_content_s.save()
        train_content = model_query_get(ProjectTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = ProjectTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))


    def post(self, request, project, day):
        query = {
            'day': day,
            'project': project,
            #'user_id': request.user.id
        }
        train_content = model_query_get(ProjectTrainContent, query=query)
        
        post_data = request.data
        post_data['day'] = day
        post_data['user_id'] = request.user.id
        post_data['project'] = project
    
        train_content_s = NewProjectTrainContentSerializer(instance=train_content, data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)
        
        train_content_s.save()
        train_content = model_query_get(ProjectTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = ProjectTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))


    def delete(self, request, project, day):
        query = {
            'day': day,
            'project': project,
            #'user_id': request.user.id
        }
        model_query(ProjectTrainContent, query=query).delete()
        return Response(return_code(0, u'删除成功'))


class TrainPlanProjectOverViewView(APIView):

    def get(self, request):

        query_is = ['project']
        query_range = ['day']
        query_set = collections.OrderedDict()

        is_details = request.GET.get('is_details')       

        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        #query_set['user_id'] = request.user.id

        for q in query_range:
            if '{}_from'.format(q) in request.GET and request.GET['{}_from'.format(q)]:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET and request.GET['{}_to'.format(q)]:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]

        train_contents = model_query(ProjectTrainContent, query=query_set, order_by=['day'])
        pg = CustomPageNumberPagination()
        page_datas = pg.paginate_queryset(queryset=train_contents, request=request, view=self)
        data = collections.OrderedDict()

        if is_details == 'true':
            for tc in page_datas:
                data[tc.day_str] = ProjectTrainContentSerializer(tc).data
        else:
            for tc in page_datas:
                data[tc.day_str] = True
        return pg.get_paginated_response(data)        

class TrainPlanAthGroupView(APIView):

    def get(self, request, ath_group_id, day):
        query = {
            'day': day,
            'ath_group_id': ath_group_id,
        }
        train_content = model_query_first(AthgroupTrainContent, query=query)
        if not train_content:
            return Response(return_code(0, data={}))
        train_content_s = AthgroupTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def put(self, request, ath_group_id, day):
        post_data = request.data
        post_data['day'] = day
        post_data['user_id'] = request.user.id
        post_data['ath_group_id'] = ath_group_id

        train_content_s = NewAthgroupTrainContentSerializer(data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        train_content_s.save()
        train_content = model_query_get(AthgroupTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = AthgroupTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def post(self, request, ath_group_id, day):
        
        query = {
            'day': day,
            'ath_group_id': ath_group_id,
        }
        train_content = model_query_get(AthgroupTrainContent, query=query)

        post_data = request.data
        post_data['day'] = day
        post_data['user_id'] = request.user.id
        post_data['ath_group_id'] = ath_group_id

        train_content_s = NewAthgroupTrainContentSerializer(instance=train_content, data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        train_content_s.save()
        train_content = model_query_get(AthgroupTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = AthgroupTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def delete(self, request, ath_group_id, day):
        query = {
            'day': day,
            'ath_group_id': ath_group_id,
        }
        model_query(AthgroupTrainContent, query=query).delete()
        return Response(return_code(0, u'删除成功'))

class TrainPlanAthGroupOverViewView(APIView):

    def get(self, request):

        query_is = ['ath_group_id']
        query_range = ['day']
        query_set = collections.OrderedDict()

        is_details = request.GET.get('is_details')       

        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        for q in query_range:
            if '{}_from'.format(q) in request.GET and request.GET['{}_from'.format(q)]:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET and request.GET['{}_to'.format(q)]:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]

        train_contents = model_query(AthgroupTrainContent, query=query_set, order_by=['day'])
        pg = CustomPageNumberPagination()
        page_datas = pg.paginate_queryset(queryset=train_contents, request=request, view=self)
        data = collections.OrderedDict()

        if is_details == 'true':
            for tc in page_datas:
                data[tc.day_str] = AthgroupTrainContentSerializer(tc).data
        else:
            for tc in page_datas:
                data[tc.day_str] = True
        return pg.get_paginated_response(data)        

class TrainPlanAmountExerciseView(APIView):

    def get(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()

        query = {
            'day': day,
            'athlete_id': athlete_id,
        }
        
        train_content = model_query_first(AmountExerciseTrainContent, query=query)
        if not train_content:
            return Response(return_code(0, data={}))
        train_content_s = AmountExerciseTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))

    def put(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404() 
        post_data = request.data
        post_data['day'] = day
        post_data['athlete_id'] = athlete_id
        post_data['user_id'] = request.user.id

        train_content_s = NewAmountExerciseTrainContentSerializer(data = post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        train_content_s.save()
        train_content = model_query_get(AmountExerciseTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = AmountExerciseTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))


    def post(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        
        query = {
            'day': day,
            'athlete_id': athlete_id,
        }
        train_content = model_query_get(AmountExerciseTrainContent, query=query)

        post_data = request.data
        post_data['day'] = day
        post_data['athlete_id'] = athlete_id
        post_data['user_id'] = request.user.id

        train_content_s = NewAmountExerciseTrainContentSerializer(instance=train_content, data=post_data)
        if not train_content_s.is_valid():
            return Response(return_code(2001, detail=train_content_s.errors),
                status=status.HTTP_400_BAD_REQUEST)

        train_content_s.save()
        train_content = model_query_get(AmountExerciseTrainContent, query={"pk": train_content_s.data['id']})
        train_content_s = AmountExerciseTrainContentSerializer(train_content)
        return Response(return_code(0, data=train_content_s.data))
        

    def delete(self, request, athlete_id, day):
        athlete_ids = get_resource_column_by_user(request, 'athlete', column='athlete_id')
        if athlete_id not in athlete_ids:
            raise Http404()
        query = {
            'day': day,
            'athlete_id': athlete_id,
        }
        model_query_get(AmountExerciseTrainContent, query=query).delete()
        return Response(return_code(0, u'删除成功'))

class TrainPlanAmountExerciseOverViewView(APIView):

    def get(self, request):
        query_is = ['athlete_id']
        query_range = ['day']
        query_set = collections.OrderedDict()

        is_details = request.GET.get('is_details')

        for q in query_is:
            if q in request.GET:
                query_set[q] = request.GET[q]

        for q in query_range:
            if '{}_from'.format(q) in request.GET and request.GET['{}_from'.format(q)]:
                query_set['{}__gte'.format(q)] = request.GET['{}_from'.format(q)]
            if '{}_to'.format(q) in request.GET and request.GET['{}_to'.format(q)]:
                query_set['{}__lte'.format(q)] = request.GET['{}_to'.format(q)]


        train_contents = model_query(AmountExerciseTrainContent, query=query_set, order_by=['day'])
        data = collections.OrderedDict()

        data['total'] = collections.OrderedDict((
            ('skill_tactic', 0),
            ('small_technology', 0),
            ('strength', 0),
            ('special_item', 0),

        ))

        for tc in train_contents:
            data['total']['skill_tactic'] += tc.skill_tactic
            data['total']['small_technology'] += tc.small_technology
            data['total']['strength'] += tc.strength
            data['total']['special_item'] += tc.special_item
            if is_details == 'true':
                data[tc.day_str] = AmountExerciseTrainContentSerializer(tc).data
            else:
                data[tc.day_str] = True
                
        return Response(return_code(0, data=data))

