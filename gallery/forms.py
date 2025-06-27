"""
Forms for the Ghibli Gallery app
Handles image upload and artwork creation
"""

from django import forms
from .models import GhibliArtwork

class ArtworkUploadForm(forms.ModelForm):
    class Meta:
        model = GhibliArtwork
        fields = ['name', 'original_image', 'conversion_method']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter artwork name or description (e.g., "Mountain Landscape", "Portrait of Sarah")',
                'required': True
            }),
            'original_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'conversion_method': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Artwork Name',
            'original_image': 'Select Image',
            'conversion_method': 'Conversion Method'
        }
        help_texts = {
            'name': 'Give your artwork a descriptive name',
            'original_image': 'Maximum file size: 10MB. Supported formats: JPEG, PNG, WebP',
            'conversion_method': 'Choose how to convert your image to Ghibli style'
        }
    
    def clean_original_image(self):
        """Validate uploaded image"""
        image = self.cleaned_data.get('original_image')
        
        if image:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if image.size > max_size:
                raise forms.ValidationError(
                    f"Image file too large ({image.size / (1024*1024):.1f}MB). "
                    f"Maximum allowed size is 10MB."
                )
            
            # Check file type
            valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in valid_types:
                raise forms.ValidationError(
                    "Invalid image format. Please use JPEG, PNG, or WebP."
                )
            
            # Check minimum dimensions
            try:
                from PIL import Image
                import tempfile
                
                # Save temporarily to check dimensions
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in image.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    
                    # Open with PIL to check dimensions
                    with Image.open(temp_file.name) as pil_image:
                        width, height = pil_image.size
                        
                        # Minimum size check
                        if width < 256 or height < 256:
                            raise forms.ValidationError(
                                f"Image too small ({width}x{height}). "
                                f"Minimum size is 256x256 pixels."
                            )
                        
                        # Maximum size check
                        if width > 4096 or height > 4096:
                            raise forms.ValidationError(
                                f"Image too large ({width}x{height}). "
                                f"Maximum size is 4096x4096 pixels."
                            )
                
                # Clean up temp file
                import os
                os.unlink(temp_file.name)
                
            except Exception as e:
                # If we can't process the image, let it through
                # The actual processing will catch any issues
                pass
        
        return image
    
    def clean_name(self):
        """Validate artwork name"""
        name = self.cleaned_data.get('name')
        
        if name:
            # Remove extra whitespace
            name = name.strip()
            
            # Length validation
            if len(name) < 2:
                raise forms.ValidationError(
                    "Name must be at least 2 characters long."
                )
            
            if len(name) > 200:
                raise forms.ValidationError(
                    "Name must be less than 200 characters."
                )
            
            # Content validation
            if name.lower() in ['test', 'untitled', 'image', 'photo', 'picture']:
                raise forms.ValidationError(
                    "Please provide a more descriptive name for your artwork."
                )
        
        return name
    
    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        
        # Additional validations can go here
        # For example, checking if name and image match
        
        return cleaned_data

class QuickUploadForm(forms.Form):
    """Simple form for quick uploads without choosing method"""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter artwork name...'
        })
    )
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean_image(self):
        """Quick validation for image"""
        image = self.cleaned_data.get('image')
        
        if image and image.size > 10 * 1024 * 1024:  # 10MB
            raise forms.ValidationError("Image too large. Maximum size is 10MB.")
        
        return image
    


# Add this to the END of your existing gallery/forms.py

from .models import BatchUpload
import zipfile

class BatchUploadForm(forms.ModelForm):
    class Meta:
        model = BatchUpload
        fields = ['name', 'zip_file', 'conversion_method']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch name (e.g., "Vacation Photos", "Family Pictures")',
                'required': True
            }),
            'zip_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.zip',
                'required': True
            }),
            'conversion_method': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Batch Name',
            'zip_file': 'ZIP File',
            'conversion_method': 'Style for All Images'
        }
        help_texts = {
            'name': 'Give your batch a descriptive name',
            'zip_file': 'ZIP file containing JPEG, PNG, or WebP images. Maximum 100MB.',
            'conversion_method': 'All images in the batch will use this style'
        }
    
    def clean_zip_file(self):
        """Validate uploaded ZIP file"""
        zip_file = self.cleaned_data.get('zip_file')
        
        if zip_file:
            # Check file size (max 100MB)
            max_size = 100 * 1024 * 1024  # 100MB
            if zip_file.size > max_size:
                raise forms.ValidationError(
                    f"ZIP file too large ({zip_file.size / (1024*1024):.1f}MB). "
                    f"Maximum allowed size is 100MB."
                )
            
            # Check if it's a valid ZIP file
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    
                    # Check for valid image files
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                    image_files = []
                    
                    for filename in file_list:
                        # Skip directories and hidden files
                        if filename.endswith('/') or filename.startswith('.'):
                            continue
                        
                        # Check file extension
                        file_ext = '.' + filename.lower().split('.')[-1]
                        if file_ext in valid_extensions:
                            image_files.append(filename)
                    
                    if len(image_files) == 0:
                        raise forms.ValidationError(
                            "No valid image files found in ZIP. "
                            "Please include JPEG, PNG, or WebP files."
                        )
                    
                    if len(image_files) > 10:  # Limit batch size for testing
                        raise forms.ValidationError(
                            f"Too many images ({len(image_files)}). "
                            f"Maximum 10 images per batch for now."
                        )
                    
                    print(f"✅ Valid ZIP with {len(image_files)} images")
                    
            except zipfile.BadZipFile:
                raise forms.ValidationError("Invalid ZIP file. Please upload a valid ZIP archive.")
            except Exception as e:
                raise forms.ValidationError(f"Error reading ZIP file: {str(e)}")
        
        return zip_file
    
    def clean_name(self):
        """Validate batch name"""
        name = self.cleaned_data.get('name')
        
        if name:
            name = name.strip()
            
            if len(name) < 3:
                raise forms.ValidationError("Batch name must be at least 3 characters long.")
            
            if len(name) > 200:
                raise forms.ValidationError("Batch name must be less than 200 characters.")
        
        return name
    

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class AdminRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        if commit:
            user.save()
        return user

class ClientRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'client'
        if commit:
            user.save()
        return user
