Digest mail
===========

:synopsis: Explains digest mail functionality

How it works
------------

Jobs are executed within a `try` ... `exception` block. If an exception is 
thrown, its error message is persisted in the `result` field of the 
`Jobschedule` object.

Additionally, the outputs of `stdout` and `stderr` are captured and persisted 
in the same way as error messages.

When an error occurs, either due to an exception or some text present in 
`stderr`, the `has_error` flag in the `Jobschedule` object is set to `True` 
to indicate that this execution encountered problems.

Therefore, when writing your jobs, it is a good practice to throw exceptions 
when critical problems that prevent the `job` from completing occur, and to 
send non-critical error and warning messages to `stderr`. To print to 
`stderr` in Python, use the syntax:

.. code-block:: python

    import sys
    print("This message goes to stderr.", file=sys.stderr)

If necessary, explanatory messages can be sent to `stdout`.

Execution summaries
-------------------

Execution summaries are produced by combining one or more execution logs, 
depending on the frequency of summary submissions.

Two templates are used to generate the summary report: 

 * `job_controller/digest_txt.html` and 
 * `job_controller/digest_html.html`.
 
 The first generates a plain text containing the logs to be sent, and the other 
 generates an HTML snippet of the same logs.

Both templates receive the following context variables:

* **job**: The Cronjob object being processed
* **rounds**: A queryset containing all the logs that will be reported in 
  the summary.

Sending emails
--------------

To send emails we use the `send_mail` function from the `django.core.mail` 
package (`see Django sending email <https://docs.djangoproject.com/en/5.2/topics/email/#send-mail>`__).

The text produced with the `digest_txt.html` template is sent as a `message` 
and the html snippet produced by the `digest_html.html` template is sent as 
`html_message` in case the recipient's email client is able to display html.

The email sender (`from_email` parameter of `send_mail` function) is set to
``settings.SERVER_EMAIL``, the same email address that Django uses to send 
error messages.

Email sending fails silently if the SMTP server is not correctly configured in 
the Django settings or if some other problem occurs.

Customizing summaries
---------------------

You can customize the appearance of summary reports by overwriting the 
templates.

To define your own templates, create a `job_controller` folder inside the 
`templates` folder of your project or in the `templates` folder of some app 
in your project and then write the desired new template inside that folder,
keeping the original template names.

The original templates are these:

job_controller/digest_txt.html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: django

    {% load i18n %}{% translate "report" as t_report %}{% blocktranslate with digest_days=job.digest_days asvar t_last_days %}Last {digest_days} days{% endblocktranslate %}{{ job.get_description }} ({{ job.job_name }}) {% if job.digest_days == 0 %}{{ t_report}}{% else %}{{ t_last_days }}{% endif %}
    {% for s in job.get_description %}={% endfor %}=={% for s in job.job_name %}={% endfor %}=={% if job.digest == 0 %}{% for s in t_report %}={% endfor %}{% else %}{% for s in t_last_days %}={% endfor %}{% endif %}

    {% for run in rounds %}{% blocktranslate with started=run.started|date:"SHORT_DATETIME_FORMAT" time_spent=run.get_time_spent_display %}* runned at {{ started }} taking {{ time_spent }} to finish:{% endblocktranslate %}{% if run.result == "" %}{% translate " no reports" %}{% else %}

    {% for row in run.result.splitlines %}   {{ row }}
    {% endfor %}{% endif %}
    {% endfor %}

job_controller/digest_html.html
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: django

    {% load i18n %}
    <h1>
    {{ job.get_description }} ({{ job.job_name }})
    {% if job.digest_days == 0 %}
        {% translate "report" %}
    {% else %}
        {% blocktranslate with digest_days=job.digest_days %}Last {digest_days} days{% endblocktranslate %}
    {% endif %}
    </h1>

    <ul>
    {% for run in rounds %}
        <li>
        <strong>
            {% blocktranslate with started=run.started|date:"SHORT_DATETIME_FORMAT" time_spent=run.get_time_spent_display %}
            runned at {{ started }} taking {{ time_spent }} to finish:
            {% endblocktranslate %}
        </strong>
        {% if run.result == "" %}
            {% translate " no reports" %}
        {% else %}
            <pre>{{ run.result }}</pre>
        {% endif %}
        </li>
    {% endfor %}
    </ul>
