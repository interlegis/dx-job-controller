Job controller
==============

:synopsis: How the job-controller works

The job controller is a common job created with `django-extensions` to control 
other jobs in the system. Ideally, it should run every minute, but this isn't 
mandatory and will depend on your needs.

Its ``run`` method executes the following tasks in sequence:

Remove old jobs
---------------

Remove from the jobs table those that were removed from the code. Whenever a 
job is removed from the code, its record in the `cronjobs` table is also 
removed, along with all execution and scheduling records.

Sync new jobs
-------------

Add in the jobs table those new jobs that were been created in the code.
Whenever a new job is created in the code, a record in the cronjobs table is 
added to represent it in the admin interface.

Run scheduled jobs
------------------

IdentiIdentifies the jobs that are scheduled to run at this time (scheduled 
start is less than or equal to now) and invokes them encapsulated in a 
``threading.Thread`` object to take advantage from execution parallelism.

The schedule status is changed to `Running` to ensure that neither the user 
nor another instance of the `job-controller` starts another job execution.

If the running job throws any exception, the error message will be captured 
and saved in the `Jobschedule` result field and the `has_errors` field will 
be set to True.

`Stdout` and `stderr` are captured and added to the Jobschedule's `result` 
field. If there is any text in `stderr`, the `has_errors` field is set to True.

Schedule jobs
-------------

Creates scheduling records to the next execution for jobs that do not have 
any records with the status `running` or `scheduled`.

Digest emails
-------------

Generates log summary and send it by email.

Remove old logs
---------------

Delete old logs from database.