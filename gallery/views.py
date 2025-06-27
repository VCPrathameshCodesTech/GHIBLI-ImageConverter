"""
Views for the Ghibli Gallery app
Handles web pages and user interactions
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminRegisterForm, ClientRegisterForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import GhibliArtwork
from .forms import ArtworkUploadForm, QuickUploadForm
from .models import BatchUpload
from .forms import BatchUploadForm
from .batch_processor import process_batch_upload

def home_view(request):
    """Home page with upload form and recent artworks"""
    # Get recent completed artworks for display
    recent_artworks = GhibliArtwork.objects.filter(status='completed')[:6]
    
    # Calculate statistics
    stats = {
        'total_artworks': GhibliArtwork.objects.count(),
        'completed_artworks': GhibliArtwork.objects.filter(status='completed').count(),
        'processing_artworks': GhibliArtwork.objects.filter(status='processing').count(),
        'pending_artworks': GhibliArtwork.objects.filter(status='pending').count(),
    }
    
    # Quick upload form for home page
    quick_form = QuickUploadForm()
    
    context = {
        'recent_artworks': recent_artworks,
        'stats': stats,
        'quick_form': quick_form,
    }
    return render(request, 'home.html', context)

def upload_view(request):
    """Handle artwork upload with full form"""
    if request.method == 'POST':
        form = ArtworkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save()
            
            # Process immediately instead of background
            try:
                from .huggingface_processor import processor
                from django.utils import timezone
                from django.core.files.base import ContentFile
                from io import BytesIO
                import time
                
                # Update status to processing
                artwork.status = 'processing'
                artwork.processing_started = timezone.now()
                artwork.save()
                
                start_time = time.time()
                
                # Create conversion prompt
                prompt = f"Convert this image of {artwork.name} into Studio Ghibli anime art style"
                
                # Use the Hugging Face processor
                result_image = processor.convert_to_ghibli(
                    image_path=artwork.original_image.path,
                    prompt=prompt,
                    model_name=artwork.conversion_method
                )
                
                if result_image:
                    # Convert PIL Image to bytes
                    output_buffer = BytesIO()
                    result_image.save(output_buffer, format='JPEG', quality=95)
                    image_content = ContentFile(output_buffer.getvalue())
                    
                    # Save the converted image
                    filename = f"{artwork.id}_ghibli.jpg"
                    artwork.converted_image.save(filename, image_content, save=False)
                    
                    # Update artwork status
                    artwork.status = 'completed'
                    artwork.processing_completed = timezone.now()
                    artwork.processing_time = time.time() - start_time
                    artwork.save()
                    
                    messages.success(
                        request, 
                        f'🎉 Successfully converted "{artwork.name}" to Ghibli style in {artwork.processing_time:.1f} seconds!'
                    )
                else:
                    # Conversion failed
                    artwork.status = 'failed'
                    artwork.error_message = 'Hugging Face API returned no image'
                    artwork.save()
                    
                    messages.warning(
                        request,
                        f'Upload successful but conversion failed. The image might be processing on Hugging Face servers. Try again in a few minutes.'
                    )
                    
            except Exception as e:
                # Handle conversion errors
                artwork.status = 'failed'
                artwork.error_message = str(e)
                artwork.save()
                
                messages.warning(
                    request,
                    f'Upload successful but conversion failed: {str(e)}'
                )
            
            return redirect('artwork_detail', pk=artwork.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ArtworkUploadForm()
    
    context = {
        'form': form,
        'page_title': 'Upload Your Artwork'
    }
    return render(request, 'upload.html', context)

def quick_upload_view(request):
    """Handle quick upload from home page"""
    if request.method == 'POST':
        form = QuickUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create artwork with default settings
            artwork = GhibliArtwork.objects.create(
                name=form.cleaned_data['name'],
                original_image=form.cleaned_data['image'],
                conversion_method='huggingface'  # Default to Hugging Face
            )
            
            # Process immediately
            try:
                from .huggingface_processor import processor
                from django.utils import timezone
                from django.core.files.base import ContentFile
                from io import BytesIO
                import time
                
                # Update status to processing
                artwork.status = 'processing'
                artwork.processing_started = timezone.now()
                artwork.save()
                
                start_time = time.time()
                
                # Create conversion prompt
                prompt = f"Convert this image of {artwork.name} into Studio Ghibli anime art style"
                
                # Use the Hugging Face processor
                result_image = processor.convert_to_ghibli(
                    image_path=artwork.original_image.path,
                    prompt=prompt,
                    model_name=artwork.conversion_method
                )
                
                if result_image:
                    # Convert PIL Image to bytes
                    output_buffer = BytesIO()
                    result_image.save(output_buffer, format='JPEG', quality=95)
                    image_content = ContentFile(output_buffer.getvalue())
                    
                    # Save the converted image
                    filename = f"{artwork.id}_ghibli.jpg"
                    artwork.converted_image.save(filename, image_content, save=False)
                    
                    # Update artwork status
                    artwork.status = 'completed'
                    artwork.processing_completed = timezone.now()
                    artwork.processing_time = time.time() - start_time
                    artwork.save()
                    
                    messages.success(
                        request,
                        f'🎉 Quick upload success! "{artwork.name}" converted to Ghibli style in {artwork.processing_time:.1f} seconds!'
                    )
                else:
                    artwork.status = 'failed'
                    artwork.error_message = 'Conversion failed - no image returned'
                    artwork.save()
                    
                    messages.warning(
                        request,
                        f'Upload successful but conversion failed. Try again in a few minutes.'
                    )
                    
            except Exception as e:
                artwork.status = 'failed'
                artwork.error_message = str(e)
                artwork.save()
                
                messages.warning(
                    request,
                    f'Upload successful but conversion failed: {str(e)}'
                )
            
            return redirect('artwork_detail', pk=artwork.pk)
        else:
            messages.error(request, 'Upload failed. Please check your image and try again.')
    
    return redirect('home')


@login_required
def gallery_view(request):
    """Gallery page with all completed artworks"""
    # Filter options
    method_filter = request.GET.get('method')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Base queryset - only completed artworks
    artworks = GhibliArtwork.objects.filter(status='completed')
    
    # Apply filters
    if method_filter:
        artworks = artworks.filter(conversion_method=method_filter)
    
    if search_query:
        artworks = artworks.filter(
            Q(name__icontains=search_query)
        )
    
    # Apply sorting
    valid_sorts = ['-created_at', 'created_at', 'name', '-name', '-processing_time', 'processing_time']
    if sort_by in valid_sorts:
        artworks = artworks.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(artworks, 12)  # Show 12 artworks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options for template
    conversion_methods = GhibliArtwork.CONVERSION_METHODS
    
    context = {
        'page_obj': page_obj,
        'conversion_methods': conversion_methods,
        'current_method': method_filter,
        'search_query': search_query,
        'current_sort': sort_by,
        'total_count': artworks.count(),
    }
    return render(request, 'gallery.html', context)

@login_required
def artwork_detail_view(request, pk):
    """Detail view for a single artwork"""
    artwork = get_object_or_404(GhibliArtwork, pk=pk)
    
    # Get similar artworks (same conversion method, different artworks)
    similar_artworks = GhibliArtwork.objects.filter(
        conversion_method=artwork.conversion_method,
        status='completed'
    ).exclude(pk=artwork.pk)[:4]
    
    context = {
        'artwork': artwork,
        'similar_artworks': similar_artworks,
    }
    return render(request, 'detail.html', context)

def processing_view(request):
    """View for artworks currently being processed"""
    processing_artworks = GhibliArtwork.objects.filter(
        status__in=['pending', 'processing']
    ).order_by('-created_at')
    
    paginator = Paginator(processing_artworks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_count': processing_artworks.count(),
        'page_title': 'Processing Queue'
    }
    return render(request, 'processing.html', context)

def failed_view(request):
    """View for failed artworks"""
    failed_artworks = GhibliArtwork.objects.filter(status='failed').order_by('-created_at')
    
    paginator = Paginator(failed_artworks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_count': failed_artworks.count(),
        'page_title': 'Failed Conversions'
    }
    return render(request, 'failed.html', context)

def retry_artwork_view(request, pk):
    """Retry processing a failed artwork"""
    if request.method == 'POST':
        artwork = get_object_or_404(GhibliArtwork, pk=pk)
        
        if artwork.status == 'failed':
            # Process immediately on retry
            try:
                from .huggingface_processor import processor
                from django.utils import timezone
                from django.core.files.base import ContentFile
                from io import BytesIO
                import time
                
                # Update status to processing
                artwork.status = 'processing'
                artwork.processing_started = timezone.now()
                artwork.error_message = ''
                artwork.save()
                
                start_time = time.time()
                
                # Create conversion prompt
                prompt = f"Convert this image of {artwork.name} into Studio Ghibli anime art style"
                
                # Use the Hugging Face processor
                result_image = processor.convert_to_ghibli(
                    image_path=artwork.original_image.path,
                    prompt=prompt,
                    model_name='ghibli_diffusion'
                )
                
                if result_image:
                    # Convert PIL Image to bytes
                    output_buffer = BytesIO()
                    result_image.save(output_buffer, format='JPEG', quality=95)
                    image_content = ContentFile(output_buffer.getvalue())
                    
                    # Save the converted image
                    filename = f"{artwork.id}_ghibli.jpg"
                    artwork.converted_image.save(filename, image_content, save=False)
                    
                    # Update artwork status
                    artwork.status = 'completed'
                    artwork.processing_completed = timezone.now()
                    artwork.processing_time = time.time() - start_time
                    artwork.save()
                    
                    messages.success(request, f'🎉 Successfully retried and converted "{artwork.name}" to Ghibli style!')
                else:
                    artwork.status = 'failed'
                    artwork.error_message = 'Retry failed - no image returned'
                    artwork.save()
                    messages.warning(request, f'Retry failed for "{artwork.name}". Please try again later.')
                    
            except Exception as e:
                artwork.status = 'failed'
                artwork.error_message = str(e)
                artwork.save()
                messages.error(request, f'Retry failed: {str(e)}')
        else:
            messages.error(request, 'Can only retry failed artworks')
    
    return redirect('artwork_detail', pk=pk)

# API Views for AJAX requests
def artwork_status_api(request, pk):
    """API endpoint to check artwork status"""
    artwork = get_object_or_404(GhibliArtwork, pk=pk)
    
    data = {
        'status': artwork.status,
        'status_display': artwork.get_status_display(),
        'is_completed': artwork.is_processed,
        'has_error': artwork.has_error,
        'error_message': artwork.error_message,
        'processing_time': artwork.processing_time,
        'created_at': artwork.created_at.isoformat(),
    }
    
    if artwork.is_processed and artwork.converted_image:
        data['converted_image_url'] = artwork.converted_image.url
    
    return JsonResponse(data)

def gallery_stats_api(request):
    """API endpoint for gallery statistics"""
    stats = {
        'total': GhibliArtwork.objects.count(),
        'completed': GhibliArtwork.objects.filter(status='completed').count(),
        'processing': GhibliArtwork.objects.filter(status='processing').count(),
        'pending': GhibliArtwork.objects.filter(status='pending').count(),
        'failed': GhibliArtwork.objects.filter(status='failed').count(),
    }
    
    # Method breakdown
    method_stats = {}
    for method_code, method_name in GhibliArtwork.CONVERSION_METHODS:
        method_stats[method_code] = {
            'name': method_name,
            'count': GhibliArtwork.objects.filter(
                conversion_method=method_code,
                status='completed'
            ).count()
        }
    
    return JsonResponse({
        'stats': stats,
        'methods': method_stats
    })

def upload_progress_api(request):
    """API endpoint to get recent upload progress"""
    recent_uploads = GhibliArtwork.objects.filter(
        status__in=['pending', 'processing']
    ).order_by('-created_at')[:10]
    
    data = []
    for artwork in recent_uploads:
        data.append({
            'id': str(artwork.id),
            'name': artwork.name,
            'status': artwork.status,
            'status_display': artwork.get_status_display(),
            'created_at': artwork.created_at.isoformat(),
            'method': artwork.get_conversion_method_display(),
        })
    
    return JsonResponse({'artworks': data})


# Add these views to the END of your existing gallery/views.py

def batch_upload_view(request):
    """Handle batch ZIP upload"""
    if request.method == 'POST':
        form = BatchUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save()
            
            # Start batch processing immediately
            try:
                result_message = process_batch_upload(str(batch.id))
                messages.success(request, result_message)
            except Exception as e:
                messages.error(request, f'Batch processing failed: {str(e)}')
            
            return redirect('batch_detail', pk=batch.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BatchUploadForm()
    
    context = {
        'form': form,
        'page_title': 'Batch Upload'
    }
    return render(request, 'batch_upload.html', context)

def batch_detail_view(request, pk):
    """Detail view for a batch upload"""
    batch = get_object_or_404(BatchUpload, pk=pk)
    
    # Get all artworks in this batch
    artworks = batch.artworks.all().order_by('-created_at')
    
    # Pagination for large batches
    paginator = Paginator(artworks, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'batch': batch,
        'page_obj': page_obj,
        'artworks': artworks,
        'total_count': artworks.count(),
    }
    return render(request, 'batch_detail.html', context)

def batch_list_view(request):
    """List all batch uploads"""
    batches = BatchUpload.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(batches, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_count': batches.count(),
        'page_title': 'Batch Uploads'
    }
    return render(request, 'batch_list.html', context)

def batch_retry_view(request, pk):
    """Retry processing a failed batch"""
    if request.method == 'POST':
        batch = get_object_or_404(BatchUpload, pk=pk)
        
        if batch.status == 'failed':
            try:
                # Reset batch status
                batch.status = 'uploading'
                batch.error_message = ''
                batch.processed_images = 0
                batch.successful_images = 0
                batch.failed_images = 0
                batch.save()
                
                # Restart processing
                result_message = process_batch_upload(str(batch.id))
                messages.success(request, f'Batch retry completed: {result_message}')
            except Exception as e:
                messages.error(request, f'Batch retry failed: {str(e)}')
        else:
            messages.error(request, 'Can only retry failed batches')
    
    return redirect('batch_detail', pk=pk)

# API view for batch progress
def batch_progress_api(request, pk):
    """API endpoint to check batch processing progress"""
    batch = get_object_or_404(BatchUpload, pk=pk)
    
    data = {
        'status': batch.status,
        'status_display': batch.get_status_display(),
        'progress_percentage': batch.progress_percentage,
        'total_images': batch.total_images,
        'processed_images': batch.processed_images,
        'successful_images': batch.successful_images,
        'failed_images': batch.failed_images,
        'is_completed': batch.is_completed,
        'is_processing': batch.is_processing,
        'error_message': batch.error_message,
    }
    
    return JsonResponse(data)



def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

# ... your is_admin function, AdminRegisterForm, ClientRegisterForm, etc.

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_register_view(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin registered successfully!')
            return redirect('home')  
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = AdminRegisterForm()
    return render(request, 'admin_register.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def client_register_view(request):
    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client user registered successfully!')
            return redirect('home')  # Stays on the form for next user
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ClientRegisterForm()
    return render(request, 'client_register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print(user)
        if user:
            login(request, user)
            next_url = request.GET.get('next') or reverse('home')  
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login') 


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import GhibliArtwork
import os

@login_required
def delete_artwork(request, artwork_id):
    if request.user.role != 'admin':
        return HttpResponseForbidden("You don't have permission to delete artworks.")
    artwork = get_object_or_404(GhibliArtwork, id=artwork_id)
    if request.method == 'POST':
        artwork_name = artwork.name
        # Remove files (optional)
        for img in [artwork.original_image, artwork.converted_image]:
            if img and img.name:
                try:
                    if os.path.isfile(img.path):
                        os.remove(img.path)
                except Exception as e:
                    print(f"Error deleting image: {e}")
        artwork.delete()
        messages.success(request, f'Artwork "{artwork_name}" has been deleted successfully.')
        return redirect('gallery')
    return redirect('gallery')
