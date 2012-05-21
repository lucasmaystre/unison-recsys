Example Apache configuration file (suppose ROOT is the root folder for Unison):

    # Use name-based virtual hosting.
    NameVirtualHost *:80

    <VirtualHost *:80>
        ServerAdmin lum@unison.local
        ServerName api.unison.local
        DocumentRoot "%{ROOT}/api"
        ErrorLog "/private/var/log/apache2/api.unison.local-error_log"
        CustomLog "/private/var/log/apache2/api.unison.local-access_log" common
        LogLevel info

        # Set an environment variables that the WSGI app can access.
        SetEnv UNISON_ROOT %{ROOT}

        # Set up WSGI so that it includes the packages from the virtual env.
        WSGIDaemonProcess unison-api \
          python-path=%{ROOT}/venv/lib/python2.6/site-packages
        WSGIProcessGroup unison-api

        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptAlias / %{ROOT}/api/unison.wsgi

        # Pass the authentication headers to the app.
        WSGIPassAuthorization On

        <Directory %{ROOT}/api>
            Order allow,deny
            Allow from all
        </Directory>
    </VirtualHost>
