from django.db import models

# Create your models here.
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