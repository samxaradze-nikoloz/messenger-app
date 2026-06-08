import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


def generate_thumbnail_from_video(video_file, output_format='jpeg'):
    """
    Extract a frame from a video file and convert it to a thumbnail image.
    
    Args:
        video_file: Django File object (from request.FILES)
        output_format: Image format (default: 'jpeg')
    
    Returns:
        ContentFile object or None if extraction fails
    """
    if not HAS_OPENCV:
        return None
    
    try:
        # Save uploaded video to a temporary file
        temp_video_path = f"/tmp/{video_file.name}"
        
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
        
        # Write video file temporarily
        with open(temp_video_path, 'wb') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(temp_video_path)
        
        if not cap.isOpened():
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return None
        
        # Read the first frame
        ret, frame = cap.read()
        cap.release()
        
        # Clean up temp file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        
        if not ret:
            return None
        
        # Convert BGR to RGB (OpenCV uses BGR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize to reasonable thumbnail size (maintain aspect ratio)
        pil_image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        image_io = BytesIO()
        pil_image.save(image_io, format=output_format.upper())
        image_io.seek(0)
        
        # Create a ContentFile to return
        filename = f"thumbnail_{video_file.name.split('.')[0]}.{output_format.lower()}"
        return ContentFile(image_io.getvalue(), name=filename)
    
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None
