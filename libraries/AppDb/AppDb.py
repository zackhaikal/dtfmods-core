#!/usr/bin/env python
# Copyright 2013-2014 Jake Valletta (@jake_valletta)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# API for working with applications

import sqlite3
from os.path import isfile, isdir
from pydtf import dtflog as log
from pydtf import dtfglobals
from pydtf import dtfconfig
import base64

_TAG = "AppDb"

APP_DB_NAME = "sysapps.db"

AOSP_PACKAGE_PREFIX="appdb-aosp-"

PROTECTION_NORMAL = 0
PROTECTION_DANGEROUS = 1
PROTECTION_SIGNATURE = 2
PROTECTION_SIGNATURE_OR_SYSTEM = 3

PROTECTION_FLAG_SYSTEM = 0x10
PROTECTION_FLAG_DEVELOPMENT = 0x20

PROTECTION_MASK_BASE = 0x0f

# Check if we can the api data
def isAOSPDataInstalled():

    sdk = dtfconfig.get_prop("Info", "sdk")
    dtf_packages = dtfglobal.DTF_PACKAGES

    if isdir(dtf_packages + '/' + AOSP_PACKAGE_PREFIX + sdk):
        return True
    else:
        return False

# Exceptions
class AppDbException(Exception):

    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        Exception.__init__(self, message)


# Application Class
class Application(object):

    _id = 0
    project_name = ""
    min_sdk_version = 0
    target_sdk_version = 0
    permisison = None
    debuggable = None
    has_native = 0

    def __init__(self, project_name, min_sdk_version, target_sdk_version, debuggable, permission, has_native, id=None):

        self.project_name = project_name

        if debuggable == None:
            self.debuggable = None
        elif debuggable == True:
            self.debuggable = 1
        elif debuggable == False:
            self.debuggable = 0

        self.min_sdk_version = min_sdk_version
        self.target_sdk_version = target_sdk_version
        self.permission = permission
        self.has_native = has_native
 
        if id is not None:
            self._id = id

    def setDebuggable(self, value):
        self.debuggable = value

    def getDebuggable(self):
        if self.debuggable == None:
            return None
        elif self.debuggable == 0:
            return False
        elif self.debuggable == 1:
            return True

# Component Object Classes
class PermissionGroup(object):

    _id = 0
    application_id = 0
    name = ""

    def __init__(self, name, application_id, id=None):

        self.name = name
        self.application_id = application_id

        if id is not None:
            self._id = id

class Permission(object):

    _id = 0
    application_id = 0
    name = ""
    permission_group = None
    protection_level = ""

    def __init__(self, name, protection_level, permission_group, application_id, id=None):
        self.name = name
        self.protection_level = protection_level
        self.permission_group = permission_group
        self.application_id = application_id

        if id is not None:
            self._id = id

    def __repr__(self):
        return "%s [%s]" % (self.name, self.protection_level)


class Activity(object):

    _id = 0
    application_id = 0
    name = ""
    permission = None
    enabled = None
    exported = None
    intent_data = ""

    def __init__(self, name, enabled, exported, permission, intent_data, application_id, id=None):

        # EDIT : Constructor expects True/False/NoneType as exported and enabled.
        # Note - Constrctor expects intent_data as a string.
        self.name = name
        self.permission = permission

        self.exported = exported
        self.enabled = enabled

        # A object should store the String representaiton of the intent_data.
        self.intent_data = intent_data
        self.application_id = application_id
 
        if id is not None:
            self._id = id

class Service(object):

    _id = 0
    application_id = 0
    name = ""
    permission = None
    enabled = None
    exported = None
    intent_data = ""

    def __init__(self, name, enabled, exported, permission, intent_data, application_id, id=None):

        # EDIT : Constructor expects True/False/NoneType as exported and enabled.
        # Note - Constrctor expects intent_data as a string.
        self.name = name
        self.permission = permission

        self.exported = exported
        self.enabled = enabled

        self.intent_data = intent_data
        self.application_id = application_id

        if id is not None:
            self._id = id

class Provider(object):

    _id = 0
    application_id = 0
    name = ""
    authorities = None
    enabled = None
    exported = None
    permission = None
    read_permission = None
    write_permission = None
    grant_uri_permissions = ""
    path_permission_data = ""
    grant_uri_permission_data = ""

    def __init__(self, name, authorities, enabled, exported, grant_uri_permissions, 
                 grant_uri_permission_data, path_permission_data, permission, read_permission, 
                 write_permission, application_id, id=None):

        # EDIT : Constructor expects True/False/NoneType as exported and enabled.
        # Note - Constructor expects 0/1/NoneType as grantUriPermissions
        # Note - Constrctor expects path_permission_data  as a string.
        self.name = name
        self.authorities = authorities

        self.exported = exported
        self.enabled = enabled

        if grant_uri_permissions == 0:
            self.grant_uri_permissions = False
        elif grant_uri_permissions == 1:
            self.grant_uri_permissions = True
        else:
            self.grant_uri_permissions = None

        self.permission = permission
        self.read_permission = read_permission
        self.write_permission = write_permission
        self.path_permission_data = path_permission_data
        self.grant_uri_permission_data = grant_uri_permission_data
        self.application_id = application_id

        if id is not None:
            self._id = id

class Receiver(object):

    _id = 0
    application_id = 0
    name = ""
    permission = None
    enabled = None
    exported = None
    intent_data = ""

    def __init__(self, name, enabled, exported, permission, intent_data, application_id, id=None):

        # EDIT : Constructor expects True/False/NoneType as exported and enabled.
        # Note - Constrctor expects intent_data as a string.
        # Note - Construtor expects 0/1/NoneType as exported/enabled
        self.name = name
        self.permission = permission

        self.exported = exported
        self.enabled = enabled

        self.intent_data = intent_data
        self.application_id = application_id

        if id is not None:
            self._id = id

# End Component Class Declarations


#### Class AppDb ########################################
class AppDb(object):

    db_path = None
    app_db = None

    def __init__(self, db_path, safe=False):

        # Make sure the DB exists, don't create it.
        if safe and not isfile(db_path): raise AppDbException("Database file not found : %s!" % db_path)

        self.db_path = db_path
        self.app_db = sqlite3.connect(db_path)     


    def commit(self):
        return self.app_db.commit()

#### Table Creation Methods ############################
    def createTables(self):

        if (not self.createPermissionsTable()):
            log.e(_TAG, "failed to create Permissions Table!")
            return -1

        if (not self.createPermissionGroupsTable()):
            log.e(_TAG, "failed to create Permission Groups Table!")
            return -1

        if (not self.createActivitiesTable()):
            log.e(_TAG, "failed to create Activities Table!")
            return -1

        if (not self.createServicesTable()):
            log.e(_TAG, "failed to create Services Table!")
            return -1

        if (not self.createProvidersTable()):
            log.e(_TAG, "failed to create Providers Table!")
            return -1

        if (not self.createReceiversTable()):
            log.e(_TAG, "failed to create Receivers Table!")
            return -1

        if (not self.createAppUsesPermissionsTable()):
            log.e(_TAG, "failed to create App Uses Permissions Table!")
            return -1
 
        if (not self.createSharedLibrariesTable()):
            log.e(_TAG, "failed to create Shared libraries Table!")
            return -1

        return 0

    def createPermissionGroupsTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS permission_groups'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id)'
               ')')

        return self.app_db.execute(sql)

    def createPermissionsTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS permissions'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'permission_group INTEGER,'
               'protection_level TEXT,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id),'
               'FOREIGN KEY(permission_group) REFERENCES permission_groups(id)'
               ')')

        rtn = self.app_db.execute(sql)
        if rtn != 0:
            return rtn   

        # TODO: This is hacky.
        sql = ('INSERT INTO permissions(id, name, permission_group, protection_level, application_id) '
               "VALUES (0, 'None', 0, 'None',0)")

        return self.app_db.execute(sql)

    def createActivitiesTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS activities'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'permission INTEGER,'
               'exported TEXT,'
               'enabled TEXT,'
               'intent_data TEXT,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id),'
               'FOREIGN KEY(permission) REFERENCES permissions(id)'
               ')')

        return self.app_db.execute(sql)

    def createServicesTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS services'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'permission INTEGER,'
               'exported TEXT,'
               'enabled TEXT,'
               'intent_data TEXT,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id),'
               'FOREIGN KEY(permission) REFERENCES permissions(id)'
               ')')

        return self.app_db.execute(sql)

    def createProvidersTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS providers'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'authorities TEXT NOT NULL,'
               'name TEXT NOT NULL,'
               'permission INTEGER,'
               'read_permission INTEGER,'
               'write_permission INTEGER,'
               'exported TEXT,'
               'enabled TEXT,'
               'grant_uri_permissions INTEGER,'
               'path_permission_data TEXT,'
               'grant_uri_permission_data TEXT,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id),'
               'FOREIGN KEY(permission) REFERENCES permissions(id),'
               'FOREIGN KEY(read_permission) REFERENCES permissions(id),'
               'FOREIGN KEY(write_permission) REFERENCES permissions(id)'
               ')')

        return self.app_db.execute(sql)

    def createReceiversTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS receivers'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'permission INTEGER,'
               'exported TEXT,'
               'enabled TEXT,'
               'intent_data TEXT,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id)'
               ')')

        return self.app_db.execute(sql)

    def createAppUsesPermissionsTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS app_uses_permissions'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'application_id INTEGER,'
               'permission_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id),'
               'FOREIGN KEY(permission_id) REFERENCES permissions(id)'
               ')')

        return self.app_db.execute(sql)

    def createSharedLibrariesTable(self):

        sql = ('CREATE TABLE IF NOT EXISTS shared_libraries'
               '('
               'id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'name TEXT NOT NULL,'
               'application_id INTEGER,'
               'FOREIGN KEY(application_id) REFERENCES apps(id)'
               ')')

        return self.app_db.execute(sql)
    # End Table Creation

#### Table Deletion Methods ############################
    def dropTables(self):

        global app_db

        self.app_db.execute('''DROP TABLE IF EXISTS shared_libraries''')
        self.app_db.execute('''DROP TABLE IF EXISTS app_uses_permissions''')
        self.app_db.execute('''DROP TABLE IF EXISTS receivers''')
        self.app_db.execute('''DROP TABLE IF EXISTS providers''')
        self.app_db.execute('''DROP TABLE IF EXISTS services''')
        self.app_db.execute('''DROP TABLE IF EXISTS activities''')
        self.app_db.execute('''DROP TABLE IF EXISTS permission_groups''')
        self.app_db.execute('''DROP TABLE IF EXISTS permissions''')

    # End Table Deletion

#### Table Modification Methods ############################
    def addPermissionGroup(self, permission_group):

        name = permission_group.name
        application_id = permission_group.application_id

        sql = ('INSERT INTO permission_groups(name, application_id) '
               "VALUES ('%s', %i)" % (name, application_id))

        return self.app_db.execute(sql)


    def addPermission(self, permission):

        name = permission.name
        protection_level = permission.protection_level
        permission_group = permission.permission_group
        application_id = permission.application_id

        print permission.permission_group

        if permission_group is None:
            permission_group_id = 0
        else:
            permission_group_id = permission_group._id


        sql = ('INSERT INTO permissions(name, permission_group, protection_level, application_id) '
               "VALUES('%s',%i,'%s',%i)" % (name, permission_group_id, protection_level, application_id))

        return self.app_db.execute(sql)

    def addAppUsesPermission(self, application_id, permission_id):

        sql = ('INSERT INTO app_uses_permissions(application_id, permission_id) '
               "VALUES (%i,%i)" % (application_id, permission_id))

        return self.app_db.execute(sql)

    def addActivity(self, activity):

        name = activity.name
        enabled = activity.enabled
        exported = activity.exported
        intent_data = base64.b64encode(activity.intent_data)
        application_id = activity.application_id

        permission = activity.permission

        if permission != None:
            permission_id = permission._id
        else:
            permission_id = 0
 
        sql = ('INSERT INTO activities(name, permission, exported, enabled, intent_data, application_id) '
               "VALUES ('%s',%i,'%s','%s','%s',%i)"  % (name, permission_id, exported, enabled, 
                                                        intent_data, application_id))

        return self.app_db.execute(sql)

    def addService(self, service):

        name = service.name
        enabled = service.enabled
        exported = service.exported
        intent_data = base64.b64encode(service.intent_data)
        application_id = service.application_id

        permission = service.permission

        if permission != None:
            permission_id = permission._id
        else:
            permission_id = 0

        sql = ('INSERT INTO services(name, permission, exported, enabled, intent_data, application_id) '
               "VALUES ('%s',%i,'%s','%s','%s',%i)"  % (name, permission_id, exported, enabled,
                                                        intent_data, application_id))

        return self.app_db.execute(sql)


    def addProvider(self, provider):

        name = provider.name
        authorities = ';'.join(provider.authorities)
        enabled = provider.enabled
        exported = provider.exported
        grant_uri_permissions = provider.grant_uri_permissions       
        grant_uri_permission_data = base64.b64encode(provider.grant_uri_permission_data)
        path_permission_data = base64.b64encode(provider.path_permission_data)

        if grant_uri_permissions == True:
            grant_uri_permissions = 1
        elif grant_uri_permissions == False:
            grant_uri_permissions = 0

        application_id = provider.application_id

        permission = provider.permission
        read_permission = provider.read_permission
        write_permission = provider.write_permission

        if permission != None:
            permission_id = permission._id
        else:
            permission_id = 0

        if read_permission != None:
            read_permission_id = read_permission._id
        else:
            read_permission_id = 0

        if write_permission != None:
            write_permission_id = write_permission._id
        else:
            write_permission_id = 0

        sql = ('INSERT INTO providers'
               '(name, authorities, permission, read_permission, write_permission, exported, enabled, '
               'grant_uri_permissions, grant_uri_permission_data, path_permission_data, application_id) '
               "VALUES ('%s','%s',%i,%i,%i,'%s','%s','%s','%s','%s',%i)"
                % (name, authorities, permission_id, read_permission_id, write_permission_id, exported, enabled, 
                   grant_uri_permissions, grant_uri_permission_data, path_permission_data, application_id))

        return self.app_db.execute(sql)


    def addReceiver(self, receiver):

        name = receiver.name
        enabled = receiver.enabled
        exported = receiver.exported
        intent_data = base64.b64encode(receiver.intent_data)
        application_id = receiver.application_id

        permission = receiver.permission

        if permission != None:
            permission_id = permission._id
        else:
            permission_id = 0

        sql = ('INSERT INTO receivers(name, permission, exported, enabled, intent_data, application_id) '
               "VALUES ('%s',%i,'%s','%s','%s',%i)"  % (name, permission_id, exported, enabled,
                                                        intent_data, application_id))

        return self.app_db.execute(sql)

    def addShared(self, application_id, name):
        
        sql = ( 'INSERT INTO shared_libraries(name, application_id)'
            "VALUES( '%s',%i)" % (name, application_id))

        return self.app_db.execute(sql)

    # End Table Modification


#### Table Querying Methods ############################
    def getApps(self,aosp=True):

        app_list = list()

        if aosp:
            return self.app_db.execute('SELECT * FROM apps ORDER BY id')
        else:

            sql = ('SELECT * '
                   'FROM apps '
                   'WHERE aosp_package=0 '
                   'ORDER BY id')

            for line in self.app_db.execute(sql):

                id = line[0]
                package_name = line[1]
                project_name = line[2]
                install_path = line[3]
                aosp_package = line[4]
                has_native = line[5]
                min_sdk_version = line[6]
                target_sdk_version = line[7]
                debuggable = line[8]
                permission_id = line[9]
                successfully_unpacked = line[10]

                # TODO: remove once newer schema takes action
                if has_native is None:
                    has_native = 0

                if permission_id != 0 and permission_id is not None:
                    permission = self.resolvePermissionById(permission_id)
                else:
                    permission = None

                app_list.append( Application(project_name, min_sdk_version, target_sdk_version,
                                             debuggable, permission, has_native, id))

            return app_list


    def getAppById(self, application_id):
        c = self.app_db.cursor()

        rtn = c.execute("SELECT * FROM apps WHERE id=%i" % application_id)

        try:
            (id, package_name, project_name, install_path, aosp_package, 
             has_native, min_sdk_version, target_sdk_version, permission_id, debuggable,
             successfully_unpacked) = c.fetchone()

            # TODO: remove once newer schema takes action
            if has_native is None:
                has_native = 0

            if permission_id != 0 and permission_id is not None:
                permission = self.resolvePermissionById(permission_id)
            else:
                permission = None

            return Application(project_name, min_sdk_version, target_sdk_version, debuggable, permission, has_native, id)

        except IOError:
            pass
        #except TypeError:
            log.e(_TAG, "Unable to resolve application ID %d!" % id)
            return 0

    def getAppByName(self, name):
        c = self.app_db.cursor()

        _id = ""
        package_name = ""
        project_name = ""
        install_path = ""
        aosp_package = ""
        has_native = ""
        min_sdk_version = ""
        target_sdk_version = ""
        permission_id = ""
        debuggable = ""
        successfully_unpacked = ""

        rtn = c.execute("SELECT * FROM apps WHERE project_name='%s'" % name)
        try:

            (id, package_name, project_name, install_path, aosp_package,
             has_native, min_sdk_version, target_sdk_version, permission_id, debuggable,
             successfully_unpacked) = c.fetchone()

            # TODO: remove once newer schema takes action
            if has_native is None:
                has_native = 0

            if permission_id != 0 and permission_id is not None:
                permission = self.resolvePermissionById(permission_id)
            else:
                permission = None

            return Application(project_name, min_sdk_version, target_sdk_version, debuggable, permission, has_native, id)

        except TypeError:
            log.e(_TAG, "Unable to resolve application name : %s!" % name)
            return None



    def resolveGroupByName(self, permission_group_name):
        c = self.app_db.cursor()

        rtn = c.execute("SELECT * FROM permission_groups WHERE name=\"%s\"" % permission_group_name)

        try:
            id, name, application_id = c.fetchone()
            return PermissionGroup(name, int(application_id), id=int(id))

        except TypeError:
            log.e(_TAG, "Unable to resolve group \"%s\"!" % permission_group_name)
            return None

    def resolveGroupById(self, permission_group_id):

        c = self.app_db.cursor()

        rtn = c.execute("SELECT * FROM permission_groups WHERE id=%i" % permission_group_id)

        try:
            id, name, application_id = c.fetchone()
            return PermissionGroup(name, int(application_id), id=int(id))

        except TypeError:
            log.e(_TAG, "Unable to resolve group ID %i!" % permission_group_id)
            return 0

    def resolvePermissionByName(self, permission_name):

        c = self.app_db.cursor()

        rtn = c.execute("SELECT * FROM permissions WHERE name=\"%s\"" % permission_name)

        try:
            id, name, permission_group_id, protection_level, application_id = c.fetchone()

            if permission_group_id is not 0:
                permission_group = self.resolveGroupById(permission_group_id)
            else:
                permission_group = None

            return Permission(name, protection_level, permission_group, int(application_id), id=int(id))

        except TypeError:
            log.e(_TAG, "Unable to resolve permission \"%s\"!" % permission_name)
            return None

    def resolvePermissionById(self, permission_id):

        c = self.app_db.cursor()

        rtn = c.execute("SELECT * FROM permissions WHERE id=%d" % permission_id)

        try:
            id, name, permission_group_id, protection_level, application_id = c.fetchone()

            if permission_group_id is not 0:
                permission_group = self.resolveGroupById(permission_group_id)
            else:
                permission_group = None

            return Permission(name, protection_level, permission_group, int(application_id), id=int(id))

        except TypeError:
            log.e(_TAG, "Unable to resolve permission by id %d!" % permission_id)
            return None

    def getAppPermissions(self, application_id):
      
        perm_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT * FROM permissions '
               'WHERE application_id=%d' % application_id) 
        
        for line in c.execute(sql):
             _id = line[0]
             name = line[1]
             permission_group_id = line[2]
             protection_level = line[3]
 
             if permission_group_id != 0:
                 permission_group = self.resolveGroupById(permission_group_id)
             else:
                 permission_group = None

             perm_list.append( Permission(name, protection_level, permission_group, 
                               application_id, id=_id) )

        return perm_list

    def getAppUsesPermissions(self, application_id):

        uses_perm_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT permission_id FROM app_uses_permissions '
               'WHERE application_id=%d' % application_id)

        for line in c.execute(sql):
             permission_id = line[0]

             permission = self.resolvePermissionById(permission_id)

             uses_perm_list.append(permission)

        return uses_perm_list


    def getAppActivities(self, application_id):

        activity_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT * FROM activities '
               'WHERE application_id=%d' % application_id)

        for line in c.execute(sql):

             _id = line[0]
             name = line[1]
             permission_id = line[2]
             exported = line[3]
             enabled = line[4]
             intent_data = base64.b64decode(line[5])
             application_id = line[6]

             if exported == "None":
                 exported = None
             elif exported == "False":
                 exported = False
             elif exported == "True":
                 exported = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % exported)

             if enabled == "None":
                 enabled = None
             elif enabled == "False":
                 enabled = False
             elif enabled == "True":
                 enabled = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % enabled)

             if permission_id != 0:
                 permission = self.resolvePermissionById(permission_id)
             else:
                 permission = None

             activity_list.append( Activity(name, enabled, exported, permission, intent_data, 
                                            application_id, id=_id) )

        return activity_list


    def getAppServices(self, application_id):

        service_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT * FROM services '
               'WHERE application_id=%d' % application_id)

        for line in c.execute(sql):

             _id = line[0]
             name = line[1]
             permission_id = line[2]
             exported = line[3]

             enabled = line[4]
             intent_data = base64.b64decode(line[5])
             application_id = line[6]

             if exported == "None":
                 exported = None
             elif exported == "False":
                 exported = False
             elif exported == "True":
                 exported = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % exported)

             if enabled == "None":
                 enabled = None
             elif enabled == "False":
                 enabled = False
             elif enabled == "True":
                 enabled = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % enabled)

             if permission_id != 0:
                 permission = self.resolvePermissionById(permission_id)
             else:
                 permission = None

             service_list.append( Service(name, enabled, exported, permission, intent_data,
                                            application_id, id=_id) )

        return service_list

    def getAppProviders(self, application_id):

        provider_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT * FROM providers '
               'WHERE application_id=%d' % application_id)

        for line in c.execute(sql):

             _id = line[0]
             authorities  = line[1].split(';')
             name = line[2]
             permission_id = line[3]
             read_permission_id = line[4]
             write_permission_id = line[5]
             exported = line[6]
             enabled = line[7]
             grant_uri_permissions = line[8]
             path_permission_data = base64.b64decode(line[9])
             
             grant_uri_permission_data = base64.b64decode(line[10])
             application_id = line[11]             

             if exported == "None":
                 exported = None
             elif exported == "False":
                 exported = False
             elif exported == "True":
                 exported = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % exported)

             if enabled == "None":
                 enabled = None
             elif enabled == "False":
                 enabled = False
             elif enabled == "True":
                 enabled = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % enabled)

             # Generic Permission
             if permission_id != 0:
                 permission = self.resolvePermissionById(permission_id)
             else:
                 permission = None

             # Read Permission
             if read_permission_id != 0:
                 read_permission = self.resolvePermissionById(read_permission_id)
             else:
                 read_permission = None

             # Write Permission
             if write_permission_id != 0:
                 write_permission = self.resolvePermissionById(write_permission_id)
             else:
                 write_permission = None

             provider_list.append( Provider(name, authorities, enabled, exported, 
                                            grant_uri_permissions, grant_uri_permission_data,
                                            path_permission_data, permission, read_permission,
                                            write_permission, application_id, id=_id))

        return provider_list

    def getAppReceivers(self, application_id):

        receiver_list = list()
        c = self.app_db.cursor()

        sql = ('SELECT * FROM receivers '
               'WHERE application_id=%d' % application_id)
        
        for line in c.execute(sql):

             _id = line[0]
             name = line[1]
             permission_id = line[2]
             exported = line[3]
             enabled = line[4]
             intent_data = base64.b64decode(line[5])
             application_id = line[6]

             if exported == "None":
                 exported = None
             elif exported == "False":
                 exported = False
             elif exported == "True":
                 exported = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % exported)

             if enabled == "None":
                 enabled = None
             elif enabled == "False":
                 enabled = False
             elif enabled == "True":
                 enabled = True
             else:
                 log.e(_TAG, "Unknown export value :  %s" % enabled)

             if permission_id != 0:
                 permission = self.resolvePermissionById(permission_id)
             else:
                 permission = None

             receiver_list.append( Receiver(name, enabled, exported, permission, intent_data,
                                            application_id, id=_id) )

        return receiver_list

########### Update Methods ########################
    def updateApplication(self, application):

        print "UpdateApplication called!"

        _id = application._id
        project_name =  application.project_name
        min_sdk_version = application.min_sdk_version
        target_sdk_version = application.target_sdk_version
        debuggable = application.debuggable
        has_native = application.has_native

        print debuggable, application.debuggable

        if application.permission is None:
            permission = 0
        else:
            permission = application.permission._id

        sql = ("UPDATE apps SET id=?, project_name=?, min_sdk_version=?, "
               "target_sdk_version=?, debuggable=?, permission=?, has_native=? "
               "WHERE id=?")

        return self.app_db.execute(sql, (_id, project_name, min_sdk_version, target_sdk_version, 
                                         debuggable, permission, has_native, _id))

#        return self.app_db.execute(sql)
        return self.app_db.execute(sql)


# End class AppDb

# Fix Permission, if a numerical is present
# Shamelessly rewritten from AOSP
def protectionToString(level):

    prot_level = "????"

    level_based = level & PROTECTION_MASK_BASE

    if level_based == PROTECTION_DANGEROUS:
        prot_level = "dangerous"
    elif level_based == PROTECTION_NORMAL:
        prot_level = "normal"
    elif level_based == PROTECTION_SIGNATURE:
        prot_level = "signature"
    elif level_based == PROTECTION_SIGNATURE_OR_SYSTEM:
        prot_level = "signatureOrSystem"

    if (level & PROTECTION_FLAG_SYSTEM) != 0:
        prot_level += "|system"
    if (level & PROTECTION_FLAG_DEVELOPMENT) != 0:
        prot_level += "|development"

    return prot_level
