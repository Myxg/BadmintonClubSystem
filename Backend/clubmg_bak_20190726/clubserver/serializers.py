# coding: utf-8

import datetime

from rest_framework import serializers
from .models import *
from common.utils import ModelUpdateSerializer, lmd5sum
from common.pub_map import MATCH_TYPE

def match_sn_id():
    date_curr = datetime.datetime.now().strftime("%Y_%m%d_")
    match_info = MatchInfo.objects.filter(
        match_id__startswith=date_curr
    ).order_by('match_id').all()
    if match_info:
        match_id = list(match_info)[-1].match_id
        _id = "%04d" % (int(match_id.split('_')[-1]) + 1)
    else:
        _id = "0000"
    match_id = "{}{}".format(date_curr, _id)
    return match_id

class NewUserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'password1', 'password2', 'email', 'user_type')

class UserAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'user_role', 'user_type')

class UserUpdateEmailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    class Meta:
        model = User
        fields = ('email',)

class UserUpdatePhotoSerializer(serializers.ModelSerializer):
    profile_photo = serializers.models.ImageField(
        max_length=128,
        upload_to="static/img/profilephoto")
    class Meta:
        model = User
        fields = ('profile_photo', )
        
class UserSerializer(serializers.ModelSerializer):
    user_role_name = serializers.CharField(source='get_user_role_display')
    user_type_name = serializers.CharField(source='get_user_type_display')
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'user_role', 'user_role_name', 'user_type', 'user_type_name', 'profile_photo', 'group')

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'user_role', 'user_type')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'user', 'permission', 'resource')

class NewGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (u'name', )

class UpdateGroupSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = Group
        fields = (u'name', )
        unique_fields=((u'name', ), )

class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operation
        fields = '__all__'
        
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class AthleteCompanySerializer(serializers.ModelSerializer):
    contact_way = serializers.CharField(source='get_contact_way_display')
    class Meta:
        model = AthleteCompany
        fields = ('id', 'company_id', 'company_name', 'author_rep', 'credit_code', 'company_addr', 'contact', 'contact_way',
                  'context_info', 'created_at', 'updated_at')

class NewAthleteCompanySerializer(serializers.ModelSerializer):
    company_id = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(lmd5sum)
    )
    author_rep = serializers.CharField(max_length=64, allow_blank=True)
    credit_code = serializers.CharField(max_length=128, allow_blank=True)
    company_addr = serializers.CharField(max_length=1024, allow_blank=True)
    contact = serializers.CharField(max_length=64, allow_blank=True)
    context_info = serializers.CharField(max_length=64, allow_blank=True)
    class Meta:
        model = AthleteCompany
        fields = ('id', 'company_id', 'company_name', 'author_rep', 'credit_code', 'company_addr', 'contact', 'contact_way',
                  'context_info')

class UpdateAthleteCompanySerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    author_rep = serializers.CharField(max_length=64, allow_blank=True)
    credit_code = serializers.CharField(max_length=128, allow_blank=True)
    company_addr = serializers.CharField(max_length=1024, allow_blank=True)
    contact = serializers.CharField(max_length=64, allow_blank=True)
    context_info = serializers.CharField(max_length=64, allow_blank=True)
    class Meta:
        model = AthleteCompany
        fields = ('company_name', 'author_rep', 'credit_code', 'company_addr', 'contact', 'contact_way',
                  'context_info')
        unique_fields=((u'company_id', ), (u'company_name', ), )


class AthleteInfoSerializer(serializers.ModelSerializer):

    gender = serializers.CharField(source='get_gender_display')
    hand_held = serializers.CharField(source='get_hand_held_display')
    sport_level = serializers.CharField(source='get_sport_level_display')

    class Meta:
        model = AthleteInfo
        fields = ('id', 'athlete_id', 'company_id', 'company_name', 'name', 'english_name', 'gender', 'profile_photo', 'nationality', 'native_place',
                  'folk', 'birthday','sport_project', 'hand_held', 'sport_level', 'initial_training_time', 'first_coach',
                  'pro_team_coach', 'nat_team_coach', 'group', 'sport_events', 'created_at', 'updated_at')

class NewAthleteInfoSerializer(serializers.ModelSerializer):
    athlete_id = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(lmd5sum)
    )
    class Meta:
        model = AthleteInfo
        fields = ('id', 'athlete_id', 'company_id', 'name', 'english_name', 'gender', 'profile_photo', 'nationality',
                  'native_place', 'folk', 'birthday', 'sport_project', 'hand_held', 'sport_level', 'initial_training_time',
                  'first_coach', 'pro_team_coach', 'nat_team_coach')

class UpdateAthleteInfoSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = AthleteInfo
        fields = ('company_id', 'name', 'english_name', 'gender', 'profile_photo', 'nationality', 'native_place', 'folk', 'birthday',
                  'sport_project', 'hand_held', 'sport_level', 'initial_training_time', 'first_coach',
                  'pro_team_coach', 'nat_team_coach')
        #foreign_id_fields = (('company_id', AthleteCompany, 'company_id'), )
        unique_fields=((u'athlete_id', ), )

class SportEventExpSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source='get_event_type_display')
    class Meta:
        model = SportEventExp
        fields = ('id', 'sport_event_id', 'athlete_id', 'event_name', 'event_type', 'event_time', 'rank', 'rank_info',
                  'event_honor', 'event_honor_img01', 'event_honor_img02', 'event_honor_img03',  'created_at',
                  'updated_at')

class NewSportEventExpSerializer(serializers.ModelSerializer):
    sport_event_id = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(lmd5sum)
    )
    class Meta:
        model = SportEventExp
        fields = ('id', 'sport_event_id', 'athlete_id', 'event_name', 'event_type', 'event_time', 'rank', 'rank_info',
                  'event_honor', 'event_honor_img01', 'event_honor_img02', 'event_honor_img03')

class UpdateSportEventExpSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = SportEventExp
        fields = ('sport_event_id', 'event_name', 'event_type', 'event_time', 'rank', 'rank_info', 'event_honor',
                  'event_honor_img01', 'event_honor_img02', 'event_honor_img03')
        unique_fields = (('sport_event_id', ), )

class MarkMatchInfoSerializer(serializers.ModelSerializer):
    # 标注系统 match_info 表的序列化
    class Meta:
        model = MarkMatchInfo 
        fields = ('id', 'match_id', 'match_name')

class MatchInfoSerializer(serializers.ModelSerializer):
    match_type = serializers.CharField(source='get_match_type_display')
    match_result = serializers.CharField(source='get_match_result_display')
    class Meta:
        model = MatchInfo
        fields = ('id', 'match_id', 'level1', 'level2', 'match_type', 'match_name', 'match_date', 'player_a', 'player_a_id',
                  'player_b', 'player_b_id', 'winnum_a', 'winnum_b', 'match_result', 'match_round', 'memo', 'created_at',
                  'updated_at')

class NewMatchInfoSerializer(serializers.ModelSerializer):
    match_id = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(match_sn_id)
    )
    level1 =  serializers.CharField(max_length=32, allow_blank=True, default='')
    level2 =  serializers.CharField(max_length=32, allow_blank=True, default='')
    winnum_a = serializers.IntegerField(default=0)
    winnum_b = serializers.IntegerField(default=0)
    match_round = serializers.CharField(max_length=32, allow_blank=True, default='')
    memo = serializers.CharField(max_length=2048, allow_blank=True, default='')
    class Meta:
        model = MatchInfo
        fields = ('id', 'match_id', 'level1', 'level2', 'match_type', 'match_name', 'match_date', 'player_a', 'player_a_id',
                  'player_b', 'player_b_id', 'winnum_a', 'winnum_b', 'match_result', 'match_round', 'memo')

class UpdateMatchInfoSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    level1 =  serializers.CharField(max_length=32, allow_blank=True, default='')
    level2 =  serializers.CharField(max_length=32, allow_blank=True, default='')
    winnum_a = serializers.IntegerField(default=0)
    winnum_b = serializers.IntegerField(default=0)
    match_round = serializers.CharField(max_length=32, allow_blank=True, default='')
    memo = serializers.CharField(max_length=2048, allow_blank=True, default='')
    class Meta:
        model = MatchInfo
        fields = ('level1', 'level2', 'match_type', 'match_name', 'match_date', 'player_a', 'player_a_id',
                  'player_b', 'player_b_id', 'winnum_a', 'winnum_b', 'match_result', 'match_round', 'memo')

class RptHitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RptHits
        fields = ('matchid', 'frame_hit', 'frame_prev', 'frame_next', 'action', 'player', 'zone_start', 'height', 'zone_end',
                  'video', 'route')

class RptScoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = RptScores
        fields = ('matchid', 'game', 'score', 'score_a', 'score_b', 'a1num', 'a2num', 'serve', 'goal', 'frame_start', 'frame_end',
                  'duration', 'updown', 'video', 'route')

class RptServerecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RptServerecord
        fields = ('matchid', 'score_a', 'score', 'score_b', 'serve', 'hit', 'special_hit', 'land', 'game', 'video')

class RptPlaygroundrecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RptPlaygroundrecord
        fields = ('matchid', 'a', 'b', 'c', 'd', 'normal', 'game', 'video')

class WorldRankingSerializer(serializers.ModelSerializer):
    match_type = serializers.CharField(source='get_match_type_display')
    class Meta:
        model = WorldRanking
        fields = ('id', 'match_type', 'athlete_id', 'athlete', 'ranking', 'announcemented_at',
                  'created_at', 'updated_at')

class NewWorldRankinSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorldRanking
        fields = ('id', 'match_type', 'athlete_id', 'athlete', 'ranking', 'announcemented_at')

class UpdateWorldRankinSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = WorldRanking
        fields = ('match_type', 'athlete_id', 'athlete', 'ranking', 'announcemented_at')
        unique_fields = (('match_type', 'athlete_id', 'announcemented_at'), )

class OlympicRankingSerializer(serializers.ModelSerializer):
    match_type = serializers.CharField(source='get_match_type_display')
    class Meta:
        model = OlympicRanking
        fields = ('id', 'match_type', 'athlete_id', 'athlete', 'ranking', 'points', 'announcemented_at',
                  'created_at', 'updated_at')

class NewOlympicRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OlympicRanking
        fields = ('id', 'match_type', 'athlete_id', 'athlete', 'ranking', 'points', 'announcemented_at')

class UpdateOlympicRankingSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = OlympicRanking
        fields = ('match_type', 'athlete_id', 'athlete', 'ranking', 'points', 'announcemented_at')
        unique_fields = (('match_type', 'athlete_id', 'announcemented_at'), )

class PhysicalFitnessDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalFitnessData
        fields = ('id', 'fitness_item_id', 'fitness_item_name', 'fitness_test_date', 'fitness_test_value', 'unit', 'athlete_id',
                  'athlete_name', 'created_at', 'updated_at')

class NewPhysicalFitnessDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalFitnessData
        fields = ('id', 'fitness_item_id', 'fitness_test_date', 'fitness_test_value', 'athlete_id')

class UpdatePhysicalFitnessDataSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = PhysicalFitnessData
        fields = ('fitness_item_id', 'fitness_test_date', 'fitness_test_value', 'athlete_id')
        unique_fields = (('athlete_id', 'fitness_item_id', 'fitness_test_date'),)
        foreign_id_fields = (('athlete_id', AthleteInfo, 'athlete_id'), ('fitness_item_id', PhysicalFitnessItems, 'item_id'))

class AthleteGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteGroup
        fields = ('id', 'name', 'athlete')

class NewAthleteGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteGroup
        fields = ('name', )

class UpdateAthleteGroupSerializer(serializers.ModelSerializer, ModelUpdateSerializer):
    class Meta:
        model = AthleteGroup
        fields = ('name', )
        unique_fields=((u'name', ), )


class DocLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocLink
        fields = ('id', 'path', 'module_id', 'match_id_link', 'match_id_list', 'athlete_id_link', 'athlete_id_list',
            'match_type_link', 'match_type_list', 'tags_link', 'created_at', 'updated_at')

class NewDocLinkSerializer(serializers.ModelSerializer):
    match_id_link = serializers.CharField(max_length=255, allow_blank=True)
    athlete_id_link = serializers.CharField(max_length=255, allow_blank=True)
    match_type_link = serializers.CharField(max_length=32, allow_blank=True)
    tags_link = serializers.CharField(max_length=255, allow_blank=True)
    class Meta:
        model = DocLink
        fields = ('id', 'path', 'module_id', 'match_id_link', 'athlete_id_link', 'match_type_link', 'tags_link')
        
