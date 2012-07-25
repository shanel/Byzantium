# 
# Maybe just make/get objects - return them all and people can sort/choose based on their attrs
# 
# struct-ish?
# 
# NOTE: we may need to change the column order declared in the current SQL files.


import abc
import sqlite3

class State(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def initialize(self, name, prototype):
        return

    @abc.abstractmethod
    def create(self, kind, item):
        return

    @abc.abstractmethod
    def list(self, kind):
        pass

    @abc.abstractmethod
    def replace(self, kind, old_item, new_item):
        pass

class DBBackedState(State):

    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.kind_to_class = {}

    def _create_initialization_fragment_from_prototype(self, prototype):
        """Take an instance of a class and make a table based on its attributes."""
        query = []
        columns = prototype.__dict__.keys()
        columns.sort()
        for column in columns:
            if type(columns(column)) == int:
                query.append('? NUMERIC,')
            else:
                query.append('TEXT,')
        return ' '.join(query)[0:-1], columns

    def _create_query_fragment_from_item(self, item):
        query = []
        values = []
        attrs = item.__dict__.keys()
        attrs.sort()
        for attr in attrs:
            query.append('?')
            values.append(item.__dict__[attr])
        return ','.join(query), values

    def _create_update_query_fragment_from_item(self, item):
        update = []
        values = []
        for k, v in item.__dict__.iteritems():
            update.append('%s=?' % k)
            values.append(v)
        return ' AND '.join(update), values

    def _create_update_setting_fragment_from_item(self, item):
        update = []
        values = []
        for k, v in item.__dict__.iteritems():
            update.append('%s=?' % k)
            values.append(v)
        return ','.join(update), values 

    def initialize(self, name, prototype):
        frag, columns = self._create_initialization_fragment_from_prototype(prototype)
        to_execute = 'CREATE TABLE %s (%s)' % (name, frag)
        cursor = self.connection.cursor()
        cursor.execute(to_execute, columns)
        self.connection.commit()
        self.kind_to_class[name] = prototype.__class__

    def create(self, kind, item):
        frag, values = self._create_query_fragment_from_item(item)
        to_execute = 'INSERT INTO %s VALUES (%s);' % (kind, frag)
        cursor = self.connection.cursor()
        cursor.execute(to_execute, values)
        self.connection.commit()

    def list(self, kind):
        to_execute = 'SELECT * FROM ?'
        cursor = self.connection.cursor()
        cursor.execute(to_execute, kind)
        col_name_list = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        objects = []
        for result in results:
            attrs = {}
            for i, v in result.enumerate():
                attrs[col_name_list[i]] = v
            obj = self.kind_to_class[kind](**attrs)
            objects.append(obj)
        return objects

    def replace(self, kind, old, new):
        query_frag, query_values = self._create_update_query_fragment_from_item(old)
        setting_frag, setting_values = self._create_update_setting_fragment_from_item(new)
        to_execute = 'UPDATE %s SET %s WHERE %s;' % (kind, setting_frag, query_frag)
        cursor = self.connection.cursor()
        cursor.execute(to_execute, setting_values + query_values)
        self.connection.commit()


class NetworkState(DBBackedState):

    def __init__(self):
        super(NetworkState, self).__init__()
        self.initialize_wired_networks()
        self.initialize_wireless_networks()

    def initialize_wired_networks(self):
        self.initialize('wired', WiredNetwork('', '', ''))

    def initialize_wireless_networks(self):
        self.initialize(WirelessNetwork('wireless', '', '', '', '', 0, ''))


class ServiceState(DBBackedState):

    def __init__(self):
        super(ServiceState, self).__init__()
        self.initialize_daemons()
        self.initialize_webaps()
        self.initialize_mesh_networks()

    def initialize_daemons(self):
        self.initialize('daemons', Daemon('', '', 0, '', ''))

    def initialize_webaps(self):
        self.initialize('webapps', WebApp('', ''))

    def initialize_mesh_networks(self):
        self.initialize('meshes', Mesh('', '', ''))


class WiredNetwork(object):
    
    def __init__(self, interface, gateway, enabled):
        self.interface = interface
        self.gateway = gateway
        self.enabled = enabled


class WirelessNetwork(object):

    def __init__(self, client_interface, mesh_interface, gateway, enabled, channel, essid):
        self.client_interface = client_interface
        self.mesh_interface = mesh_interface
        self.gateway = gateway
        self.enabled = enabled
        self.channel = channel
        self.essid = essid


class Mesh(object):

    def __init__(self, interface, protocol, enabled):
        self.interface = interface
        self.protocol = protocol
        self.enabled = enabled


class Daemon(object):

    def __init__(self, name, showtouser, port, initscript, status):
        self.name = name
        self.status = status
        self.showtouser = showtouser
        self.port = port
        self.initscript = initscript


class WebApp(object):

    def __init__(self, name, status):
        self.name = name
        self.status = status