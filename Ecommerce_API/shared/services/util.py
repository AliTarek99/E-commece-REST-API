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
            if "," in image_data:
                header, image_base64 = image_data.split(',')
            else:
                image_base64 = image_data

            image = base64.b64decode(image_base64)
            file_extension = header.split('/')[1].split(';')[0] if "," in image_data else 'png'
            filename = f'{request.user.id}_{uuid.uuid4()}.{file_extension}'
            urls.append(f'media/{filename}')
            with open(os.path.join('media', f'{filename}'), 'wb+') as destination:
                destination.write(image)
        return urls
    
class HealthCheck(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return JsonResponse({"status": "ok"}, status=200)