# -*- coding: utf-8 -*-
from django.dispatch import Signal

team_join_approved = Signal(providing_args=[
    'nt', 'context', 'project', 'team', 'access_request', 'error_msg',
])
team_join_denied = Signal(providing_args=[
    'nt', 'context', 'project', 'team', 'access_request', 'error_msg',
])
