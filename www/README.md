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

        <Directory %{ROOT}/www>
            Order allow,deny
            Allow from all
        </Directory>
    </VirtualHost>
