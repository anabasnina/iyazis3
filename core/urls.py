"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path

from essay_generator.views import index, FileFieldView, document

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('upload/', FileFieldView.as_view(), name='upload'),
    re_path(r'^document/(?P<pk>\w+)/(?P<sum_type>\w+)$', document, name='document')
]
