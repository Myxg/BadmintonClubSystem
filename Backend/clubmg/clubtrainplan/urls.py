#coding: utf-8

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^athlete/(?P<athlete_id>[0-9a-z]{32})/trainplan/(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})$', views.TrainPlanAthleteView.as_view()),
    url(r'^athlete/trainplan/overview$', views.TrainPlanOverViewView.as_view()),
    url(r'^athlete/(?P<athlete_id>[0-9a-z]{32})/trainplan/empty$', views.TrainPlanEmpty.as_view()),
    url(r'^project/(?P<project>[0-9])/trainplan/(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})$', views.TrainPlanProjectView.as_view()),
    url(r'^project/trainplan/overview$', views.TrainPlanProjectOverViewView.as_view()),

    url(r'^athgroup/(?P<ath_group_id>[0-9]+)/trainplan/(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})$', views.TrainPlanAthGroupView.as_view()),
    url(r'^athgroup/trainplan/overview$', views.TrainPlanAthGroupOverViewView.as_view()),

    url(r'^athlete/(?P<athlete_id>[0-9a-z]{32})/amounttrainplan/(?P<day>[0-9]{4}-[0-9]{2}-[0-9]{2})$', views.TrainPlanAmountExerciseView.as_view()),
    url(r'^athlete/amounttrainplan/overview$', views.TrainPlanAmountExerciseOverViewView.as_view()),
]

