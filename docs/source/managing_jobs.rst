Managing jobs
=============

:synopsis: How to manage your jobs in *dx-job-controller* admin interface

After ``job_controller`` runs the first time (normally triggered by cron) 
the `Cronjob` table is populated with all jobs found in each app in 
your project.

Each `Cronjob` entry has the following fields:

  * **job** (Readonly): the cronjob class name,
  * **app** (Readonly): the app name where the cronjob was defined,
  * **description** (Readonly): the cronjob `docstring` and/or cronjob 
    `help` attribute,
  * **CRON expression**: the moment that this job will be run, in standard 
    `crontab format <https://help.ubuntu.com/community/CronHowto>`__,
  * **days to retain log**: Number of days that execution logs will be kept in 
    the database. Zero means the log will never be deleted,
  * **email recipient(s)**: a list of emails to send job execution reports, 
    one per line,
  * **days to digest**: How many days to wait to make a summary of reports,
    zero means the email should be sent immediately after execution,
  * **report just errors**: Send reports by email only when job execution 
    error occurs,
  * **last digest submission** (Readonly): the last time the execution report
    email was sent.

Defining when a job should run
------------------------------

for each job you can set the ``CRON expression`` to define when this job will
be executed.

Cron expressions must have the standard crontab format (see: `CronHowto
<https://help.ubuntu.com/community/CronHowto>`__). They are evaluated by the 
`cron-converter <https://pypi.org/project/cron-converter/>`__ component 
(thanks `Andrea Salvatori <https://github.com/Sonic0>`__).

When the Crontab table is populated, the `when` property of the Job class is 
evaluated to set the initial value of the `CRON expression`:

.. table:: when / crontab equivalece table
  :widths: auto

  +---------------+--------------------------+
  | when property | Result `CRON expression` |
  +===============+==========================+
  | minutely      | ``* * * * *``            |
  +---------------+--------------------------+
  | QuarterHourly | ``*/15 * * * *``         |
  +---------------+--------------------------+
  | hourly        | ``0 * * * *``            |
  +---------------+--------------------------+
  | daily         | ``0 0 * * *``            |
  +---------------+--------------------------+
  | weekly        | ``0 0 * * 0``            |
  +---------------+--------------------------+
  | monthly       | ``0 0 1 * *``            |
  +---------------+--------------------------+
  | yearly        | ``0 0 1 1 *``            |
  +---------------+--------------------------+

If the Job class does not have a ``when`` attribute or if its value is not in 
the above table, then the cron expression used is ``0 0 * * *`` (`daily`).

Job reports
-----------

**dx-job-controller** collects job output and saves it as run logs. These 
logs are available for viewing and can be emailed as summary reports.

Log retention time
^^^^^^^^^^^^^^^^^^

You can set the number of days that logs will be kept in the database. After
this period, the execution logs will be permanently deleted.

Email summaries
^^^^^^^^^^^^^^^

**dx-job-controller** can email log summaries to a list of users provided 
by the ``email recipient(s)`` field. The summary is composed by concatenation
of all logs generated in previous runs of a job.

Admin users can set the frequency, in days, of sending the summary email in the
field ``days to digest``.

If the ``report just errors`` field is checked, only logs from runs where 
errors occurred will be added to the summary.