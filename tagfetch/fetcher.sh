#!/bin/sh
### BEGIN INIT INFO
# Provides:          fetcher
# Required-Start:
# Required-Stop:
# Default-Start:     3 4 5
# Default-Stop:      0 1 2 6
# Short-Description: Starts the Last.fm fetcher.
### END INIT INFO

# Inspired from (or blatantly copied from, depending on POV):
# https://github.com/fhd/init-script-template

# Allow user to be overridden.
if [ -z $user ]; then
    user="unison"
fi
# Allow root directory to be overridden.
if [ -z $root ]; then
    root="/var/unison-recsys"
fi
cmd="UNISON_ROOT=$root nohup $root/venv/bin/python $root/tagfetch/fetcher.py"

name=`basename $0`
pid_file="/var/run/$name.pid"
stdout_log="/var/log/$name.log"
stderr_log="/var/log/$name.err"

get_pid() {
    cat "$pid_file"    
}

is_running() {
    [ -f "$pid_file" ] && ps `get_pid` > /dev/null 2>&1
}

case "$1" in
    start)
  if is_running; then
      echo "Already started"
  else
      echo "Starting $name"
      cd "$dir"
            sudo -u "$user" $cmd >> "$stdout_log" 2>> "$stderr_log" \
    & echo $! > "$pid_file"
      if ! is_running; then
    echo "Unable to start, see $stdout_log and $stderr_log"
    exit 1
      fi
  fi
  ;;
    stop)
  if is_running; then
      echo "Stopping $name"
      kill `get_pid`
      rm "$pid_file"
  else
      echo "Not running"
  fi
  ;;
    restart)
  $0 stop
  $0 start
  ;;
    status)
  if is_running; then
      echo "Running"
  else
      echo "Stopped"
      exit 1
  fi
  ;;
    *)
  echo "Usage: $0 {start|stop|restart|status}"
  exit 1
  ;;
esac

exit 0
