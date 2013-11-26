#!/usr/local/bin/python3

import argparse
#import intersys.pythonbind3 as pythonbind
import subprocess
import sys
import os
import os.path

class CacheInstance:
    def __init__(self, instanceName="", host="", port=0, location=""):
        if not (host or port or location):
            if not instanceName:
                instanceName = self.getDefaultCacheInstanceName()
            ccontrol = subprocess.Popen(['ccontrol', 'qlist'],stdout=subprocess.PIPE)
            stdout = ccontrol.communicate()[0]
            instanceStrings = stdout.decode('UTF-8').split('\n')
            for instanceString in instanceStrings:
                instanceArray = instanceString.split('^')
                if instanceName.upper() == instanceArray[0]:
                    self.host = '127.0.0.1'
                    self.port = int(instanceArray[5])
                    self.location = instanceArray[1]
                    break
            else:
                print("Invalid Instance Name")
                quit(1)
        else:
            self.host = host
            self.port = port
            self.location = location

    def getDefaultCacheInstanceName(self):
        ccontrol = subprocess.Popen(['ccontrol', 'default'],stdout=subprocess.PIPE)
        stdout = ccontrol.communicate()[0]
        return stdout.decode('UTF-8').split('\n')[0]


#Returns True if it was not already there, false if it was
def addToEnvPath(env,location):
    changedIt = True
    if not os.environ.get(env):
        os.environ[env] = ":"+location
    elif not location in os.environ.get(env):
        os.environ[env] += ":"+location
    else:
        changedIt = False
    return changedIt

def install(instance):
    binDirectory = os.path.join(instance.location,'bin')
    rerun = addToEnvPath('DYLD_LIBRARY_PATH',binDirectory) and addToEnvPath('PATH',binDirectory)
    if rerun:
        os.execve(os.path.realpath(__file__), sys.argv, os.environ)

    try:
        import intersys.pythonbind3
    except ImportError:
        print("First run - installing python bindings")
        installerDirectory = os.path.join(directory, 'dev', 'python')
        installerPath = os.path.join(installerDirectory, 'setup3.py')
        installerProcess = subprocess.Popen([sys.executable, installerPath, 'install'], cwd=installerDirectory, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        installerProcess.communicate(bytes(directory, 'UTF-8'))
        import intersys.pythonbind3


    return intersys.pythonbind3

def connect(bindings,username,password,namespace,instance):
    url = '%s[%i]:%s' % (instance.host, instance.port, namespace)
    conn = bindings.connection()
    conn.connect_now(url, username, password, None)
    database = bindings.database(conn)
    return database

def deleteClass(database,className):
    database.run_class_method('%SYSTEM.OBJ', 'Delete', [className])

def classExists(database,className):
    exists = database.run_class_method('%Dictionary.ClassDefinition', '%ExistsId', [className])
    return exists

def uploadClasses(pythonbind,database,verbose,files):
    for openFile in files:
        stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
        text = openFile.read()

        classNameIndexBegin = text.find(' ')+1
        classNameIndexEnd = text.find(' ', classNameIndexBegin)
        className = text[classNameIndexBegin:classNameIndexEnd]
        
        if verbose: print('Deleting %s' % className)
        if classExists(database,className):
            deleteClass(database,className)

        crlfText = text.replace('\n','\r\n')
        stream.run_obj_method('Write',[crlfText])

        if verbose: print('Uploading %s' % className)
        x = database.run_class_method('%Compiler.UDL.TextServices', 'SetTextFromStream',[None, className, stream])
        database.run_class_method('%SYSTEM.OBJ','Compile',[className])
        #print(x)

def downloadClasses(pythonbind,database,verbose,classes):
    for className in classes:

        stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
        argList = [None,className,stream] #the last None is byref
        x = database.run_class_method('%Compiler.UDL.TextServices', 'GetTextAsStream', argList)
        outputStream = argList[2]
        content = outputStream.run_obj_method('Read',[])
        print(content)

def listClasses(pythonbind,database):
    sql = 'SELECT Name FROM %Dictionary.ClassDefinition'
    query = pythonbind.query(database)
    sql_code = query.prepare(sql)
    sql_code = query.execute()
    while True:
        cols = query.fetch([None])
        if len(cols) == 0: break
        print(cols[0])

def __main():
    mainParser = argparse.ArgumentParser()

    mainParser.add_argument('-U', '--username', type=str, default='_SYSTEM')
    mainParser.add_argument('-P', '--password', type=str, default='SYS')
    mainParser.add_argument('-N', '--namespace', type=str, default='USER')
    specificationGroup = mainParser.add_mutually_exclusive_group()
    specificationGroup.add_argument('-I', '--instance', type=str, default=None)
    locationGroup = specificationGroup.add_argument_group('location')
    locationGroup.add_argument('-H', '--host', type=str)
    locationGroup.add_argument('-S', '--port', type=int)
    locationGroup.add_argument('-D', '--directory', type=str)

    subParsers = mainParser.add_subparsers(help='cstud commands')

    uploadParser = subParsers.add_parser('upload', help='Upload classes into the given namespace')
    uploadParser.add_argument('-v','--verbose',action='store_true',help='output details')
    uploadParser.add_argument("files", metavar="F", type=argparse.FileType('r'), nargs="+", help="files to upload")
    uploadParser.set_defaults(func=uploadClasses)

    downloadParser = subParsers.add_parser('download', help='Download classes to the file system')
    downloadParser.add_argument('-v','--verbose',action='store_true',help='output details')
    downloadParser.add_argument("classes", metavar="C", type=str, nargs="+", help="Classes to download")
    downloadParser.set_defaults(func=downloadClasses)

    listParser = subParsers.add_parser('list', help='List all classes in namespace')
    listParser.set_defaults(func=listClasses)


    results = mainParser.parse_args()
    kwargs = dict(results._get_kwargs())

    instance = CacheInstance(kwargs.pop('instance'), kwargs.pop('host'), kwargs.pop('port'), kwargs.pop('directory'))
    bindings = install(instance)
    database = connect(bindings, kwargs.pop('username'), kwargs.pop('password'), kwargs.pop('namespace'), instance)
    kwargs.pop('func')(bindings,database,**kwargs)

if __name__ == "__main__":
    __main()