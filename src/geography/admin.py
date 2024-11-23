from django.contrib import admin
from geography.models import Area

# Register your models here.
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'currency', 'population', 'updated_at']
    