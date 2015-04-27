#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


# This Class is an example of an Arbiter module
# Here for the configuration phase AND running one

try:
    from gevent import socket
    from gevent.pool import Pool
except ImportError:
    import socket
    Pool = None

from IPy import IP
from shinken.basemodule import BaseModule
from shinken.log import logger


properties = {
    'daemons': ['arbiter'],
    'type': 'ip-tag',
    }


# called by the plugin manager to get a module
def get_instance(plugin):
    logger.info("[IP Tag] Get a IPTag module for plugin %s" % plugin.get_name())

    # Catch errors
    ip_range = plugin.ip_range
    prop = plugin.property
    value = plugin.value
    method = getattr(plugin, 'method', 'replace')
    ignore_hosts = getattr(plugin, 'ignore_hosts', None)

    instance = Ip_Tag_Arbiter(plugin, ip_range, prop, value, method, ignore_hosts)
    return instance



# Just print some stuff
class Ip_Tag_Arbiter(BaseModule):
    def __init__(self, mod_conf, ip_range, prop, value, method, ignore_hosts=None):
        BaseModule.__init__(self, mod_conf)
        self.ip_range = IP(ip_range)
        self.property = prop
        self.value = value
        self.method = method
        if ignore_hosts:
            self.ignore_hosts = ignore_hosts.split(', ')
            logger.debug("[IP Tag] Ignoring hosts : %s" % self.ignore_hosts)
        else:
            self.ignore_hosts = []
        self.pool_size = int(getattr(mod_conf, 'pool_size', '1'))


    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[IP Tag] Initialization of the ip range tagger module")


    def hook_early_configuration(self, arb):
        logger.info("[IpTag] in hook late config")

        # Get a pool for gevent jobs
        if Pool:
            pool = Pool(100)
        else:
            pool = None
        
        for h in arb.conf.hosts:
            if not hasattr(h, 'address') and not hasattr(h, 'host_name'):
                continue

            if h.get_name() in self.ignore_hosts:
                logger.debug("[IP Tag] Ignoring host %s" % h.get_name())
                continue

            # The address to resolve
            addr = None

            # By default take the address, if not, take host_name
            if not hasattr(h, 'address'):
                addr = h.host_name
            else:
                addr = h.address

            logger.debug("[IP Tag] Looking for %s" % h.get_name())
            logger.debug("[IP Tag] Address is %s" % str(addr))
            h_ip = None
            try:
                IP(addr)
                # If we reach here, it's it was a real IP :)
                h_ip = addr
            except:
                pass

            if pool:
                pool.spawn(self.job, h, h_ip, addr)
            else:
                self.job(h, h_ip, addr)

        # Now wait for all jobs to finish if need
        if pool:
            pool.join()


    # Main job, will manage eachhost in asyncronous mode thanks to gevent
    def job(self, h, h_ip, addr):
            # Ok, try again with name resolution
            if not h_ip:
                try:
                    h_ip = socket.gethostbyname(addr)
                except Exception, exp:
                    pass

            # Ok, maybe we succeed :)
            logger.debug("[IP Tag] Host ip is: %s" % str(h_ip))
            # If we got an ip that match and the object do not already got
            # the property, tag it!
            if h_ip and h_ip in self.ip_range:
                logger.debug("[IP Tag] Is in the range")
                # 4 cases: append , replace and set
                # append will join with the value if exist (on the END)
                # prepend will join with the value if exist (on the BEGINING)
                # replace will replace it if NOT existing
                # set put the value even if the property exists
                if self.method == 'append':
                    orig_v = getattr(h, self.property, '')
                    if isinstance(orig_v, list):
                      orig_v.append(self.value)
                      setattr(h, self.property, h.properties[self.property].pythonize(orig_v))  
                    else:
                      new_v = ','.join([orig_v, self.value])
                      setattr(h, self.property, h.properties[self.property].pythonize(new_v)) 

                # Same but we put before
                if self.method == 'prepend':
                    orig_v = getattr(h, self.property, '')
                    if isinstance(orig_v, list):
                      orig_v.insert(0,self.value)
                      setattr(h, self.property, h.properties[self.property].pythonize(orig_v))
                    else:
                      new_v = ','.join([self.value, orig_v])
                      setattr(h, self.property, h.properties[self.property].pythonize(new_v))

                if self.method == 'replace':
                    if not hasattr(h, self.property):
                        # Ok, set the value!
                        setattr(h, self.property, h.properties[self.property].pythonize(self.value))

                if self.method == 'set':
                    setattr(h, self.property, h.properties[self.property].pythonize(self.value))
