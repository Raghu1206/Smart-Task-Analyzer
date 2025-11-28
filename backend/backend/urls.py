from django.urls import path, include


urlpatterns = [
path('api/', include('tasks_app.urls')),
]