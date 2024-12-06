from django.db import models

# Create your models here.


class Area(models.Model):
    areaid = models.AutoField(primary_key=True, db_comment='Auto incremental')
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'area'
    def __str__(self) -> str:
        return self.code
    def save(self, *args, **kwargs):
        if self.population == '':
            self.population = None
        super().save(*args, **kwargs)
