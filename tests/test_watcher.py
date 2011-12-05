#!/usr/bin/env python
#
# IDILES Watcher
# Copyright (c) 2007 IDILES SYSTEMS
#
"""
Tests for watcher.
"""

def test_Configuration():
    """Test for Configuration class.

        >>> from cStringIO import StringIO
        >>> from watcher import Configuration

    Make Configuration object with a simple configuration data.

        >>> config_data = '''
        ... application:
        ...     name = sample1
        ...     trigger = url http://localhost:8080 contains: error
        ...     log-file = /tmp/sample.log
        ...     notify-mail = bugs@idiles.com
        ...
        ... application:
        ...     name = sample2
        ...     trigger = file /tmp/app not-contains: OK
        ...
        ... application:
        ...     name = sample3
        ...     trigger = file /tmp/app not-contains: XXX
        ...
        ... application:
        ...     name = sample4
        ...     trigger = ping localhost not-contains: OK
        ...
        ... watcher:
        ...     smtp-server = localhost
        ... '''
        >>> fd = StringIO(config_data)
        >>> config = Configuration(fd)
        
    Check if data has been correctly parsed.

        >>> len(config.applications)
        4
        >>> app = config.applications[0]
        >>> app.name
        'sample1'
        
    Hyphens in keys should be replaces by underscores.

        >>> app.log_file
        '/tmp/sample.log'
        >>> app.notify_mail
        'bugs@idiles.com'
        >>> app.trigger
        'url http://localhost:8080 contains: error'

    Applications names must be unique. If duplicates are found, only the first
    application is saved.

        >>> app2 = config.applications[1]
        >>> 'OK' in app2.trigger
        True

        >>> app3 = config.applications[2]
        >>> 'XXX' in app3.trigger
        True

        >>> app4 = config.applications[3]
        >>> 'OK' in app4.trigger
        True

    Watcher configuration should be also loaded correctly.
        
        >>> config.watcher.smtp_server
        'localhost'
    """

def test_URLReader():
    """Test URLReader class.

        >>> from watcher import URLReader
        >>> reader = URLReader()
        >>> 'Connection refused' in reader.read("http://localhost:777")
        True
    """

def test_PingReader():
    """Test PingReader class.

        >>> from watcher import PingReader
        >>> import os
        >>> ping = PingReader()
        >>> os.environ['watcher-env'] = 'development'
        >>> ping.read('localhost')
        'OK'
    """

def test_FileReader():
    """Test FileReader class.

        >>> import os
        >>> from watcher import FileReader
        >>> reader = FileReader()
        >>> file_path = '/tmp/watcher-test'
        >>> fd = open(file_path, 'w')
        >>> print >> fd, 'dontstop'
        >>> fd.close()
        >>> 'dontstop' in reader.read(file_path)
        True
        >>> os.remove(file_path)
    """

def test_Watcher():
    """Test Watcher.

        >>> from cStringIO import StringIO
        >>> import os
        >>> from watcher import Configuration, Watcher

        >>> os.environ['watcher-env'] = 'development'

    Make a simple configuration at first.

        >>> config_data = '''
        ... application:
        ...     name = sample1
        ...     trigger = url http://localhost:777 contains: refused
        ...     command = /usr/bin/app restart
        ...     log-file = /tmp/app.log
        ...     notify-mail = bugs@idiles.com
        ...
        ... application:
        ...     name = sample2
        ...     trigger = url http://localhost:777 contains: notfound
        ...     command = /usr/bin/app2 restart
        ...     log-file = /tmp/app2.log
        ...
        ... application:
        ...     name = sample3
        ...     trigger = file /tmp/x not-contains: something
        ...     command = /usr/bin/app3restart
        ...     logfile = /tmp/app3.log
        ...
        ... application:
        ...     name = sample4
        ...     trigger = ping invalid.idiles.com not-contains: FAILURE
        ...     command = /usr/bin/app4restart
        ...     logfile = /tmp/app4.log
        ...
        ... watcher:
        ...     smtp-server = localhost
        ... '''
        >>> fd = StringIO(config_data)
        >>> config = Configuration(fd)
        
    Now make a watcher and run it.

        >>> watcher = Watcher(config)
        >>> watcher.run(repair=False)

    Print out list of commands to be executed on the system.

        >>> [app.name for app in watcher.failures]
        ['sample1', 'sample3', 'sample4']
    """

