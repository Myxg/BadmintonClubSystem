# coding: utf-8

import datetime

from rest_framework import serializers

from .models import *
from common.utils import ModelUpdateSerializer, lmd5sum


class TrainContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainContent
        fields = (
            'id', 'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount',
            'created_at', 'updated_at'
        )

class NewTrainContentSerializer(serializers.ModelSerializer):
    elam_started_at = serializers.TimeField(allow_null=True, default=None)
    elam_ended_at = serializers.TimeField(allow_null=True, default=None)
    elam_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    elam_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    am_started_at = serializers.TimeField(allow_null=True, default=None)
    am_ended_at = serializers.TimeField(allow_null=True, default=None)
    am_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    am_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    pm_started_at = serializers.TimeField(allow_null=True, default=None)
    pm_ended_at = serializers.TimeField(allow_null=True, default=None)
    pm_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    pm_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    night_started_at = serializers.TimeField(allow_null=True, default=None)
    night_ended_at = serializers.TimeField(allow_null=True, default=None)
    night_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    night_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    class Meta:
        model = TrainContent
        fields = (
            'id', 'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount', 'user_id'
        )


class ProjectTrainContentSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='get_project_display')
    class Meta:
        model = ProjectTrainContent
        fields = (
            'id', 'day', 'project', 'project_name',
            'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount',
            'created_at', 'updated_at'
        )

class NewProjectTrainContentSerializer(serializers.ModelSerializer):
    elam_started_at = serializers.TimeField(allow_null=True, default=None)
    elam_ended_at = serializers.TimeField(allow_null=True, default=None)
    elam_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    elam_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    am_started_at = serializers.TimeField(allow_null=True, default=None)
    am_ended_at = serializers.TimeField(allow_null=True, default=None)
    am_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    am_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    pm_started_at = serializers.TimeField(allow_null=True, default=None)
    pm_ended_at = serializers.TimeField(allow_null=True, default=None)
    pm_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    pm_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    night_started_at = serializers.TimeField(allow_null=True, default=None)
    night_ended_at = serializers.TimeField(allow_null=True, default=None)
    night_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    night_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    class Meta:
        model = ProjectTrainContent
        fields = (
            'id', 'day', 'project',
            'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount',
            'user_id'
        )

class AthgroupTrainContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthgroupTrainContent
        fields = (
            'id', 'day', 'ath_group_id', 'ath_group_name',
            'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount',
            'created_at', 'updated_at'
        )

class NewAthgroupTrainContentSerializer(serializers.ModelSerializer):
    elam_started_at = serializers.TimeField(allow_null=True, default=None)
    elam_ended_at = serializers.TimeField(allow_null=True, default=None)
    elam_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    elam_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    am_started_at = serializers.TimeField(allow_null=True, default=None)
    am_ended_at = serializers.TimeField(allow_null=True, default=None)
    am_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    am_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    pm_started_at = serializers.TimeField(allow_null=True, default=None)
    pm_ended_at = serializers.TimeField(allow_null=True, default=None)
    pm_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    pm_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    night_started_at = serializers.TimeField(allow_null=True, default=None)
    night_ended_at = serializers.TimeField(allow_null=True, default=None)
    night_content = serializers.CharField(max_length=255, allow_blank=True, default='')
    night_exercise_amount = serializers.CharField(max_length=64, allow_blank=True, default='')
    class Meta:
        model = AthgroupTrainContent
        fields = (
            'id', 'day', 'ath_group_id',
            'elam_started_at', 'elam_ended_at', 'elam_content', 'elam_exercise_amount',
            'am_started_at', 'am_ended_at', 'am_content', 'am_exercise_amount',
            'pm_started_at', 'pm_ended_at', 'pm_content', 'pm_exercise_amount',
            'night_started_at', 'night_ended_at', 'night_content', 'night_exercise_amount',
            'created_at', 'updated_at',
            'user_id'
        )

class AmountExerciseTrainContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmountExerciseTrainContent
        fields = (
            'id', 'day', 'athlete_id',
            'skill_tactic', 'small_technology', 'strength', 'special_item',
            'created_at', 'updated_at'
        )

class NewAmountExerciseTrainContentSerializer(serializers.ModelSerializer):
    skill_tactic = serializers.IntegerField(default=0)
    small_technology = serializers.IntegerField(default=0)
    strength = serializers.IntegerField(default=0)
    special_item = serializers.IntegerField(default=0)
    class Meta:
        model = AmountExerciseTrainContent
        fields = (
            'id', 'day', 'athlete_id', 'user_id',
            'skill_tactic', 'small_technology', 'strength', 'special_item',
        )
