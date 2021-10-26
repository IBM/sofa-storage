"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
from os import listdir, symlink, unlink, mkdir, rmdir
from os.path import isdir, isfile, islink, join, realpath

from .config import config


class Component():
    def __init__(self, path):
        self._path = path

    def getAttr(self, name):
        p = realpath(join(self._path, name))
        if isfile(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = f.read()[:-1]
                try:
                    return int(data)
                except ValueError:
                    return data
        else:
            return None

    def setAttr(self, name, val):
        p = realpath(join(self._path, name))
        if isfile(p):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(str(val))
        else:
            raise RuntimeError

    def delete(self):
        p = self._path
        if isdir(p):
            rmdir(p)


class Subsystem(Component):
    def __init__(self, name):
        super().__init__('/sys/kernel/config/nvmet/subsystems/' + name + '/')
        self.name = name

    @property
    def attr_allow_any_host(self):
        return self.getAttr('attr_allow_any_host')

    @attr_allow_any_host.setter
    def attr_allow_any_host(self, val):
        self.setAttr('attr_allow_any_host', val)

    def namespaces(self):
        ns = []
        for i in listdir(realpath(join(self._path, 'namespaces'))):
            ns.append(Namespace(self.name, i))
        return ns

    def dump(self):
        print('Subsystem: ' + self.name
              + '  attr_allow_any_host = ' + str(self.attr_allow_any_host))

    def createNamespace(self, namespace_name):
        p = realpath(join(self._path, 'namespaces', namespace_name))
        if not isdir(p):
            mkdir(p)
        return Namespace(self.name, namespace_name)


class Namespace(Component):
    def __init__(self, subsysname, name):
        super().__init__('/sys/kernel/config/nvmet/subsystems/' + subsysname + '/namespaces/' + name + '/')
        self.subsysname = subsysname
        self.name = name

    @property
    def enable(self):
        return self.getAttr('enable')

    @enable.setter
    def enable(self, val):
        return self.setAttr('enable', val)

    @property
    def device_path(self):
        return self.getAttr('device_path')

    @device_path.setter
    def device_path(self, val):
        return self.setAttr('device_path', val)

    def device_nguid(self):
        return self.getAttr('device_nguid')

    def device_uuid(self):
        return self.getAttr('device_uuid')

    def dump(self):
        print('Namespace: ' + self.name
              + '  enable = ' + str(self.enable)
              + '  device_path = ' + str(self.device_path)
              + '  device_nguid = ' + str(self.device_nguid())
              + '  device_uuid = ' + str(self.device_uuid()))


class Port(Component):
    def __init__(self, name):
        super().__init__('/sys/kernel/config/nvmet/ports/' + name + '/')
        self.name = name

    @property
    def addr_adrfam(self):
        return self.getAttr('addr_adrfam')  # ipv4

    @addr_adrfam.setter
    def addr_adrfam(self, val):
        if val in ['ipv4', 'ipv6']:
            self.setAttr('addr_adrfam', val)
        else:
            print('Port: Failed setting addr_adrfam. Must be ipv4 or ipv6.')

    @property
    def addr_traddr(self):
        return self.getAttr('addr_traddr')  # 10.100.x.x

    @addr_traddr.setter
    def addr_traddr(self, val):
        self.setAttr('addr_traddr', val)

    @property
    def addr_trsvcid(self):
        return self.getAttr('addr_trsvcid')  # 4420

    @addr_trsvcid.setter
    def addr_trsvcid(self, val):
        if 4420 <= val < 4520:  # TODO:
            self.setAttr('addr_trsvcid', str(val))
        else:
            print('Port: Failed setting addr_trscid. Out of range.')

    @property
    def addr_trtype(self):
        return self.getAttr('addr_trtype')  # rdma

    @addr_trtype.setter
    def addr_trtype(self, val):
        if val in ['rdma', 'tcp']:
            self.setAttr('addr_trtype', val)
        else:
            print('Port: Failed setting addr_trtype. Must be rdma.')

    @property
    def subsystems(self):
        subsystem_list = []
        for i in listdir(realpath(join(self._path, 'subsystems'))):
            subsystem_list.append(Subsystem(i))
        return subsystem_list

    def linkSubsystem(self, subsys):
        p = join(self._path, 'subsystems', subsys.name)
        if not islink(p):
            symlink(subsys._path, p, target_is_directory=True)

    def removeSubsystem(self, subsys):
        p = join(self._path, 'subsystems', subsys.name)
        if islink(p):
            unlink(p)

    def dump(self):
        print('Port: ' + self.name
              + '  addr_adrfam = ' + str(self.addr_adrfam)
              + '  addr_traddr = ' + str(self.addr_traddr)
              + '  addr_trsvcid = ' + str(self.addr_trsvcid)
              + '  addr_trtype = ' + str(self.addr_trtype))


class Nvmet(Component):
    def __init__(self):
        super().__init__('/sys/kernel/config/nvmet/')

    @property
    def ports(self):
        port_list = []
        for i in listdir(realpath(join(self._path, 'ports'))):
            port_list.append(Port(i))
        return port_list

    @property
    def subsystems(self):
        subsystem_list = []
        for i in listdir(realpath(join(self._path, 'subsystems'))):
            subsystem_list.append(Subsystem(i))
        return subsystem_list

    def createSubsystem(self, subsys_name):
        p = realpath(join(self._path, 'subsystems', subsys_name))
        if not isdir(p):
            mkdir(p)
        return Subsystem(subsys_name)

    def createPort(self, port_name):
        p = realpath(join(self._path, 'ports', port_name))
        if not isdir(p):
            mkdir(p)
        return Port(port_name)

    def getPortBySubsystem(self, subsys_name):
        for po in self.ports:
            for s in po.subsystems:
                if s.name == subsys_name:
                    return po
        return None


def publishVolume(volume_id):
    nvmet = Nvmet()
    ts = nvmet.createSubsystem(volume_id)
    ts.attr_allow_any_host = 1
    tn = ts.createNamespace(config['NAMESPACE'])
    tn.device_path = '/dev/' + config['VG'] + '/' + volume_id
    tn.enable = 1

    port = 1
    while str(port) in [port.name for port in nvmet.ports]:
        port = port + 1

    tp = nvmet.createPort(str(port))
    tp.addr_adrfam = 'ipv4'
    tp.addr_traddr = config['NVMET_TRADDR']
    tp.addr_trsvcid = 4420 + port - 1
    tp.addr_trtype = config['TRANSPORT_TYPE']

    tp.linkSubsystem(ts)

    return {
        'port': tp.addr_trsvcid
    }


def unpublishVolume(volume_id):
    nvmet = Nvmet()
    for po in nvmet.ports:
        for s in po.subsystems:
            if s.name == volume_id:
                po.removeSubsystem(s)
                po.delete()
                break
    ns = Namespace(volume_id, config['NAMESPACE'])
    ss = Subsystem(volume_id)
    ns.delete()
    ss.delete()
