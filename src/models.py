# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Area(models.Model):
    areaid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'area'


class Indicator(models.Model):
    inst_instid = models.ForeignKey('Institution', models.DO_NOTHING, db_column='inst_instid', blank=True, null=True)
    indicid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    name = models.CharField(unique=True, max_length=255, db_comment='E.x. GDP')
    group = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'indicator'


class Institution(models.Model):
    instid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    abbreviation = models.CharField(unique=True, max_length=24, db_comment='E.x. IMF')
    name = models.CharField(unique=True, max_length=255, db_comment='E.x. International Monetary Fund.')
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=24, blank=True, null=True)
    country = models.CharField(max_length=36, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'institution'


class Mapping(models.Model):
    map_id = models.AutoField(primary_key=True, db_comment='Auto incremental')
    indic_indicid = models.ForeignKey(Indicator, models.DO_NOTHING, db_column='indic_indicid', blank=True, null=True)
    uindic_indicid = models.ForeignKey('UnifiedIndicator', models.DO_NOTHING, db_column='uindic_indicid', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mapping'


class Publishes(models.Model):
    pub_id = models.AutoField(primary_key=True, db_comment='Auto incremental')
    inst_instid = models.ForeignKey(Institution, models.DO_NOTHING, db_column='inst_instid', blank=True, null=True)
    indic_indicid = models.ForeignKey(Indicator, models.DO_NOTHING, db_column='indic_indicid', blank=True, null=True)
    area_areaid = models.ForeignKey(Area, models.DO_NOTHING, db_column='area_areaid', blank=True, null=True)
    date_published = models.DateTimeField()
    date_from = models.DateTimeField()
    date_until = models.DateTimeField()
    value = models.IntegerField()
    is_forecast = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'publishes'


class UnifiedIndicator(models.Model):
    uindicid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    name = models.CharField(unique=True, max_length=255, db_comment='E.x. GDP')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'unified_indicator'
