#!/bin/sh

DESC="ThirdPartyBroker daemon process for TA3.1 baseline"
NAME=ThirdPartyBroker
PIDFILE=/home/$USER/spar-testing/config/$NAME.pid
COMMAND=/usr/bin/java

if [ ! -z "$2" ]; then 
  HOST=-h $2
fi
if [ ! -z "$3" ]; then 
  PORT=-p $3
fi

OPTS="-jar ../../java/jars/ThirdPartyBroker.jar $HOST $PORT"
echo Executing $COMMAND -- $OPTS as $USER from $PWD

d_start() {
    /sbin/start-stop-daemon --start --quiet --background --make-pidfile --pidfile $PIDFILE --chuid $USER --chdir $PWD --exec $COMMAND -- $OPTS
}

d_stop() {
    /sbin/start-stop-daemon --stop --quiet --pidfile $PIDFILE
    if [ -e $PIDFILE ]
        then rm $PIDFILE
    fi
}

case $1 in
    start)
    echo -n "Starting $DESC: $NAME"
    d_start
    echo "."
    ;;
    stop)
    echo -n "Stopping $DESC: $NAME"
    d_stop
    echo "."
    ;;
    restart)
    echo -n "Restarting $DESC: $NAME"
    d_stop
    sleep 1
    d_start
    echo "."
    ;;
    *)
    echo "usage: $NAME {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
