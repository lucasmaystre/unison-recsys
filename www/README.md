Example Apache configuration file (suppose ROOT is the root folder for Unison):

    # Use name-based virtual hosting.
    NameVirtualHost *:80

    <VirtualHost *:80>
        ServerAdmin lum@unison.local
        ServerName unison.local
        DocumentRoot "%{ROOT}/www"
        ErrorLog "/private/var/log/apache2/unison.local-error_log"
        CustomLog "/private/var/log/apache2/unison.local-access_log" common
        LogLevel info

        # Set an environment variables that the WSGI app can access.
        SetEnv UNISON_ROOT %{ROOT}

        # Set up WSGI so that it includes the packages from the virtual env.
        WSGIDaemonProcess unison-www \
          python-path=%{ROOT}/venv/lib/python2.6/site-packages
        WSGIProcessGroup unison-www

        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptAlias / %{ROOT}/www/www.wsgi

        <Directory %{ROOT}/www>
            Order allow,deny
            Allow from all
        </Directory>
    </VirtualHost>
