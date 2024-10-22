import os
import base64
import uuid
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.permissions import AllowAny

class FileManagment():
    @classmethod
    def save_images(cls, request, files):
        urls = []
        directory = 'media'
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        for image_data in files:
            if "," in image_data['image']:
                header, image_base64 = image_data['image'].split(',')
            else:
                image_base64 = image_data['image']
            image = base64.b64decode(image_base64)
            file_extension = header.split('/')[1].split(';')[0] if "," in image_data['image'] else 'png'
            filename = f'{request.user.id}_{uuid.uuid4()}.{file_extension}'
            urls.append({'url': f'media/{filename}', 'color': image_data['color']})
            with open(os.path.join('media', f'{filename}'), 'wb+') as destination:
                destination.write(image)
        return urls
    
    @classmethod
    def file_to_base64(cls, file_path):
        try:
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
        except Exception as e:
            return None

        return encoded_string.decode('utf-8')

class HealthCheck(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return JsonResponse({"status": "ok"}, status=200)