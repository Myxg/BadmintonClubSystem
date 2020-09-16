# coding: utf-8

from django.conf import settings
from django.db.models import Q

def model_query_column_list(model, query={}, order_by=['id'], column=['id']):

    column = column if column else ['id']
    obj = model.objects.filter(**query).order_by(*order_by)

    if len(column) == 1:
        return obj.values_list(column[0], flat=True)
    else:
        return obj.values_list(**column)
        

def model_query(model, query={}, order_by=['id']):
    obj = model.objects.filter(**query).order_by(*order_by)
    return obj

def model_query_get(model, query={}):
    obj = model.objects.get(**query)
    return obj
    

def model_query_first(model, query={}):
    obj = model.objects.filter(**query).first()
    return obj
