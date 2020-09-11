from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='sequence.index'),
    path('list', views.sequence_list, name='sequence.sequence_list'),
    path('my-sequence-list', views.my_sequence_list, name='sequence.my_sequence_list'),
    path('<str:unique_id>/detail', views.sequence_detail, name='sequence.sequence_detail'),
    path('<str:unique_id>/delete', views.sequence_delete, name='sequence.sequence_delete'),

    path('<str:unique_id>/ajax_save_sequence', views.ajax_save_sequence, name='sequence.ajax_save_sequence'),
    path('<str:unique_id>/ajax_sequence_check_publish', views.ajax_sequence_check_publish, name='sequence.ajax_sequence_check_publish'),
    path('<str:unique_id>/ajax_sequence_check_like', views.ajax_sequence_check_like, name='sequence.ajax_sequence_check_like'),
    path('<str:unique_id>/ajax_image_mark_view/<str:image_key>/', views.ajax_image_mark_view, name='sequence.ajax_image_mark_view'),
    path('<str:unique_id>/ajax_get_image_detail/<str:image_key>/', views.ajax_get_image_detail, name='sequence.ajax_get_image_detail'),
    path('<str:unique_id>/ajax_get_image_detail/<str:image_key>/', views.ajax_add_ele_in_image, name='sequence.ajax_add_ele_in_image'),
    path('<str:unique_id>/ajax_get_image_list/', views.ajax_get_image_list, name='sequence.ajax_get_image_list'),
    path('<str:seq_key>/ajax_import/', views.ajax_import, name='sequence.ajax_import'),
    path('<str:unique_id>/ajax_add_ele/', views.ajax_add_ele, name='sequence.ajax_add_ele'),

    path('import-sequence-list', views.import_sequence_list, name='sequence.import_sequence_list'),
    path('import-sequence', views.import_sequence, name='sequence.import_sequence'),


]
