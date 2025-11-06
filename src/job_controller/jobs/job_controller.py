import threading
from django.db.models import F
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _, ngettext_lazy
from django_extensions.management.jobs import BaseJob
from django_extensions.management.jobs import get_job, get_jobs
from job_controller.models import Cronjob, JobSchedule

WHEN_SETS = {
    "minutely": "* * * * *",
    "QuarterHourly": "*/15 * * * *",
    "hourly": "0 * * * *",
    "daily": "0 0 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
    "yearly": "0 0 1 1 *",
}


class Job(BaseJob):
    help = _("Main job controller")

    def execute(self):
        print(_("Running job controller"))
        self.remove_old_jobs()
        self.sync_new_jobs()
        self.run_scheduled()
        self.schedule_jobs()
        self.digest_emails()
        self.remove_old_logs()

    def remove_old_jobs(self):
        """
        Remove from the jobs table those that were removed from the code
        """

        print(
            "\t",
            _(
                "Remove from the jobs table those that were removed "
                "from the code..."
            ),
        )
        all_jobs = get_jobs()
        excludes = Cronjob.objects.all()
        for app_name, job_name in all_jobs.keys():
            excludes = excludes.exclude(app_name=app_name, job_name=job_name)
        print("\t\t", excludes.delete())

    def sync_new_jobs(self):
        """
        Update the jobs table with the new jobs that have been created
        """
        print(
            "\t",
            _(
                "Update the jobs table with the new jobs that have "
                "been created..."
            ),
        )
        all_jobs = get_jobs()
        for (app_name, job_name), JobClass in all_jobs.items():
            # Ignore job_controller
            if app_name == "job_controller" and job_name == "job_controller":
                continue
            try:
                job = Cronjob.objects.get(app_name=app_name, job_name=job_name)
            except Cronjob.DoesNotExist:
                # Insert the job in job table #
                job_obj = JobClass()
                if job_obj.when in WHEN_SETS:
                    cron_expression = WHEN_SETS[job_obj.when]
                else:
                    cron_expression = WHEN_SETS["daily"]  # Default
                job = Cronjob(
                    app_name=app_name,
                    job_name=job_name,
                    cron_expression=cron_expression,
                )
                job.save()
                print(
                    "\t\t",
                    _("New job found at {app_name}: {job_name}: {help}").format(
                        app_name=app_name, job_name=job_name, help=job_obj.help
                    ),
                )

    def run_scheduled(self):
        """Run scheduled jobs"""
        print("\t", _("Run scheduled jobs..."))
        for schedule in JobSchedule.objects.filter(
            status=JobSchedule.STATUS_SCHEDULED,
            start__lte=timezone.localtime(),
        ):
            thread = threading.Thread(target=self._job_starter, args=(schedule))
            thread.start()

    def _job_starter(self, schedule):
        if schedule is None or not isinstance(schedule, JobSchedule):
            print("\t\t", _("no job to run"))
            return
        print(
            "\t\t",
            _("{job_name} started at {start}").format(
                job_name=schedule.job.job_name, start=timezone.localtime()
            ),
        )
        try:
            schedule.run_job()
        except JobSchedule.DoesNotExecute:
            print(
                "\t\t",
                _(
                    "Error trying run job {job_name}: "
                    "job schedule in '{status}' status."
                ).format(
                    job_name=schedule.job.job_name,
                    status=schedule.get_status_display(),
                ),
            )
        print(
            "\t\t",
            _("{job_name} finished at {finish}").format(
                job_name=schedule.job.job_name, finish=timezone.localtime()
            ),
        )

    def schedule_jobs(self):
        """Create schedule for next run"""
        print("\t", _("Create schedule for next run..."))
        for job in Cronjob.objects.exclude(
            jobschedule__status__in=[
                JobSchedule.STATUS_SCHEDULED,
                JobSchedule.STATUS_RUNNING,
            ]
        ):
            schedule = job.next_schedule()
            print(
                "\t\t",
                _("Scheduled job {job_name} for {start}").format(
                    job_name=schedule.job.job_name,
                    start=localize(schedule.start),
                ),
            )

    def remove_old_logs(self):
        print("\t", _("Delete old logs..."))
        for job in Cronjob.objects.exclude(log_duration=0):
            limit_time = timezone.localtime() - timezone.timedelta(
                days=job.log_duration
            )
            result = JobSchedule.objects.filter(
                job=job,
                status=JobSchedule.STATUS_FINISHED,
                started__lt=limit_time,
                reported=True,
            ).delete()
            if result[0] > 0:
                print(
                    "\t\t",
                    ngettext_lazy(
                        "one log deleted from '{job}' job",
                        "{count} logs deleted from '{job}' job",
                        result[0],
                    ).format(job=job, count=result[0]),
                )

    def digest_emails(self):
        """Generate log summary and send by email"""
        print("\t", _("Generate log summary and send by email..."))
        now = timezone.now()
        jobs = Cronjob.objects.exclude(email_recipient="")
        for job in jobs:
            if not (
                job.last_digest is None
                or job.last_digest
                <= timezone.now() - timezone.timedelta(days=job.digest_days)
            ):
                continue
            all_rounds = job.jobschedule_set.filter(
                reported=False, status=JobSchedule.STATUS_FINISHED
            )
            if job.error_only:
                rounds = all_rounds.filter(has_errors=True)
            else:
                rounds = all_rounds.all()
            if not rounds.exists():
                continue
            context = {
                "job": job,
                "rounds": rounds,
            }
            message = render_to_string(
                "job_controller/digest_txt.html", context
            )
            html_message = render_to_string(
                "job_controller/digest_html.html", context
            )
            send_mail(
                subject=_("Digest JOB: {job_name}").format(
                    job_name=job.job_name
                ),
                message=message,
                from_email=settings.SERVER_EMAIL,
                recipient_list=job.get_emails_list(),
                fail_silently=True,
                html_message=html_message,
            )
            all_rounds.update(reported=True)
