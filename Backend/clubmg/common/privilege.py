# coding: utf-8

import collections

from django.conf import settings

from clubserver.models import MenuModule, UserMenuPrivilegeLink

def get_Privilege_by_user(request):
    """
    根据当前登陆的用户，获取相应模块的最大权限

    """
    menus = MenuModule.objects.order_by('id').all()

    data = []
    mp_map = collections.defaultdict(dict)
    
    for menu in menus:
        mp_map[menu.menu_module_id] = {
            "name": menu.name,
            "menu_module_id": menu.menu_module_id,
            "privilege_name": u"无权限",
            "privilege_id": 0
            
        }
    
    if request.user.username == 'admin':
        for menu in menus:
            data.append(
                {
                    "menu_module_id": menu.menu_module_id,
                    "menu_module_name": menu.name,
                    "privilege_name": u"全部",
                    "privilege_id": 2
                }
            )
        return data

    group_ids = [group['id'] for group in request.user.group]
    user_ids = list(set(group_ids + [request.user.id]))

    menu_privileges = UserMenuPrivilegeLink.objects.filter(
        user_id__in = user_ids,
    ).all()


    for mp in menu_privileges:
        if mp.privilege_id > mp_map[mp.menu_module_id]['privilege_id']:
            mp_map[mp.menu_module_id]['privilege_id'] = mp.privilege_id
            mp_map[mp.menu_module_id]['privilege_name'] = mp.privilege_name

    for mp in mp_map:
        data.append(mp_map[mp])

    return data
            
