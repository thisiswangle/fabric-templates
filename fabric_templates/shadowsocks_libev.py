#coding=utf8

import tempfile

from fabric.api import *
from fabric.contrib.files import *

users = [
        ("8080","nopasswd"),
        ("8081","nopasswd"),
        ("8082","nopasswd"),
        ("8083","nopasswd"),
        ("8084","nopasswd"),
        ("8085","nopasswd"),
        ("8086","nopasswd"),
        ("8087","nopasswd"),
        ("8088","nopasswd"),
        ("8089","nopasswd"),
        ("8090","nopasswd"),
        ("8988","nopasswd")
        ]

method = "aes-256-cfb"


monit="""check process user-{0} with pidfile /opt/shadowsocks/user-{0}/shadowsocks.pid
    start program = "/opt/shadowsocks/user-{0}/ssserver start"
    stop program = "/opt/shadowsocks/user-{0}/ssserver stop"
"""

ssserver="""#!/bin/bash
PID=/opt/shadowsocks/user-{0}/shadowsocks.pid
LOG=/opt/shadowsocks/user-{0}/shadowsocks.log

function start_app {{
    nohup ss-server -s 0.0.0.0 -p {0} -k {1} -m {2} 1>>"$LOG" 2>&1 &
    echo $! > "$PID"
}}

function stop_app {{
    if ps -p `cat $PID` > /dev/null
    then
        kill `cat $PID`
    fi
}}

case $1 in
    start)
        start_app ;;
    stop)
        stop_app ;;
    restart)
        stop_app
        start_app
        ;;
    *)
        echo "usage: ssserver [start|stop|restart]" ;;
esac
exit 0

"""
def install():
    sudo("apt-get update")
    sudo("apt install software-properties-common monit -y")
    sudo("add-apt-repository ppa:max-c-lv/shadowsocks-libev -y")
    sudo("apt-get update")
    sudo("apt install shadowsocks-libev -y")

def config():
    # make monit auto start
    sudo("systemctl enable monit")

    # user config
    for user in users:
        (port, passwd) = user
        # mkdir
        workdir = '/opt/shadowsocks/user-%s' % port
        sudo('mkdir -p %s' % workdir)

        # write ssserver
        remote_ssserver = '%s/ssserver' % workdir
        local_ssserver = tempfile.mktemp('.sh')
        content = ssserver.format(port, passwd, method)
        with open(local_ssserver, 'w') as f:
            f.write(content)
        put(local_ssserver, remote_ssserver, use_sudo=True, mode="755")

        # write monit conffile
        remote_monit = '%s/monit.conf' % workdir
        local_monit = tempfile.mktemp('.conf')
        content = monit.format(port, passwd, method)
        with open(local_monit, 'w') as f:
            f.write(content)
        put(local_monit, remote_monit, use_sudo=True, mode="644")

        # clear solf link is exist
        sudo('rm -f /etc/monit/conf.d/user-%s.conf' % (workdir, port))

        # make soft link
        sudo('ln -s %s/monit.conf /etc/monit/conf.d/user-%s.conf' % (workdir, port))


