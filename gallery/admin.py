from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, BatchUpload, GhibliArtwork

# 1. Enhanced CustomUser admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'role')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    ordering = ('-date_joined',)


# 2. Inline for artworks under batch upload
class GhibliArtworkInline(admin.TabularInline):
    model = GhibliArtwork
    extra = 0
    fields = ('name', 'status', 'conversion_method', 'created_at', 'is_processed', 'has_error')
    readonly_fields = ('created_at', 'is_processed', 'has_error')


# 3. Enhanced BatchUpload admin
@admin.register(BatchUpload)
class BatchUploadAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'conversion_method', 'total_images', 'processed_images', 
        'successful_images', 'failed_images', 'created_at', 'processing_started', 'processing_completed'
    )
    list_filter = ('status', 'conversion_method', 'created_at')
    search_fields = ('name', 'zip_file')
    readonly_fields = (
        'created_at', 'processing_started', 'processing_completed',
        'total_images', 'processed_images', 'successful_images', 'failed_images', 'progress_percentage'
    )
    inlines = [GhibliArtworkInline]
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_failed']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} batch uploads marked as completed.")
    mark_completed.short_description = "Mark selected batch uploads as completed"

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} batch uploads marked as failed.")
    mark_failed.short_description = "Mark selected batch uploads as failed"


# 4. Enhanced GhibliArtwork admin
@admin.register(GhibliArtwork)
class GhibliArtworkAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'batch_upload', 'conversion_method', 'status', 'created_at', 'is_processed', 'has_error', 'retry_count'
    )
    list_filter = ('status', 'conversion_method', 'created_at', 'batch_upload')
    search_fields = ('name', 'error_message')
    readonly_fields = (
        'created_at', 'processing_started', 'processing_completed', 'original_file_size', 'processing_time'
    )
    raw_id_fields = ('batch_upload',)
    actions = ['mark_completed', 'mark_failed', 'reset_processing']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} artworks marked as completed.")
    mark_completed.short_description = "Mark selected artworks as completed"

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} artworks marked as failed.")
    mark_failed.short_description = "Mark selected artworks as failed"

    def reset_processing(self, request, queryset):
        updated = queryset.update(status='pending', retry_count=0)
        self.message_user(request, f"{updated} artworks reset to pending status.")
    reset_processing.short_description = "Reset selected artworks to pending"

