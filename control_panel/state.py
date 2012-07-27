# state.py - Abstraction layer for storing different types of state in any kind
#     of backend store

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3
#
# Stuff in here should probably be broken out into a number of files:
#
# State-related stuff can probably stay here
# Model should probably go into something like models/base.py or models/model.py
# Everything that inherits from Model should go in its own file in a models/ directory


import abc
import sqlite3


def Error(Exception):
    pass


def _sanitize(tainted):
    if 'persistance' in tainted:
        tainted.pop('persistance')
    return tainted


def get_matching(pattern, objects):
    """Take a dict and find all objects in list with matching values.
    
    Args:
      pattern: dict, a dict to match off
      objects: list, list of objects to check against

    Returns:
      A list of matching objects

    Raises:
      Error: if the keys of the pattern are not valid object attrs
    """
    contenders = []
    keys = set(pattern.keys())
    vals = set(pattern.values())
    for obj in objects:
        if not set(obj.__dict__.keys()) >= keys:
            raise Error('Bad pattern passed.')
        if set(obj.__dict__.values()) >= vals:
            contenders.append(obj)
    return contenders


class State(object):
    """Metaclass State object."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def initialize(self, name, prototype):
        """Set up any initial state necessary.
        
        Args:
          name: str, the name of the state you are storing
          prototype: instance, a simple instance of the class who's attributes
              make up the state
        """
        return

    @abc.abstractmethod
    def create(self, kind, item):
        """Create a new state entry.
        
        Args:
          kind: str, the kind of state you are creating
          item: instance, the instance who's attributes you are adding
        """
        return

    @abc.abstractmethod
    def list(self, kind):
        """Get a list of state objects.
        
        Args:
          kind: str, the kind of state you are trying to get a listing of
        
        Returns:
          A list of appropriate objects
        """
        pass

    @abc.abstractmethod
    def replace(self, kind, old, new):
        """Replace an old state entry with a new one.
        
        Args:
          kind: str, the kind of state you are trying to update
          old: instance, the instance who's attributes you will be replacing
          new: instance, the instance who's attributes will replace the old attributes
        """
        pass

class DBBackedState(State):
    """A State object who's backend store is an SQLite3 DB.
    
    Attributes:
      db_path: str, the path to the SQLite3 DB file
      connection: sqlite3.connection, a connection object for working with the
          db
      kind_to_class: dict, a mapping of string 'kinds' to the proper classes to
          return them with
    """

    def __init__(self, db_path):
        super(DBBackedState, self).__init__()
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)

    def _execute_and_commit(self, query, values=None):
        cursor = self.connection.cursor()
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        self.connection.commit()

    def _create_initialization_fragment_from_prototype(self, prototype):
        """Take an instance of a class and make a table based on its attributes.
        
        Args:
          prototype: dict, dict of attributes we will
              name columns with
        
        Returns:
          A string with '%s NUMERIC/TEXT' entries to be used and the tuple of
              column names
        """
        query = []
        columns = _sanitize(prototype).keys()
        columns.sort()
        for column in columns:
            if type(prototype[column]) == int:
                query.append('%s NUMERIC,')
            else:
                query.append('%s TEXT,')
        return ' '.join(query)[0:-1], tuple(columns)

    def _create_query_fragment_from_item(self, item):
        """Take an item and build a query fragment from its attributes.
        
        Args:
          item: instance, an instance of a class who's attributes we will query
        
        Returns:
          A string of '?,' entries and a tuple of values to be used in the query
        """
        query = []
        values = []
        attrs = _sanitize(item).keys()
        attrs.sort()
        for attr in attrs:
            query.append('?')
            values.append(item[attr])
        return ','.join(query), tuple(values)

    def _create_update_query_fragment_from_item(self, item):
        """Take an item and build a query template for an update.
        
        Args:
          item: instance, an instance of a class who's attributes we will query
        
        Returns:
          A string of 'attribute=?' entries and a tuple of values to be used in
              the query
        """
        update = []
        values = []
        for k, v in item.iteritems():
            if k not in ('kind', 'persistance'):
                update.append('%s=?' % k)
                values.append(v)
        return ' AND '.join(update), tuple(values)

    def _create_update_setting_fragment_from_item(self, item):
        """Take an item and build a setting template for an update.
        
        Args:
          item: dict, a dict who's attributes we will use
        
        Returns:
          A string of 'attribute=?' entries and a tuple of values to be used in
              the setting command
        """
        update = []
        values = []
        for k, v in item.iteritems():
            if k not in ('kind', 'persistance'):
                update.append('%s=?' % k)
                values.append(v)
        return ','.join(update), tuple(values )

    def initialize(self, prototype):
        """Create a table based on a prototype dict.
        
        Args:
          prototype: dict, a dict to base column names off
        """
        kind = prototype.pop('kind')
        frag, columns = self._create_initialization_fragment_from_prototype(prototype)
        to_execute = 'CREATE TABLE IF NOT EXISTS %s (%s);' % (kind, frag % columns)
        self._execute_and_commit(to_execute)

    def create(self, item):
        """Insert or replace an entry in the backend.
        
        Args:
          item: dict, a dict who's attributes we'll insert/replace
        """
        kind = item.pop('kind')
        frag, values = self._create_query_fragment_from_item(item)
        to_execute = 'INSERT OR REPLACE INTO %s VALUES (%s);' % (kind, frag)
        self._execute_and_commit(to_execute, values)

    def list(self, kind, klass):
        """List all entries for a given kind, returning them as klass objects.
        
        Args:
          kind: str, the kind of entry we are looking for
          klass: class, the class type we should build out of each result
          
         Returns:
           a list of klass objects based on results from the backend call
        """
        to_execute = 'SELECT * FROM %s;' % kind
        cursor = self.connection.cursor()
        cursor.execute(to_execute)
        # We need to know what the attribute names are of the class we are
        # building
        col_name_list = [desc[0] for desc in cursor.description()]
        # Not the most efficient way of doing things, but the db will always
        # be small enough that it won't matter
        results = cursor.fetchall()
        objects = []
        for result in results:
            attrs = {}
            for i, v in enumerate(result):
                attrs[col_name_list[i]] = v
            obj = klass(**attrs)
            objects.append(obj)
        return objects

    def replace(self, old, new):
        """Replace an old entry with a new one.
        
        Args:
          old: dict, a dict of the old data (what we search for)
          new: dict, a dict of the replacement data
        """
        kind = old.pop('kind')
        query_frag, query_values = self._create_update_query_fragment_from_item(old)
        setting_frag, setting_values = self._create_update_setting_fragment_from_item(new)
        # Again, not the most efficient, but it works in all cases and doesn't
        # need any fancy logic
        to_execute = 'UPDATE OR REPLACE %s SET %s WHERE %s;' % (kind, setting_frag, query_frag)
        self._execute_and_commit(to_execute, setting_values + query_values)


class NetworkState(DBBackedState):

    def __init__(self, db_path):
        super(NetworkState, self).__init__(db_path)
        wired = {'interface': '', 'gateway': '', 'enabled': '', 'kind': 'wired'}
        wireless = {'client_interface': '', 'mesh_interface': '',
                    'gateway': '', 'enabled': '', 'channel': 0, 'essid': '',
                    'kind': 'wireless'}
        self.initialize(wired)
        self.initialize(wireless)


class MeshState(DBBackedState):
    
    def __init__(self, db_path):
        super(MeshState, self).__init__(db_path)
        meshes = {'interface': '', 'protocol': '', 'enabled': '', 'kind': 'meshes'}
        self.initialize(meshes)


class ServiceState(DBBackedState):

    def __init__(self, db_path):
        super(ServiceState, self).__init__(db_path)
        daemons = {'name': '', 'showtouser': '', 'port': 0, 'initscript': '', 'status': '', 'kind': 'daemons'}
        webapps = {'name': '', 'status': '', 'kind': 'webapps'}
        self.initialize(daemons)
        self.initialize(webapps)    


class Model(object):
    
    def __init__(self, persistance, testing=False):
        print "Dict as we come into Model: %s" % self.__dict__
        self.persistance = persistance
        print "Dict after resetting self.persistance: %s" % self.__dict__
        if not testing:
            self.persistance.create(self.__dict__)
            print "Dict after create call: %s" % self.__dict__
    
    def list(self):
        return self.persistance.list(self.kind, self.__class__)
    
    def replace(self, **kwagrs):
        old = self.__dict__.copy()
        for k, v in kwargs:
            if k not in ('kind', 'persistance'):
                setattr(self, k, v)
        self.persistance.replace(self.__class__(old), self)
                
                
class WiredNetwork(Model):
    
    def __init__(self, interface, gateway, enabled, persistance, testing=False):
        self.interface = interface
        self.gateway = gateway
        self.enabled = enabled
        self.kind = 'wired'
        self.persistance = persistance
        super(WiredNetwork, self).__init__(persistance, testing)
        
    # probably going to want something like the activate/set_ip/tcip functionality here


class WirelessNetwork(Model):

    def __init__(self, client_interface, mesh_interface, gateway, enabled, channel, essid, persistance, testing=False):
        self.client_interface = client_interface
        self.mesh_interface = mesh_interface
        self.gateway = gateway
        self.enabled = enabled
        self.channel = channel
        self.essid = essid
        self.kind = 'wireless'
        self.persistance = persistance
        super(WirelessNetwork, self).__init__(persistance, testing)
        
    # probably going to want something like the activate/set_ip/tcip functionality here


class Mesh(Model):

    def __init__(self, interface, protocol, enabled, persistance, testing=False):
        self.interface = interface
        self.protocol = protocol
        self.enabled = enabled
        self.kind = 'meshes'
        self.persistance = persistance
        super(Mesh, self).__init__(persistance, testing)
    
    # probably going to want some method to update_babeld in here


class Daemon(Model):

    def __init__(self, name, showtouser, port, initscript, status, persistance, testing=False):
        self.name = name
        self.status = status
        self.showtouser = showtouser
        self.port = port
        self.initscript = initscript
        self.kind = 'daemons'
        self.persistance = persistance
        super(Daemon, self).__init__(persistance, testing)
        
    # probably going to want something like toggle_service in here


class WebApp(Model):

    def __init__(self, name, status, persistance, testing=False):
        self.name = name
        self.status = status
        self.kind = 'webapps'
        self.persistance = persistance
        print "__dict__ before super: %s" % self.__dict__
        super(WebApp, self).__init__(persistance, testing)
        
    # probably going to want something like toggle_service in here