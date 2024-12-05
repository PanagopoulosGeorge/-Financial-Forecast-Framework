from django.db import models
from geography.models import Area
from institution.models import Institution
# Create your models here.


class Indicator(models.Model):
    inst_instid = models.ForeignKey(
        Institution, models.DO_NOTHING, db_column='inst_instid', blank=True, null=True)
    indicid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    name = models.CharField(
        unique=False, max_length=255)
    group = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    abbreviation = models.CharField(
        unique=False, max_length=255, db_comment='E.x. GDP')

    class Meta:
        managed = False
        db_table = 'indicator'


class Mapping(models.Model):
    map_id = models.AutoField(primary_key=True, db_comment='Auto incremental')
    indic_indicid = models.ForeignKey(
        Indicator, models.DO_NOTHING, db_column='indic_indicid', blank=True, null=True)
    uindic_indicid = models.ForeignKey(
        'UnifiedIndicator', models.DO_NOTHING, db_column='uindic_indicid', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    formula = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mapping'


class Publishes(models.Model):
    pub_id = models.AutoField(primary_key=True, db_comment='Auto incremental')
    inst_instid = models.ForeignKey(
        Institution, models.DO_NOTHING, db_column='inst_instid', blank=True, null=True)
    indic_indicid = models.ForeignKey(
        Indicator, models.DO_NOTHING, db_column='indic_indicid', blank=True, null=True)
    area_areaid = models.ForeignKey(
        Area, models.DO_NOTHING, db_column='area_areaid', blank=True, null=True)
    date_published = models.DateTimeField()
    date_from = models.DateTimeField()
    date_until = models.DateTimeField()
    value = models.IntegerField()
    is_forecast = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'publishes'


class UnifiedIndicator(models.Model):
    uindicid = models.AutoField(
        primary_key=True, db_comment='Auto incremental')
    name = models.CharField(unique=True, max_length=255, db_comment='E.x. GDP')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'unified_indicator'
