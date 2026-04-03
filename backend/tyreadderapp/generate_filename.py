import os
import pathlib
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import SuspiciousFileOperation

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        """Return the same name to allow overwrites and force DB updates"""
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name

    def _save(self, name, content):
        """
        Save the file without any filename modifications
        """
        full_path = self.path(name)
        # print('full_path --->',full_path)

        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write the new file
        with open(full_path, 'wb') as f:
            for chunk in content.chunks():
                f.write(chunk)

        print('=-=-path=-=->>',name)
        if hasattr(content, 'seek'):
            content.seek(0)
            
        return name
    
    def delete(self, name):
        """Override delete to ensure complete removal"""
        super().delete(name)
        # Force storage to re-evaluate file existence
        if hasattr(self, '_entries'):
            del self._entries