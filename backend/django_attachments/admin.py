# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, TemplateView
from django.urls import path

from .fields import LibraryField, GalleryField
from .forms import ImageUploadForm
from .models import Attachment, Library
from .views import AttachmentEditableMixin
from .widgets import AdminLibraryWidget, AdminGalleryWidget


class AttachmentsPermsMixin(UserPassesTestMixin):
	def test_func(self):
		user = self.request.user
		if not user.is_authenticated:
			return False
		if not user.is_staff:
			return False
		if not user.has_perm('django_attachments.change_attachment'):
			return False
		return True


class LibraryEditView(AttachmentsPermsMixin, AttachmentEditableMixin, TemplateView):
	template_name = 'admin/attachments/library_edit.html'

	def get_library(self):
		return get_object_or_404(Library, pk=self.kwargs['pk'])


class GalleryEditView(LibraryEditView):
	upload_form_class = ImageUploadForm


class AttachmentsAdminMixin(object):
	def formfield_for_dbfield(self, db_field, request, **kwargs):
		if isinstance(db_field, GalleryField):
			return db_field.formfield(widget=AdminGalleryWidget, **kwargs)
		if isinstance(db_field, LibraryField):
			return db_field.formfield(widget=AdminLibraryWidget, **kwargs)
		return super().formfield_for_dbfield(db_field, request, **kwargs)


class LibraryCreateViw(AttachmentsPermsMixin, CreateView):
	template_name = 'admin/attachments/library_create.html'
	model = Library
	fields = ('title',)

	def form_valid(self, form):
		self.object = form.save()
		return JsonResponse({'id': self.object.pk})


class AttachmentsInline(admin.TabularInline):
	model = Attachment
	fields = ('rank',)


class LibraryAdmin(admin.ModelAdmin):
	inlines = [AttachmentsInline]
	raw_id_fields = ('primary_attachment',)

	def get_urls(self):
		urlpatterns = super().get_urls()
		urlpatterns = [
			path('api/create/', LibraryCreateViw.as_view(), name='attachments_library_create_api'),
			path('api/attachments/<int:pk>/', LibraryEditView.as_view(), name='attachments_library_edit_api'),
			path('api/gallery/<int:pk>/', GalleryEditView.as_view(), name='attachments_gallery_edit_api'),
		] + urlpatterns
		return urlpatterns


admin.site.register(Attachment)
admin.site.register(Library, LibraryAdmin)
