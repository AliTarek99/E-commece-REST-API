import os
from datetime import datetime

class FileManagment():
    @classmethod
    def save_images(cls, request, fieldname):
        images = request.FILES.getlist(fieldname)
        urls = []
        directory = 'media'
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        for image in images:
            filename = f'{request.user.id}{int(datetime.now().timestamp())}{os.path.splitext(image.name)[1]}'
            urls.append(f'media/{filename}')
            with open(os.path.join('media', f'{filename}'), 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
        return urls