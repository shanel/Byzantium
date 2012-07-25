# 
# Maybe just make/get objects - return them all and people can sort/choose based on their attrs
# 
# struct-ish?
# 


import abc

class State(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def initialize(self, name, prototype):
        return

    @abc.abstractmethod
    def create(self, item):
        return

    @abc.abstractmethod
    def list(self, kind):
        pass

    @abc.abstractmethod
    def replace(self, old_item, new_item):
        pass

class DBBackedState(State):

    def _create_query_fragment_from_prototype(self, prototype):
        query = []
        for k, v in prototype.__dict__.iteritems():
            query.append(k)
            if type(v) == int:
                query.append('NUMERIC,')
            else:
                query.append('TEXT,')
        return ' '.join(query)

    def initialize(self, name, prototype):
        pass

    def create(self, network):
        pass

    def list(self, kind):
        pass

    def replace(self, old_network, new_network):
        pass

class NetworkState(DBBackedState):

    def __init__(self):
        super(NetworkState, self).__init__()
        self.initialize_wired_networks()
        self.initialize_wireless_networks()
        self.initialize_mesh_networks()

    def initialize_wired_networks(self):
        self.initialize('wired', WiredNetwork('', ''. ''))

    def initialize_wireless_networks(self):
        self.initialize(WirelessNetwork('wireless', '', '', '', '', 0, ''))

    def initialize_mesh_networks(self):
        self.initialize('meshes', Mesh('', '', ''))

    def create(self, network):
        pass

    def list(self, kind):
        pass

    def replace(self, old_network, new_network):
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

    def create(self, service):
        pass

    def list(self, kind):
        pass

    def replace(self, old_service, new_service):
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

    def __init__(self, name, showtouser, port, initiscript, status):
        self.name = name
        self.status = status
        self.showtouser = showtouser
        self.port = port
        self.initscript = initscript

class WebApp(object):

    def __init__(self, name, status):
        self.name = name
        self.status = status