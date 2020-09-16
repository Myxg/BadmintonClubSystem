#coding: utf-8

from django.conf.urls import include, url

from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    url(r'^token-auth$', obtain_jwt_token),
    url(r'^useradd$', views.UserAdd.as_view()),
    url(r'^user$', views.UserView.as_view()),
    url(r'^user/password$', views.UpdatePassword.as_view()),
    url(r'^user/email$', views.UpdateEmail.as_view()),
    url(r'^user/photo$', views.UpdatePhoto.as_view()),
    url(r'^user/(?P<user_id>[0-9]+)$', views.EditUserView.as_view()),
    url(r'^users$', views.UsersView.as_view()),

    url(r'^group/(?P<pk_id>[0-9]+)$', views.GroupView.as_view()),
    url(r'^groups$', views.GroupsView.as_view()),

    url(r'^operations$', views.OperationsView.as_view()),
    url(r'^permissions$', views.PermissionsView.as_view()),

    url(r'^athlete/(?P<pk_id>[0-9]+)$', views.AthleteView.as_view()),
    url(r'^athletes$', views.AthletesView.as_view()),
    url(r'^athlete/company/(?P<pk_id>[0-9]+)$', views.AthleteCompanyView.as_view()),
    url(r'^athlete/companys$', views.AthleteCompanysView.as_view()),
    url(r'^athlete/sportevent/(?P<pk_id>[0-9]+)$', views.SportEventExpView.as_view()),
    url(r'^athlete/group/(?P<pk_id>[0-9]+)$', views.AthleteGroupView.as_view()),
    url(r'^athlete/groups$', views.AthleteGroupsView.as_view()),
    url(r'^athlete/fitness/items$', views.FitnessItemsView.as_view()),
    url(r'^athlete/fitness/datas$', views.FitnessDatasView.as_view()),
    url(r'^athlete/fitness/data/(?P<pk_id>[0-9]+)$', views.FitnessDataView.as_view()),
    url(r'^athlete/worldrankinglist$', views.WorldRankingListView.as_view()),
    url(r'^athlete/worldranking/(?P<pk_id>[0-9]+)$', views.WorldRankingView.as_view()),
    url(r'^athlete/olympicrankinglist$', views.OlympicRankingListView.as_view()),
    url(r'^athlete/olympicranking/(?P<pk_id>[0-9]+)$', views.OlympicRankingView.as_view()),

    url(r'^athlete/overview/(?P<pk_id>[0-9]+)$', views.AthleteOverViewView.as_view()),
    url(r'^athlete/linkdocs/(?P<pk_id>[0-9]+)$', views.AthleteDocLinkView.as_view()),
    url(r'^athlete/matchs/(?P<pk_id>[0-9]+)$', views.AthleteMatchVideosSearchView.as_view()),

    url(r'^video/(?P<pk_id>[0-9]+)$', views.MatchVideoView.as_view()),
    url(r'^videos$', views.MatchVideosSearchView.as_view()),

    url(r'^matchinfo/(?P<pk_id>[0-9]+)$', views.MatchInfoView.as_view()),
    url(r'^matchinfos$', views.MatchInfosView.as_view()),
    url(r'^matchlist$', views.MatchListView.as_view()),
    url(r'^matchlevel2list$', views.MatchLevel2NameView.as_view()),

    url(r'^markdata/matchinfos$', views.MarkMatchInfosView.as_view()),
    url(r'^markdata/show/(?P<name>(hits|scores|serverecord|playgroundrecord))/(?P<match_id>[0-9]{4}_[0-9]{4}_[0-9]{4})$', views.MarkDataShow.as_view()),
    url(r'^markdata/sync/(?P<name>(hits|scores|serverecord|playgroundrecord))/(?P<match_id>[0-9]{4}_[0-9]{4}_[0-9]{4})$', views.MarkDataSync.as_view()),
    url(r'^markdata/sync/(?P<name>(hits|scores))/(?P<match_id>[0-9]{4}_[0-9]{4}_[0-9]{4})/retry$', views.MarkDataSyncRetry.as_view()),


    url(r'^docs/(?P<module_id>[a-zA-Z0-9_]+)(/)?$', views.DocsView.as_view()),
    url(r'^docs/link/(?P<module_id>[a-zA-Z0-9_]+)(/)?$', views.DocLinkView.as_view()),
    url(r'^history/(?P<module_id>[a-zA-Z0-9_]+)(/)?$', views.DocsView.as_view()),

    url(r'^companylist$', views.CompanysListView.as_view()),

    # test url
    url(r'^sn/(?P<type_id>[a-z]+)$', views.NewSN.as_view()),
    url(r'^test$', views.Test.as_view()),
]

