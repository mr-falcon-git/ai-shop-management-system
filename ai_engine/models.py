from django.db import models
from django.conf import settings


class AIFeed(models.Model):
	"""Persisted feed data sent from other pages (per-user or per-session)."""
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
	session_key = models.CharField(max_length=64, null=True, blank=True)
	payload = models.JSONField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		who = self.user.username if self.user else f"session:{self.session_key}"
		return f"AIFeed {self.id} ({who})"
