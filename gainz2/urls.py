"""
URL configuration for gainz project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path

from accounts.views import demo_page, design_page, home_page, login_page, logout_page, register_page
from routines.views import (
    import_routine_page,
    new_routine_page,
    routine_detail_page,
    routines_list_page,
)
from exercises.views import exercise_list_page
from programs.views import (
    import_program_page,
    new_program_page,
    new_progression_template_page,
    program_detail_page,
    program_routine_page,
    progression_template_detail_page,
    progression_templates_list_page,
    programs_list_page,
)
from progress.views import progress_page, progress_records_page
from workouts.views import (
    new_workout_page,
    service_worker,
    workout_detail_page,
    workouts_list_page,
)

urlpatterns = [
    path("service-worker.js", service_worker, name="service-worker"),
    path("", home_page, name="home"),
    path("design/", design_page, name="design"),
    path("login/", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("demo/", demo_page, name="demo"),
    path("logout/", logout_page, name="logout"),
    path("admin/", admin.site.urls),
    path("progress/", progress_page, name="progress"),
    path("progress/records/", progress_records_page, name="progress-records"),
    path("exercises/", exercise_list_page, name="exercises-list"),
    path("workouts/", workouts_list_page, name="workouts-list"),
    path("workouts/new/", new_workout_page, name="new-workout"),
    path("workouts/<int:workout_id>/", workout_detail_page, name="workout-detail"),
    path("programs/", programs_list_page, name="programs-list"),
    path("programs/import/", import_program_page, name="program-import"),
    path("programs/new/", new_program_page, name="new-program"),
    path("programs/<int:program_id>/", program_detail_page, name="program-detail"),
    path(
        "programs/<int:program_id>/routines/<int:routine_id>/",
        program_routine_page,
        name="program-routine-detail",
    ),
    path("programs/progression/", progression_templates_list_page, name="progression-templates-list"),
    path("programs/progression/new/", new_progression_template_page, name="new-progression-template"),
    path("programs/progression/<int:template_id>/", progression_template_detail_page, name="progression-template-detail"),
    path("routines/", routines_list_page, name="routines-list"),
    path("routines/import/", import_routine_page, name="routine-import"),
    path("routines/new/", new_routine_page, name="new-routine"),
    path("routines/<int:routine_id>/", routine_detail_page, name="routine-detail"),
]
