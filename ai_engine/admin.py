from django.contrib import admin
from .models import AIFeed


@admin.register(AIFeed)
class AIFeedAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'session_key', 'created_at', 'payload_preview')
	readonly_fields = ('created_at',)
	search_fields = ('user__username', 'session_key')
	list_filter = ('created_at',)

	def payload_preview(self, obj):
		text = str(obj.payload)
		return (text[:120] + '...') if len(text) > 120 else text

	payload_preview.short_description = 'Payload (preview)'
