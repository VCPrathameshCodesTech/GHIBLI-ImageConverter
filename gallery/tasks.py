"""
Celery tasks for background image processing
Handles Ghibli art conversion using Hugging Face API
"""

from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import GhibliArtwork
from .huggingface_processor import processor
import time
from io import BytesIO

@shared_task
def convert_to_ghibli(artwork_id):
    """
    Main task to convert artwork to Ghibli style using Hugging Face API
    
    Args:
        artwork_id: UUID of the GhibliArtwork to process
        
    Returns:
        str: Success message or error details
    """
    try:
        # Get the artwork from database
        artwork = GhibliArtwork.objects.get(id=artwork_id)
        
        # Update status to processing
        artwork.status = 'processing'
        artwork.processing_started = timezone.now()
        artwork.save()
        
        print(f"🎨 Starting conversion for: {artwork.name}")
        start_time = time.time()
        
        # Choose conversion method
        if artwork.conversion_method == 'huggingface':
            result_image = convert_with_huggingface(artwork)
        elif artwork.conversion_method == 'openai':
            result_image = convert_with_openai(artwork)
        elif artwork.conversion_method == 'stability':
            result_image = convert_with_stability(artwork)
        elif artwork.conversion_method == 'replicate':
            result_image = convert_with_replicate(artwork)
        else:
            raise ValueError(f"Unknown conversion method: {artwork.conversion_method}")
        
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
            
            print(f"✅ Successfully converted: {artwork.name} in {artwork.processing_time:.1f}s")
            return f"Successfully converted artwork: {artwork.name}"
            
        else:
            raise Exception("Conversion returned no result")
            
    except Exception as e:
        # Handle errors
        try:
            artwork = GhibliArtwork.objects.get(id=artwork_id)
            artwork.status = 'failed'
            artwork.error_message = str(e)
            artwork.retry_count += 1
            artwork.save()
            
            print(f"❌ Conversion failed for {artwork.name}: {e}")
            
            # Auto-retry if less than 3 attempts
            if artwork.retry_count < 3:
                print(f"🔄 Scheduling retry {artwork.retry_count}/3 for {artwork.name}")
                convert_to_ghibli.apply_async(args=[artwork_id], countdown=60)  # Retry after 1 minute
            
        except Exception as save_error:
            print(f"❌ Error saving failure state: {save_error}")
        
        raise e

def convert_with_huggingface(artwork):
    """Convert using Hugging Face API"""
    try:
        print(f"🤗 Using Hugging Face API for: {artwork.name}")
        
        # Create conversion prompt
        prompt = f"Convert this image of {artwork.name} into Studio Ghibli anime art style"
        
        # Use the processor
        result_image = processor.convert_to_ghibli(
            image_path=artwork.original_image.path,
            prompt=prompt,
            model_name='ghibli_diffusion'
        )
        
        if result_image:
            print(f"✅ Hugging Face conversion successful")
            return result_image
        else:
            raise Exception("Hugging Face API returned no image")
            
    except Exception as e:
        raise Exception(f"Hugging Face API error: {str(e)}")

def convert_with_openai(artwork):
    """Convert using OpenAI API (placeholder for future implementation)"""
    raise Exception("OpenAI integration not implemented yet")

def convert_with_stability(artwork):
    """Convert using Stability AI API (placeholder for future implementation)"""
    raise Exception("Stability AI integration not implemented yet")

def convert_with_replicate(artwork):
    """Convert using Replicate API (placeholder for future implementation)"""
    raise Exception("Replicate integration not implemented yet")

@shared_task
def cleanup_failed_artworks():
    """
    Periodic task to clean up artworks that have been processing for too long
    This prevents stuck processing states
    """
    from datetime import timedelta
    
    print("🧹 Running cleanup task...")
    
    # Find artworks stuck in processing state for more than 1 hour
    cutoff_time = timezone.now() - timedelta(hours=1)
    stuck_artworks = GhibliArtwork.objects.filter(
        status='processing',
        processing_started__lt=cutoff_time
    )
    
    count = 0
    for artwork in stuck_artworks:
        artwork.status = 'failed'
        artwork.error_message = "Processing timeout - artwork was stuck in processing state"
        artwork.save()
        count += 1
        print(f"🔧 Cleaned up stuck artwork: {artwork.name}")
    
    if count > 0:
        print(f"✅ Cleaned up {count} stuck artworks")
    else:
        print("✅ No stuck artworks found")
    
    return f"Cleaned up {count} stuck artworks"

@shared_task
def test_huggingface_connection():
    """Test task to verify Hugging Face API connection"""
    try:
        success = processor.test_connection()
        if success:
            return "✅ Hugging Face API connection successful"
        else:
            return "❌ Hugging Face API connection failed"
    except Exception as e:
        return f"❌ Connection test error: {str(e)}"