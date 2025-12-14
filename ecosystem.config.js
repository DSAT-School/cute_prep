module.exports = {
  apps: [
    // Django Application (Gunicorn)
    {
      name: 'practice-portal-final',
      script: 'venv/bin/gunicorn',
      args: 'config.wsgi:application --bind 127.0.0.1:7777 --workers 4 --timeout 120',
      interpreter: 'none',
      cwd: '/home/raju/dsatschool-product/practice_portal',
      env: {
        DJANGO_SETTINGS_MODULE: 'config.settings.prod',
        PYTHONPATH: '/home/raju/dsatschool-product/practice_portal'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/home/raju/dsatschool-product/practice_portal/logs/pm2-error.log',
      out_file: '/home/raju/dsatschool-product/practice_portal/logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    
    // Celery Worker
    {
      name: 'celery-worker',
      script: 'venv/bin/celery',
      args: '-A config worker --loglevel=info --concurrency=4',
      interpreter: 'none',
      cwd: '/home/raju/dsatschool-product/practice_portal',
      env: {
        DJANGO_SETTINGS_MODULE: 'config.settings.prod',
        PYTHONPATH: '/home/raju/dsatschool-product/practice_portal'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: '/home/raju/dsatschool-product/practice_portal/logs/celery-worker-error.log',
      out_file: '/home/raju/dsatschool-product/practice_portal/logs/celery-worker-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    
    // Celery Beat Scheduler
    {
      name: 'celery-beat',
      script: 'venv/bin/celery',
      args: '-A config beat --loglevel=info',
      interpreter: 'none',
      cwd: '/home/raju/dsatschool-product/practice_portal',
      env: {
        DJANGO_SETTINGS_MODULE: 'config.settings.prod',
        PYTHONPATH: '/home/raju/dsatschool-product/practice_portal'
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      error_file: '/home/raju/dsatschool-product/practice_portal/logs/celery-beat-error.log',
      out_file: '/home/raju/dsatschool-product/practice_portal/logs/celery-beat-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
