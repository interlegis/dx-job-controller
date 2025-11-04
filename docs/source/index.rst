Welcome to dx-job-controller's documentation!
=============================================

**Dx-job-controller** is a Django admin interface for managing cronjobs created
with the `django-extensions package 
<https://django-extensions.readthedocs.io/en/latest/jobs_scheduling.html>`__


Main features:
  * cronjob management via the Django admin interface,
  * defines the execution time of each job directly in the interface, without
    the need for changes to the crontab,
  * executes concurrent jobs using `threading <https://docs.python.org/3/library/threading.html>`__,
  * retains job messages with each run (log),
  * sends emails with log summaries.

Getting Started
---------------

You can get dx-job-controller by using pip::

 $ pip install dx-job-controller

If you want to install it from source, pip directly from git repository::

 $ pip install git+https://github.com/interlegis/dx-job-controller.git

For more detailed instructions check out our :doc:`installation_instructions`. 
Enjoy.

Compatibility with versions of Python and Django
=================================================

We follow the Django guidelines for supported Python and Django versions. 
See more at `Django Supported Versions <https://docs.djangoproject.com/en/dev/internals/release-process/#supported-versions>`__

This might mean the dx-job-controller may work with older or unsupported versions 
but we do not guarantee it and most likely will not fix bugs related to 
incompatibilities with older versions.

Contents
--------

.. toctree::

    installation_instructions
    admin_interface
    managing_jobs
    job_controller
    digest_mail
