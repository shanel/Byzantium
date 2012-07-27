# state.py - Abstraction layer for storing different types of state in any kind
#     of backend store

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3


import abc
import sqlite3

def _sanitize(tainted):
    if 'persistance' in tainted:
        tainted.pop('persistance')
    return tainted


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
        columns = _sanitize(prototype.keys())
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
        attrs = _sanitize(item.keys())
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
        cursor = self.connection.cursor()
        cursor.execute(to_execute)
        self.connection.commit()

    def create(self, item):
        """Insert or replace an entry in the backend.
        
        Args:
          item: dict, a dict who's attributes we'll insert/replace
        """
        kind = prototype.pop('kind')
        frag, values = self._create_query_fragment_from_item(item)
        to_execute = 'INSERT OR REPLACE INTO %s VALUES (%s);' % (kind, frag)
        cursor = self.connection.cursor()
        cursor.execute(to_execute, values)
        self.connection.commit()

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
        col_name_list = [desc[0] for desc in cursor.description]
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
        query_frag, query_values = self._create_update_query_fragment_from_item(old)
        setting_frag, setting_values = self._create_update_setting_fragment_from_item(new)
        # Again, not the most efficient, but it works in all cases and doesn't
        # need any fancy logic
        to_execute = 'UPDATE OR REPLACE %s SET %s WHERE %s;' % (old.kind, setting_frag, query_frag)
        cursor = self.connection.cursor()
        cursor.execute(to_execute, setting_values + query_values)
        self.connection.commit()


class NetworkState(DBBackedState):

    def __init__(self, db_path):
        super(NetworkState, self).__init__(db_path)
        self.initialize(WiredNetwork('', '', ''))
        self.initialize(WirelessNetwork('', '', '', '', 0, ''))


class NetworkState(DBBackedState):

    def __init__(self, db_path):
        super(NetworkState, self).__init__(db_path)
        self.initialize(Daemon('', '', 0, '', ''))
        self.initialize(WebApp('', ''))
        self.initialize(Mesh('', '', ''))


class Model(object):
    
    def __init__(self, kind, persistance, testing=False):
        self.kind = kind
        self.persistance = persistance
        if not testing:
            self.persistance.create(self.__dict__)
    
    def list(self):
        return self.persistance.list(self.kind, self.__class__)
    
    def replace(self, **kwagrs):
        old = self.__dict__.copy()
        for k, v in kwargs:
            if k not in ('kind', 'persistance'):
                setattr(self, k, v)
        self.persistance.replace(self.__class__(old), self)
                
                
class WiredNetwork(Model):
    
    def __init__(self, interface, gateway, enabled, persistance):
        self.interface = interface
        self.gateway = gateway
        self.enabled = enabled
        super(WiredNetwork, self).__init__('wired', persistance)


class WirelessNetwork(Model):

    def __init__(self, client_interface, mesh_interface, gateway, enabled, channel, essid, persistance):
        self.client_interface = client_interface
        self.mesh_interface = mesh_interface
        self.gateway = gateway
        self.enabled = enabled
        self.channel = channel
        self.essid = essid
        super(WirelessNetwork, self).__init__('wireless', persistance)


class Mesh(Model):

    def __init__(self, interface, protocol, enabled, persistance):
        self.interface = interface
        self.protocol = protocol
        self.enabled = enabled
        super(Mesh, self).__init__('meshes', persistance)


class Daemon(Model):

    def __init__(self, name, showtouser, port, initscript, status, persistance):
        self.name = name
        self.status = status
        self.showtouser = showtouser
        self.port = port
        self.initscript = initscript
        super(Daemon, self).__init__('daemons', persistance)


class WebApp(Model):

    def __init__(self, name, status, persistance):
        self.name = name
        self.status = status
        super(WebApp, self).__init__('webapps', persistance)