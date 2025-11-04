# dx-job-controller
Django admin interface for dango-extensions cronjobs

**Dx-job-controller** is a Django admin interface for managing cronjobs created
with the [django-extensions package](https://django-extensions.readthedocs.io/en/latest/jobs_scheduling.html)


Main features:
  * cronjob management via the Django admin interface,
  * defines the execution time of each job directly in the interface, without
    the need for changes to the crontab,
  * executes concurrent jobs using [threading](https://docs.python.org/3/library/threading.html),
  * retains job messages with each run (log),
  * sends emails with log summaries.

## Requirements:

- Python>=3.10
- Django>=5.1
- Django-extensions>=5.2

## Getting it

You can get **dx-job-controller** by using pip::

 $ pip install dx-job-controller

If you want to install it from source, pip directly from git repository::

 $ pip install git+https://github.com/interlegis/dx-job-controller.git

## Installing it

To enable **dx-job-controller** in your project you need to add `job_controller`
and `django_extensions` to `INSTALLED_APPS` in your project's `settings.py` 
file:

```python
   INSTALLED_APPS = (
      ...
      'django_extensions',
      'job_controller',
   )
```

run `python manage.py migrate` to create **dx-job-controller** database tables.

The next time you run your project and access the Django admin, voila! it will 
already have the Job controller app listed in your admin dashboard!

## Compatibility with versions of Python and Django

We follow the Django guidelines for supported Python and Django versions. 
See more at [Django Supported Versions](https://docs.djangoproject.com/en/dev/internals/release-process/#supported-versions)

This might mean the **dx-job-controller** may work with older or unsupported 
versions  but we do not guarantee it and most likely will not fix bugs related 
to incompatibilities with older versions.

## Documentation

The complete documentation can be found at https://job-controller.readthedocs.io/
Or you can look at the docs/ directory in the repository.

## Getting Involved

Job controller is free and always will be. It is developed and maintained by 
developers in an Open Source manner. Any support is welcome. You could help by 
writing documentation, pull-requests, report issues and/or translations.
