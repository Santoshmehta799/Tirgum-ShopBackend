from django.contrib import admin
from users.models import ContactUs, User
# Register your models here.



class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'name', 'surname', 'user_type', 'is_approved')
    list_filter = ('user_type', 'is_approved', 'user_type')  # Optional: Filters on the right sidebar
    search_fields = ('email', 'username', 'name', 'surname')  # Optional: Search functionality
    ordering = ['-id']  # Optional: Order by ID descending

admin.site.register(User, UserAdmin)


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'message')
    search_fields = ('email', )
