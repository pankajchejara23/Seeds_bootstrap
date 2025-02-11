"""seeds_bootstrap URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
"""SEEDS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from . import views
from django.conf.urls.i18n import i18n_patterns
from register import views as v
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import admin
urlpatterns = i18n_patterns(
    path('', views.index, name='home'),
    path('admin/', admin.site.urls),
    path("register/", v.register, name="register"),

    path("password_reset/", v.password_reset_request, name='password_reset'),
    path("password_reset/done", auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'), name='password_reset_done'),
    path('password_reset/confirm/<slug:uidb64>/<slug:token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="sign_pwd_reset_step2.html"), name='password_reset_confirm'),
    path('password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('account_activation_sent/', v.account_activation_sent,
         name='account_activation_sent'),
    path('activate/<slug:uidb64>/<slug:token>/', v.activate, name='activate'),
    path('inspect/<project_id>/<scenario_id>', views.inspect, name='inspect'),
    path('compare/<sc_1>/<sc_2>/', views.compare, name='compare'),

    path('login/', v.login, name='login'),
    path('logout/', v.logout, name='logout'),

    path('logs/', views.get_activity_log, name='get_logs'),

    path('portfolio/<query>',
         login_required(views.portfolio), name='portfolio'),
    path('portfolio/<query>/<command>/<id>/<label>',
         login_required(views.portfolio_actions), name='portfolio_actions'),
    path('interface/scenarios', views.get_scenarios_count_ajax,
         name='scenarios_count'),
    path('results/<project_id>', views.show_results,name='show_results'),
    path('project/', views.project_page,
         name='project_select_page'),
    path('select/<project_id>', views.select_starting_point, name='starting_page'),
    path('interface/<project_id>/<starting_scenario>',
         views.interface, name='interface'),

    path('fetch/<search_id>', views.get_saved_search, name='fetch'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('documentation/',views.documentation,name='documentation'),
) + [
    path('changeLang/<lang_code>', views.changLang, name='change_language'),
    path('save/<label>/', views.save_search_params),
    path('vote/<selection>/<scenario>/', views.vote, name='vote')]
