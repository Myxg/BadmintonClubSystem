# coding: utf-8

import re

from django.conf import settings
from rest_framework.permissions import BasePermission

from .models import (
    User, Group, UserGroup, Operation, GroupPermission,
    Permission, OperationPermission
)

class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        """
        行为权限验证
        """

        self.message = "权限不允许"
        user = request.user

        # 管理员放行
        if all((user, user.is_staff, user.username == 'admin')):
            return True

        for group in  user.group:
            if group['name'] == u'管理员':
                return True

        # 获取 user 组
        user_groups = UserGroup.objects.filter(user_id = user.id).all()
        if not user_groups:
            return False

        # 获取用户组对应的权限
        permissions = []
        for user_group in user_groups:
            permissions += GroupPermission.objects.filter(group_id = user_group.group_id).all()

        if not permissions:
            return False

        # 获取权限对应的行为
        operations = []
        for permission in permissions:
            operation_permissions = OperationPermission.objects.filter(permission_id = permission.permission_id).all()
            for operation_permission in operation_permissions:
                operations += operation_permission.operation

        if not operations:
            return False

        # 验证行为是否有权限
        for operation in operations:
            path = request.path.replace('/{}'.format(settings.API_PREFIX), '', 1)
            if request.method.upper() == operation['method'].upper() and \
                re.search(r'{}'.format(operation['url']), path):
                return True
            else:
                continue
        return False

