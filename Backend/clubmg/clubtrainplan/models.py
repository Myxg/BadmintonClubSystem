# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections

from django.db import models
from django.utils.timezone import now

from clubserver.models import AthleteGroup
from common.pub_map import MATCH_TYPE

# Create your models here.

class TrainContent(models.Model):
    elam_started_at = models.TimeField(blank=True, null=True)
    elam_ended_at = models.TimeField(blank=True, null=True)
    elam_content = models.CharField(max_length=255, default='')
    elam_exercise_amount = models.CharField(max_length=64, default='')
    am_started_at = models.TimeField(blank=True, null=True)
    am_ended_at = models.TimeField(blank=True, null=True)
    am_content = models.CharField(max_length=255, default='')
    am_exercise_amount = models.CharField(max_length=64, default='')
    pm_started_at = models.TimeField(blank=True, null=True)
    pm_ended_at = models.TimeField(blank=True, null=True)
    pm_content = models.CharField(max_length=255, default='')
    pm_exercise_amount = models.CharField(max_length=64, default='')
    night_started_at = models.TimeField(blank=True, null=True)
    night_ended_at = models.TimeField(blank=True, null=True)
    night_content = models.CharField(max_length=255, default='')
    night_exercise_amount = models.CharField(max_length=64, default='')
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'train_content'


class TrainPlanAthleteLink(models.Model):
    train_content_id = models.IntegerField()
    day = models.DateField()
    athlete_id = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'train_plan_athlete_link'
        unique_together = (('athlete_id', 'day'),)

    @property
    def day_str(self):
        return self.day.strftime('%Y-%m-%d')

class ProjectTrainContent(models.Model):
    elam_started_at = models.TimeField(blank=True, null=True)
    elam_ended_at = models.TimeField(blank=True, null=True)
    elam_content = models.CharField(max_length=255, default='')
    elam_exercise_amount = models.CharField(max_length=64, default='')
    am_started_at = models.TimeField(blank=True, null=True)
    am_ended_at = models.TimeField(blank=True, null=True)
    am_content = models.CharField(max_length=255, default='')
    am_exercise_amount = models.CharField(max_length=64, default='')
    pm_started_at = models.TimeField(blank=True, null=True)
    pm_ended_at = models.TimeField(blank=True, null=True)
    pm_content = models.CharField(max_length=255, default='')
    pm_exercise_amount = models.CharField(max_length=64, default='')
    night_started_at = models.TimeField(blank=True, null=True)
    night_ended_at = models.TimeField(blank=True, null=True)
    night_content = models.CharField(max_length=255, default='')
    night_exercise_amount = models.CharField(max_length=64, default='')
    day = models.DateField(db_index=True)
    project = models.IntegerField(choices=MATCH_TYPE, db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'project_train_content'
        unique_together = (('day', 'project'),)

    @property
    def day_str(self):
        return self.day.strftime('%Y-%m-%d')

class AthgroupTrainContent(models.Model):
    elam_started_at = models.TimeField(blank=True, null=True)
    elam_ended_at = models.TimeField(blank=True, null=True)
    elam_content = models.CharField(max_length=255, default='')
    elam_exercise_amount = models.CharField(max_length=64, default='')
    am_started_at = models.TimeField(blank=True, null=True)
    am_ended_at = models.TimeField(blank=True, null=True)
    am_content = models.CharField(max_length=255, default='')
    am_exercise_amount = models.CharField(max_length=64, default='')
    pm_started_at = models.TimeField(blank=True, null=True)
    pm_ended_at = models.TimeField(blank=True, null=True)
    pm_content = models.CharField(max_length=255, default='')
    pm_exercise_amount = models.CharField(max_length=64, default='')
    night_started_at = models.TimeField(blank=True, null=True)
    night_ended_at = models.TimeField(blank=True, null=True)
    night_content = models.CharField(max_length=255, default='')
    night_exercise_amount = models.CharField(max_length=64, default='')
    day = models.DateField(db_index=True)
    ath_group_id = models.IntegerField(db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'athgroup_train_content'
        unique_together = (('day', 'ath_group_id'),)

    @property
    def day_str(self):
        return self.day.strftime('%Y-%m-%d')

    @property
    def ath_group_name(self):
        ath_group = AthleteGroup.objects.filter(pk = self.ath_group_id).first()
        if ath_group:
            return ath_group.name
        return ''

class AmountExerciseTrainContent(models.Model):
    skill_tactic = models.IntegerField(default=0)
    small_technology = models.IntegerField(default=0)
    strength = models.IntegerField(default=0)
    special_item = models.IntegerField(default=0)
    day = models.DateField(db_index=True)
    athlete_id = models.CharField(max_length=32, db_index=True)
    user_id = models.IntegerField(db_index=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'amount_exercise_train_content'
        unique_together = (('day', 'athlete_id'),)

    @property
    def day_str(self):
        return self.day.strftime('%Y-%m-%d')

