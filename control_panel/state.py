# 
# Maybe just make/get objects - return them all and people can sort/choose based on their attrs
# 
# struct-ish?
# 


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

    def _create_initialization_fragment_from_prototype(self, prototype):
        """Take an instance of a class and make a table based on its attributes."""
        query = []
        columns = prototype.__dict__.keys()
        columns.sort()
        for column in columns:
            query.append(column)
            if type(columns(column)) == int:
                query.append('NUMERIC,')
            else:
                query.append('TEXT,')
        return ' '.join(query)[0:-1] # snip off the final comma

    def _create_query_fragment_from_item(self, item):
        query = []
        attrs = item.__dict__.keys()
        attrs.sort()
        for attr in attrs:
            query.append(attrs(attr))
        return ','.join(query)

    def initialize(self, name, prototype):
        fragment = self._create_initialization_fragment_from_prototype(prototype)
        cursor = self.connection.cursor()
        cursor.execute('CREATE TABLE %s (%s)' % (name, fragment))
        self.connection.commit()

    def create(self, kind, network):
        pass

    def list(self, kind):
        pass

    def replace(self, kind, old_network, new_network):
        pass

class NetworkState(DBBackedState):

    def __init__(self):
        super(NetworkState, self).__init__()
        self.initialize_wired_networks()
        self.initialize_wireless_networks()
        self.initialize_mesh_networks()

    def initialize_wired_networks(self):
        self.initialize('wired', WiredNetwork('', '', ''))

    def initialize_wireless_networks(self):
        self.initialize(WirelessNetwork('wireless', '', '', '', '', 0, ''))

    def initialize_mesh_networks(self):
        self.initialize('meshes', Mesh('', '', ''))

    def create(self, kind, network):
        pass

    def list(self, kind):
        pass

    def replace(self, kind, old_network, new_network):
        pass

class ServiceState(DBBackedState):

    def __init__(self):
        super(ServiceState, self).__init__()
        self.initialize_daemons()
        self.initialize_webaps()

    def initialize_daemons(self):
        self.initialize('daemons', Daemon('', '', 0, '', ''))

    def initialize_webaps(self):
        self.initialize('webapps', WebApp('', ''))

    def create(self, kind, service):
        pass

    def list(self, kind):
        pass

    def replace(self, kind, old_service, new_service):
        pass

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