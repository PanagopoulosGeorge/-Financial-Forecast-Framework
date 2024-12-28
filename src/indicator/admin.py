from django.contrib import admin
from .models import Indicator, Mapping, Publishes, UnifiedIndicator
# Register your models here.


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ['inst_instid', 'abbreviation',
                    'name', 'unit', 'created_at', 'updated_at']
    search_fields = ['abbreviation__icontains',
                    'name__icontains', 'unit__icontains']


@admin.register(Mapping)
class MappingAdmin(admin.ModelAdmin):
    pass

@admin.register(Publishes)
class PublishesAdmin(admin.ModelAdmin):
    list_display = ['get_institution_name', 'get_indicator_symbol', 'get_indicator_name', 'get_publication_value', 
                    'get_date_from', 'get_date_until', 'get_date_published']
    search_fields = ['inst_instid__abbreviation__icontains', 'indic_indicid__abbreviation__icontains']
    def get_institution_name(self, obj):
        return obj.inst_instid.abbreviation  # Assuming inst_instid is a ForeignKey to Institution model

    def  get_indicator_symbol(self, obj):
        return obj.indic_indicid.abbreviation  # Assuming indic_indicid is a ForeignKey to Indicator model

    def get_indicator_name(self, obj):
        return obj.indic_indicid.name
    
    def get_publication_value(self, obj):
        return obj.value
    
    def get_date_from(self, obj):
        return obj.date_from.date()
    
    def get_date_until(self, obj):
        return obj.date_until.date()
    
    def get_date_published(self, obj):
        return obj.date_published.date()
    
    get_institution_name.short_description = 'Institution'
    get_indicator_symbol.short_description = 'Indicator'
    get_indicator_name.short_description = 'Indicator Name'
    get_publication_value.short_description = 'Value'
    get_date_from.short_description = 'Date From'
    get_date_until.short_description = 'Date Until'
    get_date_published.short_description = 'Date Published'

@admin.register(UnifiedIndicator)
class UnifiedIndicatorAdmin(admin.ModelAdmin):
    pass
