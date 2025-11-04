from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, path
from django.utils import timezone
from django.utils.formats import localize
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_extensions.management.jobs import get_job, get_jobs
from .models import Cronjob, JobSchedule


class JobScheduleInline(admin.TabularInline):
    model = JobSchedule
    fields = [
        "status",
        "start",
        "started",
        "time_spent",
        "has_errors",
        "get_runner",
    ]
    readonly_fields = fields
    can_delete = False
    can_add = False
    extra = 0

    def has_add_permission(self, request, obj):
        return False

    @mark_safe
    @admin.display(description=_("view/run"))
    def get_runner(self, sched):
        if sched.status == JobSchedule.STATUS_SCHEDULED:
            url = reverse(
                "admin:job_controller_jobschedule_runjob", args=[sched.id]
            )
            return f"<a href='{url}' title='{_('Run')}'>{_('Run')}</a>"
        elif sched.status == JobSchedule.STATUS_FINISHED:
            url = reverse(
                "admin:job_controller_jobschedule_change", args=[sched.id]
            )
            return (
                f"<a href='{url}' title='{_('View result')}'>"
                f"{_('View result')}</a>"
            )
        return ""


@admin.register(Cronjob)
class CronjobAdmin(admin.ModelAdmin):
    list_display = (
        "job_name",
        "app_name",
        "get_description",
        "cron_expression",
        "get_schedule",
        "get_runner",
        "last_digest",
    )
    fields = [
        "job_name",
        "app_name",
        "get_description",
        "cron_expression",
        "log_duration",
        "email_recipient",
        "digest_days",
        "error_only",
        "last_digest",
    ]
    readonly_fields = ("job_name", "app_name", "get_description", "last_digest")
    inlines = [JobScheduleInline]

    def get_urls(self):
        urls = super().get_urls()
        model_info = (self.model._meta.app_label, self.model._meta.model_name)

        my_urls = [
            path(
                "<path:object_id>/runjob/",
                self.admin_site.admin_view(self.run_job),
                name="%s_%s_runjob" % model_info,
            ),
        ]
        return my_urls + urls

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=...):
        return False

    @admin.display(description=_("next schedule"))
    def get_schedule(self, job):
        sched = job.jobschedule_set.first()
        if sched is None:
            return _("No schedules for this job")
        if sched.status == JobSchedule.STATUS_SCHEDULED:
            return _("scheduled start for {start}").format(
                start=localize(timezone.localtime(sched.start))
            )
        if sched.status == JobSchedule.STATUS_RUNNING:
            return _("running since {start}").format(
                start=localize(timezone.localtime(sched.started))
            )
        return _(
            "executed at {started}, taking {time_spent} to complete"
        ).format(
            started=localize(timezone.localtime(sched.started)),
            time_spent=localize(sched.time_spent),
        )

    @mark_safe
    @admin.display(description=_("run"))
    def get_runner(self, job):
        url = reverse("admin:job_controller_cronjob_runjob", args=[job.id])
        return f"<a href='{url}'>{_('run')}</a>"

    def run_job(self, request, object_id):
        cronjob = get_object_or_404(Cronjob, id=object_id)
        sched = cronjob.next_schedule()
        if sched.status != JobSchedule.STATUS_SCHEDULED:
            raise PermissionDenied(
                _(
                    "This schedule cannot be executed because its "
                    "status is {status}"
                )
            ).format(status=sched.get_status_display())
        sched.run_job()
        self.message_user(
            request,
            _("Job executed!"),
            messages.SUCCESS,
        )
        return redirect(
            "admin:job_controller_jobschedule_change", object_id=sched.id
        )


@admin.register(JobSchedule)
class JobScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "job",
        "status",
        "has_errors",
        "start",
        "started",
        "time_spent",
        "get_runner",
    ]
    fields = [
        "job",
        "status",
        "has_errors",
        "start",
        "started",
        "time_spent",
        "result",
    ]
    readonly_fields = fields
    list_filter = ("status", "job")
    date_hierarchy = "start"

    def get_urls(self):
        urls = super().get_urls()
        model_info = (self.model._meta.app_label, self.model._meta.model_name)

        my_urls = [
            path(
                "<path:object_id>/runjob/",
                self.admin_site.admin_view(self.run_job),
                name="%s_%s_runjob" % model_info,
            ),
        ]
        return my_urls + urls

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is None or obj.status == JobSchedule.STATUS_FINISHED:
            return super().has_delete_permission(request, obj)
        else:
            return False

    def has_change_permission(self, request, obj=None):
        return False

    @mark_safe
    @admin.display(description=_("run"))
    def get_runner(self, sched):
        if sched.status == JobSchedule.STATUS_SCHEDULED:
            url = reverse(
                "admin:job_controller_jobschedule_runjob", args=[sched.id]
            )
            return f"<a href='{url}'>{_('run')}</a>"
        return ""

    def run_job(self, request, object_id):
        sched = get_object_or_404(JobSchedule, id=object_id)
        if sched.status != JobSchedule.STATUS_SCHEDULED:
            raise PermissionDenied(
                _(
                    "This schedule cannot be executed because "
                    "its status is {status}"
                ).format(status=sched.get_status_display())
            )
        try:
            sched.run_job()
            self.message_user(
                request,
                _("Job executed!"),
                messages.SUCCESS,
            )
        except JobSchedule.DoesNotExecute:
            self.message_user(
                request,
                _("Job cannot be runned!"),
                messages.ERROR,
            )
        return redirect(
            "admin:job_controller_jobschedule_change", object_id=object_id
        )
