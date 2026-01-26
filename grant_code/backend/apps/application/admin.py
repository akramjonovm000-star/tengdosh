from django.contrib import admin
from .models import Application, Question, Answer, Item, Criterion, Attempt, Appeal, Quota
# Register your models here.

admin.site.register(Application)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Item)
admin.site.register(Criterion)
admin.site.register(Attempt)
admin.site.register(Appeal)
admin.site.register(Quota)
