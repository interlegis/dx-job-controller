Installation instructions
=========================

:synopsis: Installing dx-job-controller

Installing
----------

You can use pip to install dx-job-controller for usage::

  $ pip install dx-job-controller

Development
-----------

dx-job-controller is hosted on github::

 https://github.com/interlegis/dx-job-controller/

Source code can be accessed by performing a Git clone.

Tracking the development version of *dx-job-controller* should be
pretty stable and will keep you up-to-date with the latest fixes.

  $ pip install -e git+https://github.com/interlegis/dx-job-controller.git#egg=dx-job-controller

You find the sources in src/job-controller now.

Keep in mind that the current code in the git repository may be different from 
the packaged release. It may contain bugs and backwards-incompatible changes 
but most likely also new goodies to play with.


Configuration
-------------

To enable `dx-job-controller` in your project you need to add ``job_controller``
and ``django_extensions`` to ``INSTALLED_APPS`` in your project's 
`settings.py` file:

.. code-block:: python
   
   INSTALLED_APPS = (
      ...
      'django_extensions',
      'job_controller',
   )

run ``python manage.py migrate`` to create dx-job-controller database tables.

The next time you run your project and access the Django admin, voila! it will 
already have the Job controller app listed in your admin dashboard!

To ensure that django-extensions jobs are loaded and run, add the following
entry to your `crontab <https://man7.org/linux/man-pages/man5/crontab.5.html>`__:


.. code-block:: shell

      * * * * * python3 /your/project/path/manage.py runjob job_controller >> /var/log/django_cron.log 2>&1
   
this runs the ``job_controller`` job every minute and adds its output to the file 
`/var/log/django_cron.log`. See :doc:`job_controller` for
more details.