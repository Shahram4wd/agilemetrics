from django.db import models

class IssueType(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    hierarchy_level = models.IntegerField(blank=True, null=True)
    avatar_id = models.IntegerField(blank=True, null=True)
    subtask = models.BooleanField(default=False)
    project_scope = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Issue Type"
        verbose_name_plural = "Issue Types"

    def __str__(self):
        return self.name

