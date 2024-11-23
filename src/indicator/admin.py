from django.contrib import admin
from .models import Indicator, Mapping, Publishes, UnifiedIndicator
# Register your models here.
@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    pass

@admin.register(Mapping)
class MappingAdmin(admin.ModelAdmin):
    pass

@admin.register(Publishes)
class PublishesAdmin(admin.ModelAdmin):
    pass

@admin.register(UnifiedIndicator)
class UnifiedIndicatorAdmin(admin.ModelAdmin):
    pass