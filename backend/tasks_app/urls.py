from django.urls import path
from . import views


urlpatterns = [
path('tasks/analyze/', views.AnalyzeTasksView.as_view(), name='analyze'),
path('tasks/suggest/', views.SuggestTasksView.as_view(), name='suggest'),
]