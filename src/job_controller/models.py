import io
from contextlib import redirect_stderr, redirect_stdout
from cron_converter import Cron
from datetime import timedelta
from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from django_extensions.management.jobs import get_job, get_jobs


class Cronjob(models.Model):
    app_name = models.CharField(_("app"), max_length=100, editable=False)
    job_name = models.CharField(_("job"), max_length=100, editable=False)
    cron_expression = models.CharField(
        _("CRON expression"),
        max_length=100,
        default="* * * * *",
        help_text=_(
            """
            Use expressions in standard CRON format:<br/>
            <code>minute hour day month day-of-week</code><br/>
            More details:
            <a href='https://help.ubuntu.com/community/CronHowto'>CronHowTo</a>
            """
        ),
    )
    log_duration = models.PositiveIntegerField(
        _("days to retain log"),
        help_text=_(
            "Number of days that execution logs will be kept in the "
            "database. Zero means the log will never be deleted."
        ),
        default=30,
    )
    email_recipient = models.TextField(
        _("email recipient(s)"),
        help_text=_(
            "E-mails to send job execution reports.<br/>"
            "Enter one email address per line. "
            "Leave empty to not send e-mail reports"
        ),
        blank=True,
    )
    digest_days = models.PositiveIntegerField(
        _("days to digest"),
        default=0,
        help_text=_(
            "How many days to wait to make a summary of reports.<br/>"
            "zero means the email should be sent immediately after execution."
        ),
    )
    error_only = models.BooleanField(
        _("report just errors"),
        default=False,
        help_text=_(
            "Send reports by email only when job execution error occurs"
        ),
    )
    last_digest = models.DateTimeField(
        _("last digest submission"), blank=True, null=True, editable=False
    )

    def get_emails_list(self):
        return [
            email.strip()
            for email in self.email_recipient.splitlines()
            if email.strip()
        ]

    @admin.display(description=_("description"))
    def get_description(self):
        try:
            JobClass = get_job(self.app_name, self.job_name)
        except KeyError:
            return _("The job {app_name}.{job_name} was not found.").format(
                app_name=self.app_name, job_name=self.job_name
            )
        if JobClass.__doc__:
            if JobClass.help:
                return "\n".join([JobClass.__doc__, JobClass.help])
            else:
                return JobClass.__doc__
        elif JobClass.help:
            return JobClass.help
        else:
            return f"{self.app_name}.{self.job_name}"

    class Meta:
        ordering = ("app_name", "job_name")
        verbose_name = _("Cron job")
        verbose_name_plural = _("Cron jobs")

    def __str__(self):
        return self.job_name

    def run(self):
        try:
            JobClass = get_job(self.app_name, self.job_name)
        except KeyError:
            return (
                True,
                _(
                    "The JOB routine {job_name} of the app "
                    "{app_name} was not found."
                ).format(job_name=self.job_name, app_name=self.app_name),
            )
        try:
            job_obj = JobClass()
            with io.StringIO() as so_buf, io.StringIO() as se_buf, redirect_stdout(
                so_buf
            ), redirect_stderr(
                se_buf
            ):
                job_obj.execute()
                messages = so_buf.getvalue()
                errors = se_buf.getvalue()
            report_data = []
            if messages:
                report_data.extend(
                    ["", _("MESSAGES"), "-" * len(_("MESSAGES")), ""]
                )
                report_data.extend(messages.splitlines())
            has_errors = False
            if errors:
                has_errors = True
                report_data.extend(
                    ["", _("ERRORS"), "-" * len(_("ERRORS")), ""]
                )
                report_data.extend(errors.splitlines())
            return (has_errors, "\n".join(report_data))
        except Exception as e:
            # Any error must be reported
            return (
                True,
                _("Job aborted with error: {str_err}").format(str_err=str(e)),
            )

    def next_schedule(self):
        """
        Retrieves or create the schedule for the next run.
        """
        try:
            schedule = self.jobschedule_set.get(
                status__in=[
                    JobSchedule.STATUS_SCHEDULED,
                    JobSchedule.STATUS_RUNNING,
                ]
            )
        except JobSchedule.DoesNotExist:
            start = self.get_next_schedule_time()
            schedule = JobSchedule(job=self, start=start)
            schedule.save()
        return schedule

    def get_next_schedule_time(self):
        cron_instance = Cron(self.cron_expression)
        scheduller = cron_instance.schedule(timezone.localtime())
        return scheduller.next()


class JobSchedule(models.Model):
    STATUS_SCHEDULED = "S"
    STATUS_RUNNING = "R"
    STATUS_FINISHED = "F"
    STATUS_CHOICES = (
        (STATUS_SCHEDULED, _("Scheduled")),
        (STATUS_RUNNING, _("Running")),
        (STATUS_FINISHED, _("Finished")),
    )
    job = models.ForeignKey(
        Cronjob, verbose_name=_("cron job"), on_delete=models.CASCADE
    )
    start = models.DateTimeField(_("start at"))
    started = models.DateTimeField(_("started at"), blank=True, null=True)
    status = models.CharField(
        _("status"),
        max_length=1,
        choices=STATUS_CHOICES,
        default=STATUS_SCHEDULED,
    )
    time_spent = models.DurationField(
        _("time spent on execution"), blank=True, null=True, editable=False
    )
    result = models.TextField(_("execution result"), blank=True, editable=False)
    has_errors = models.BooleanField(_("has errors"), null=True, editable=False)
    reported = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ("-start",)
        verbose_name = _("run schedule")
        verbose_name_plural = _("run schedules")

    class DoesNotExecute(Exception):
        """
        This scheduled job cannot be executed because not in SCHEDULED state
        """

        pass

    def get_time_spent_display(self):
        if self.time_spent is None:
            return _("no time")
        result = []
        if self.time_spent.days > 0:
            result.append(
                ngettext_lazy(
                    "one day",
                    "{days} days",
                    self.time_spent.days,
                ).format(days=self.time_spent.days)
            )
        seconds = self.time_spent.seconds
        if seconds > 0:
            if seconds >= 3600:
                result.append(
                    ngettext_lazy(
                        "one hour", "{hours} hours", seconds // 3600
                    ).format(hours=seconds // 3600)
                )
                seconds = seconds % 3600
            if seconds >= 60:
                result.append(
                    ngettext_lazy(
                        "one minute", "{minutes} minutes", seconds // 60
                    ).format(minutes=seconds // 60)
                )
                seconds = seconds % 60
            if seconds > 0:
                result.append(
                    ngettext_lazy(
                        "one second", "{seconds} seconds", seconds
                    ).format(seconds=seconds)
                )
        else:
            if self.time_spent.microseconds > 0:
                result.append(
                    ngettext_lazy(
                        "one microsecond",
                        "{microseconds} microseconds",
                        self.time_spent.microseconds,
                    ).format(microseconds=self.time_spent.microseconds)
                )
        return ", ".join(result)

    def __str__(self):
        if self.status == JobSchedule.STATUS_SCHEDULED:
            return _("{job_name}: scheduled start for {start}.").format(
                job_name=self.job.job_name,
                start=localize(timezone.localtime(self.start)),
            )
        elif self.status == JobSchedule.STATUS_RUNNING:
            return _("{job_name}: running since {started}").format(
                job_name=self.job.job_name,
                started=localize(timezone.localtime(self.started)),
            )
        return _(
            "{job_name}: run on {started}, taking {time_spent} to complete"
        ).format(
            job_name=self.job.job_name,
            started=localize(timezone.localtime(self.started)),
            time_spent=localize(self.time_spent),
        )

    def run_job(self):
        """
        Run the scheduled job.

        This method does not check if the schedule is on time, it just runs
        the associated job.

        Raises:
            JobSchedule.DoesNotExecute: if the job schedule is not in
            JobSchedule.STATUS_SCHEDULED status
        """

        if self.status != JobSchedule.STATUS_SCHEDULED:
            raise JobSchedule.DoesNotExecute()

        self.started = timezone.localtime()
        self.status = JobSchedule.STATUS_RUNNING
        self.save()
        has_errors, result = self.job.run()
        self.result = result
        self.has_errors = has_errors
        self.status = JobSchedule.STATUS_FINISHED
        self.time_spent = timezone.localtime() - self.started
        self.save()
