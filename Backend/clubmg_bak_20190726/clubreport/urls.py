#coding: utf-8

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^matchinfo/report/hits$', views.MatchHitsView.as_view()),
    url(r'^matchinfo/report/hits/sum$', views.MatchHitsSumView.as_view()),
    url(r'^matchinfo/report/scores$', views.MatchScoresReportView.as_view()),
    url(r'^matchinfo/report/scores/table$', views.MatchScoresReportTableView.as_view()),
    url(r'^matchinfo/report/beats$', views.MatchBeatsReportView.as_view()),
    url(r'^matchinfo/report/double/serve$', views.DoubleMatchServeView.as_view()),
    url(r'^matchinfo/report/double/start5beat$', views.MatchStart5BeatReportView.as_view()),
    url(r'^athlete/report/worldrank$', views.WorldRankingReportView.as_view()),
    url(r'^athlete/report/olympicranking$', views.OlympicRankingReportView.as_view()),
    url(r'^athlete/report/ranking/(?P<pk_id>[0-9]+)$', views.AthleteRankingReportView.as_view()),
]

