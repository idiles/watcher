#!/usr/bin/env python
#
# IDILES Watcher
# Copyright (c) 2007 IDILES SYSTEMS
#
# This is watch-dog like application for watching another applications.
#

import os
import sys
import popen2
import urllib
import smtplib
import socket
from datetime import datetime
from ping import ping


class DataObject():
    pass


class Configuration(object):
    """Configuration class."""

    def __init__(self, config_file):
        self.file = config_file
        self.applications = []
        self.watcher = DataObject()
        self._load()

    def _load(self):
        self.file.seek(0)
        lines = self.file.readlines()

        in_app = False
        in_global = False
        app = None

        for n, line in enumerate(lines):
            if line.startswith("#"):
                continue
            elif line.startswith("application:"):
                in_global = False
                in_app = True
                if app is not None:
                    self.applications.append(app)
                    app = None
                app = DataObject()
                continue
            elif line.startswith("watcher:"):
                in_app = False
                in_global = True
                continue

            line = line.strip()
            if not line:
                continue
            
            key, value = line.split('=')
            key = key.strip().replace('-', '_')
            value = value.strip()

            if in_app:
                if key == 'name' and value in [a.name for a in
                    self.applications]:
                    in_app = False # Skip entire app block
                    continue
                else:
                    setattr(app, key, value)
            elif in_global:
                setattr(self.watcher, key, value)

        if app:
            self.applications.append(app)
            app = None


class URLReader(object):
    
    def read(self, url):
        """Read URL and return its contents."""

        try:
            resource = urllib.urlopen(url)
        except IOError, e:
            return str(e)
        return resource.read()


class PingReader(object):
    
    def read(self, host):
        """Ping host. Return 'OK' if packets returns, 'FAILURE' 
        otherwise."""

        import os
        env = os.environ.get('watcher-env', 'production')

        packets = ping(host, 2, env=env)
        if packets < 2:
            return 'FAILURE'
        return 'OK'


#
# XXX: May be wasteful memory consumption when reading large files
#
class FileReader(object):
    
    def read(self, path):
        """Read path and return file contents."""

        try:
            fd = open(path)
            data = fd.read()
            fd.close()
            return data
        except IOError, e:
            return str(e)

class Watcher(object):
    """The Watcher."""

    def __init__(self, config):
        self.config = config
        self.failures = []

    def run(self, repair=True):
        for app in self.config.applications:
            self.check(app)
        if repair:
            for app in self.failures:
                self.repair(app)

    def check(self, app):
        """Execute application checker."""
        trigger_opts = app.trigger.split()
        type = trigger_opts[0].lower()
        url = trigger_opts[1].lower()
        op = trigger_opts[2][:-1].lower()
        search_data = ' '.join(trigger_opts[3:])

        reader = None
        if type == 'url':
            reader = URLReader()
        elif type == 'file':
            reader = FileReader()
        elif type == 'ping':
            reader = PingReader()
        else:
            raise ValueError("Invalid resource type: %s" % type)

        data = reader.read(url)

        pos = data.find(search_data)
        if op == 'contains' and pos > -1 or op == 'not-contains' and pos == -1:
            self.failures.append(app)

    def repair(self, app):
        """Repair failed application."""

        if hasattr(app, 'log_file'):
            try:
                fd = open(app.log_file, 'a')
                print >> fd, "%s Watcher has detected a failure in '%s'" \
                    % (datetime.now(), app.name)
                fd.close()
            except Exception, e:
                print "WATCHER ERROR: Unable to open log file %s: %s" % (app.log_file, e)

        if hasattr(app, 'notify_mail'):
            try:
                self.send_mail(app)
            except Exception, e:
                print "WATCHER ERROR: Unable to send message to %s about %s: %s" \
                    % (app.notify_mail, app.name, e)

        output, input = popen2.popen2(app.command)


    def send_mail(self, app):
        """Send e-mail notification to recipients."""
        to = app.notify_mail.split()
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        email_from = self.config.watcher.email_from
        sender = "IDILES Watcher (%s, %s)" % (hostname, ip)
        sender_addr = "%s <%s>" % (sender, email_from)
        subject = "%s: %s failure report" % (sender, app.name)
        msg = """From: %s
To: %s
Subject: %s

Hello,

IDILES Watcher detected application failure:

    Application name: %s
    Date: %s

Command '%s' has been executed to fix the problem.

--
%s
        """ % (sender_addr, ', '.join(to), subject, app.name, 
            datetime.now(), app.command, sender)
        server = smtplib.SMTP(self.config.watcher.smtp_server)
        server.sendmail(sender, to, msg)
        server.quit()


def load_configuration(config_path):
    """Load configuration and return Configuration object."""
    fd = open(config_path)
    config = Configuration(fd)
    return config

def main():
    if len(sys.argv) != 2:
        print "Usage: %s <config>" % sys.argv[0]
        sys.exit()

    config_path = sys.argv[1]
    config = load_configuration(config_path)

    watcher = Watcher(config)
    watcher.run()

if __name__ == '__main__':
    main()

