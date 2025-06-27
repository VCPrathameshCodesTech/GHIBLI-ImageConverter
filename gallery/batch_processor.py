"""
Batch processing for ZIP file uploads
Extracts and processes multiple images at once
"""

import os
import zipfile
import tempfile
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import BatchUpload, GhibliArtwork
from .huggingface_processor import processor
import time
from PIL import Image

def process_batch_upload(batch_id):
    """
    Process a batch upload - extract ZIP and convert all images
    """
    try:
        batch = BatchUpload.objects.get(id=batch_id)
        
        print(f"🗂️ Starting batch processing: {batch.name}")
        
        # Update status
        batch.status = 'extracting'
        batch.processing_started = timezone.now()
        batch.save()
        
        # Extract ZIP file
        extracted_files = extract_zip_images(batch)
        
        if not extracted_files:
            batch.status = 'failed'
            batch.error_message = 'No valid images found in ZIP file'
            batch.save()
            return f"❌ No valid images found in {batch.name}"
        
        # Update total count
        batch.total_images = len(extracted_files)
        batch.status = 'processing'
        batch.save()
        
        print(f"📊 Processing {len(extracted_files)} images...")
        
        # Process each image
        successful_count = 0
        failed_count = 0
        
        for i, (filename, image_path) in enumerate(extracted_files):
            try:
                print(f"🎨 Processing {i+1}/{len(extracted_files)}: {filename}")
                
                # Create artwork record
                artwork_name = f"{batch.name} - {filename}"
                artwork = GhibliArtwork.objects.create(
                    name=artwork_name,
                    conversion_method=batch.conversion_method,
                    batch_upload=batch,
                    status='processing'
                )
                
                # Copy the extracted image to artwork
                with open(image_path, 'rb') as f:
                    image_content = ContentFile(f.read())
                    clean_filename = filename.replace(' ', '_').replace('(', '').replace(')', '')
                    artwork.original_image.save(f"{artwork.id}_{clean_filename}", image_content, save=True)
                
                # Process the image
                artwork.processing_started = timezone.now()
                artwork.save()
                
                start_time = time.time()
                
                # Convert using our processor
                result_image = processor.convert_to_ghibli(
                    image_path=artwork.original_image.path,
                    prompt=f"Convert {filename} to {batch.conversion_method} style",
                    model_name=batch.conversion_method
                )
                
                if result_image:
                    # Save converted image
                    from io import BytesIO
                    output_buffer = BytesIO()
                    result_image.save(output_buffer, format='JPEG', quality=95)
                    image_content = ContentFile(output_buffer.getvalue())
                    
                    converted_filename = f"{artwork.id}_converted.jpg"
                    artwork.converted_image.save(converted_filename, image_content, save=False)
                    
                    # Update artwork status
                    artwork.status = 'completed'
                    artwork.processing_completed = timezone.now()
                    artwork.processing_time = time.time() - start_time
                    artwork.save()
                    
                    successful_count += 1
                    print(f"✅ Successfully processed {filename} in {artwork.processing_time:.1f}s")
                    
                else:
                    artwork.status = 'failed'
                    artwork.error_message = 'Conversion failed - no result returned'
                    artwork.save()
                    failed_count += 1
                    print(f"❌ Failed to process {filename}")
                
                # Update batch progress
                batch.processed_images = i + 1
                batch.successful_images = successful_count
                batch.failed_images = failed_count
                batch.save()
                
                # Clean up temp file
                try:
                    os.unlink(image_path)
                except:
                    pass
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                failed_count += 1
                
                # Mark artwork as failed if it was created
                try:
                    if 'artwork' in locals():
                        artwork.status = 'failed'
                        artwork.error_message = str(e)
                        artwork.save()
                except:
                    pass
                
                # Update batch progress
                batch.processed_images = i + 1
                batch.failed_images = failed_count
                batch.save()
        
        # Complete batch processing
        batch.status = 'completed'
        batch.processing_completed = timezone.now()
        batch.successful_images = successful_count
        batch.failed_images = failed_count
        batch.save()
        
        result_message = f"🎉 Batch '{batch.name}' complete! {successful_count} successful, {failed_count} failed"
        print(result_message)
        return result_message
        
    except Exception as e:
        error_message = f"❌ Batch processing error: {e}"
        print(error_message)
        try:
            batch = BatchUpload.objects.get(id=batch_id)
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
        except:
            pass
        return error_message

def extract_zip_images(batch):
    """Extract images from ZIP file to temporary directory"""
    extracted_files = []
    
    try:
        print(f"📦 Extracting ZIP file: {batch.zip_file.name}")
        
        with zipfile.ZipFile(batch.zip_file.path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            for filename in file_list:
                # Skip directories and hidden files
                if filename.endswith('/') or filename.startswith('.') or filename.startswith('__MACOSX'):
                    continue
                
                # Check if it's an image file
                file_ext = '.' + filename.lower().split('.')[-1]
                if file_ext in valid_extensions:
                    
                    try:
                        # Extract to temporary file
                        temp_dir = tempfile.mkdtemp()
                        clean_filename = os.path.basename(filename).replace(' ', '_')
                        temp_path = os.path.join(temp_dir, clean_filename)
                        
                        with zip_ref.open(filename) as source, open(temp_path, 'wb') as target:
                            target.write(source.read())
                        
                        # Validate it's a valid image
                        with Image.open(temp_path) as img:
                            # Convert to RGB if needed and resize
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Resize large images to save processing time
                            max_size = 1024
                            if img.width > max_size or img.height > max_size:
                                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                            
                            img.save(temp_path, 'JPEG', quality=95)
                        
                        extracted_files.append((os.path.basename(filename), temp_path))
                        print(f"✅ Extracted: {filename}")
                        
                    except Exception as e:
                        print(f"❌ Invalid image {filename}: {e}")
                        try:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                        except:
                            pass
        
        print(f"📊 Successfully extracted {len(extracted_files)} valid images")
        return extracted_files
        
    except Exception as e:
        print(f"❌ ZIP extraction error: {e}")
        return []