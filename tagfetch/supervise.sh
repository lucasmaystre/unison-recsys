#!/bin/sh
# Simple supervision script for the fetcher service.
# Author: Lucas Maystre <lucas@maystre.ch>

/etc/init.d/fetcher status
if [ $? -ne 0 ]; then
    /etc/init.d/fetcher restart
fi
