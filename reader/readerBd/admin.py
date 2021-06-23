from django.contrib import admin

from .models import ControlTime, Day, ScheduleDuty, ListEvents, OrderOfDuty, Event


admin.site.register(ControlTime)
admin.site.register(Day)
admin.site.register(Event)
admin.site.register(ScheduleDuty)
admin.site.register(ListEvents)
admin.site.register(OrderOfDuty)
