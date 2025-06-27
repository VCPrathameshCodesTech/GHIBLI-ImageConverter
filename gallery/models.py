from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
import uuid

# Define choices at module level so both models can use them
CONVERSION_METHODS = [
    ('ghibli', 'Studio Ghibli Style (AI)'),
    ('anime', 'Anime Style (AI)'),
    ('cartoon', 'Cartoon Style (AI)'),
    ('sketch', 'Pencil Sketch'),
    ('vibrant', 'Vibrant Colors'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('client', 'Client'),
]

class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')

    def __str__(self):
        return f"{self.username} ({self.role})"


class BatchUpload(models.Model):
    BATCH_STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('extracting', 'Extracting Images'),
        ('processing', 'Processing Images'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Batch name or description")
    zip_file = models.FileField(upload_to='batch_uploads/', help_text="ZIP file containing images")
    conversion_method = models.CharField(max_length=20, choices=CONVERSION_METHODS, default='ghibli')
    
    # Batch processing status
    status = models.CharField(max_length=20, choices=BATCH_STATUS_CHOICES, default='uploading')
    
    # Statistics
    total_images = models.IntegerField(default=0)
    processed_images = models.IntegerField(default=0)
    successful_images = models.IntegerField(default=0)
    failed_images = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Batch Upload"
        verbose_name_plural = "Batch Uploads"
    
    def __str__(self):
        return f"{self.name} ({self.total_images} images)"
    
    def get_absolute_url(self):
        return reverse('batch_detail', kwargs={'pk': self.pk})
    
    @property
    def progress_percentage(self):
        if self.total_images == 0:
            return 0
        return int((self.processed_images / self.total_images) * 100)
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        return self.status in ['extracting', 'processing']


class GhibliArtwork(models.Model):
    # Use the module-level choices
    CONVERSION_METHODS = CONVERSION_METHODS
    STATUS_CHOICES = STATUS_CHOICES
    
    # Unique ID for each artwork
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    name = models.CharField(max_length=200, help_text="Name or description of the artwork")
    original_image = models.ImageField(upload_to='originals/', help_text="Original image to convert")
    converted_image = models.ImageField(upload_to='converted/', blank=True, null=True)
    
    # Processing details
    conversion_method = models.CharField(max_length=20, choices=CONVERSION_METHODS, default='ghibli')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Batch upload relationship
    batch_upload = models.ForeignKey(
        BatchUpload, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='artworks'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    original_file_size = models.IntegerField(null=True, blank=True)  # in bytes
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ghibli Artwork"
        verbose_name_plural = "Ghibli Artworks"
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_absolute_url(self):
        return reverse('artwork_detail', kwargs={'pk': self.pk})
    
    @property
    def is_processed(self):
        return self.status == 'completed'
    
    @property
    def has_error(self):
        return self.status == 'failed'
    
    @property
    def is_processing(self):
        return self.status == 'processing'
    
    def save(self, *args, **kwargs):
        # Auto-calculate file size
        if self.original_image and not self.original_file_size:
            self.original_file_size = self.original_image.size
        super().save(*args, **kwargs)