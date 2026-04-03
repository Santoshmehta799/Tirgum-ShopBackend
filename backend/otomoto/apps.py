from django.apps import AppConfig


class OtomotoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'otomoto'
    
    def ready(self):
        import otomoto.signals



# class TyreadderappConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'tyreadderapp'

#     def ready(self):
#         import tyreadderapp.signals
#         import tyreadderapp.templatetags.custom_filters
#         try:
#             from tyreadderapp.utils import delete_old_unpaired_pairs
#             delete_old_unpaired_pairs()
#         except Exception as e:
#             print(f"[Startup Cleanup] Error deleting old pairs: {e}")