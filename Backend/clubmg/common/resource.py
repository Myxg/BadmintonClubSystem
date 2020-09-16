# coding: utf-8

from django.conf import settings
from django.db.models import Q

from clubserver.models import UserResourceLink

def get_resource_by_user(request, resource_type):
    """
    根据当前登陆的用户，获取 resource_type 类型的所有有权限的资源

    """

    model_name, obj_name = settings.RESOURCE_TYPE_MAP[resource_type].rsplit('.', 1)
    model = __import__(model_name, None, None, [obj_name])
    model_obj = getattr(model, obj_name)

    if request.user.username == 'admin':
        return model_obj.objects

    group_ids = [group['id'] for group in request.user.group]
    user_ids = list(set(group_ids + [request.user.id]))

    resources = UserResourceLink.objects.filter(
        resource_type__in =  [resource_type, "{}_group".format(resource_type)],
        user_id__in = user_ids,
    ).all()

    resource_ids = []

    for resource in resources:
        resource_ids += resource.resource_ids

    resource_ids = list(set(resource_ids))

    return model_obj.objects.filter(pk__in = resource_ids)

def new_resource_by_user(request, resource_type, resource_pk_id):
    """
    根据当前登陆用户，创建资源所属关系记录
    """

    if request.user.username == 'admin':
        return

    resource = UserResourceLink(
        user_id=request.user.id,
        user_id_type='user',
        resource_type=resource_type,
        resource_id=resource_pk_id,
        resource_id_type= 1 if resource_type.endswith('_group') else 0
    )
    resource.save()

def del_resource_by_user(request, resource_type, resource_pk_id):
    """
    根据当前登陆用户，删除所属关系记录
    """

    if request.user.username == 'admin':
        return

    resource = UserResourceLink.objects.filter(
        user_id=request.user.id,
        user_id_type='user',
        resource_type=resource_type,
        resource_id=resource_pk_id,
    ).delete()

def get_resource_by_id(resource_type, pk_ids):
    model_name, obj_name = settings.RESOURCE_TYPE_MAP[resource_type].rsplit('.', 1)
    model = __import__(model_name, None, None, [obj_name])
    model_obj = getattr(model, obj_name)
    #objs = model_obj.objects.filter(pk__in = pk_ids).values_list('id', 'name')
    objs = model_obj.objects.filter(pk__in = pk_ids).order_by('id').all()
    data = []
    for obj in objs:
        data.append(
            {
                "id": obj.id,
                "name": obj.name
            }
        )
    return data

def get_resource_column_by_user(request, resource_type, column='id'):

    resource_obj = get_resource_by_user(request, resource_type)
    column_values = resource_obj.values_list(column, flat=True)
    
    return column_values

def get_match_by_user(request, model):

    if request.user.username == 'admin':
        return model.objects

    athletes = get_resource_by_user(request, 'athlete')
    athlete_ids = athletes.values_list('athlete_id', flat=True)

    match_obj = model.objects

    q_or = Q()
    q_or.connector = 'OR'

    for athlete_id in athlete_ids:
        q_or.children.append(('player_a_id__icontains', athlete_id))
        q_or.children.append(('player_b_id__icontains', athlete_id))

    match_obj = match_obj.filter(q_or)
    return match_obj

def get_doc_link_by_user(request, model):

    if request.user.username == 'admin':
        return model.objects
    
    athlete_ids = get_resource_column_by_user(request, 'athlete', 'athlete_id')

    doc_obj = model.objects

    q_or = Q()
    q_or.connector = 'OR'

    for athlete_id in athlete_ids:
        q_or.children.append(('athlete_id_link__icontains', athlete_id))

    doc_obj = doc_obj.filter(q_or)
    return doc_obj

def get_ranking_by_user(request, model):
    
    if request.user.username == 'admin':
        return model.objects
    
    athlete_ids = get_resource_column_by_user(request, 'athlete', 'athlete_id')

    ranking_obj = model.objects

    q_or = Q()
    q_or.connector = 'OR'

    for athlete_id in athlete_ids:
        q_or.children.append(('athlete_id__icontains', athlete_id))

    ranking_obj = ranking_obj.filter(q_or)

    return ranking_obj

def get_fitness_by_user(request, model):
    
    if request.user.username == 'admin':
        return model.objects

    athlete_ids = get_resource_column_by_user(request, 'athlete', 'athlete_id')
    fitness_obj = model.objects.filter(athlete_id__in = athlete_ids)

    return fitness_obj

