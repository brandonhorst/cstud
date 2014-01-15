#!/usr/bin/env python3

import argparse
#import intersys.pythonbind3 as pythonbind
import string
import subprocess
import sys
import math
import fileinput
import os
import os.path
import re
import signal
import threading
signal.signal(signal.SIGPIPE,signal.SIG_DFL) 

class CacheInstance:
    def __init__(self, instanceName="", host="", port=0, location=""):
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
            print("Invalid Instance Name: %s".format('instanceName'))
            quit(1)

        if host:
            self.host = host
        if port:
            self.port = port
        if location:
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

def install(instance,force):
    binDirectory = os.path.join(instance.location,'bin')
    rerun = addToEnvPath('DYLD_LIBRARY_PATH',binDirectory) and addToEnvPath('PATH',binDirectory)
    if rerun:
        os.execve(os.path.realpath(__file__), sys.argv, os.environ)

    try:
        if force:
            raise ImportError
        import intersys.pythonbind3
    except ImportError:
        print("First run - installing python bindings")
        installerDirectory = os.path.join(instance.location, 'dev', 'python')
        installerPath = os.path.join(installerDirectory, 'setup3.py')
        installerProcess = subprocess.Popen([sys.executable, installerPath, 'install'], cwd=installerDirectory, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        installerProcess.communicate(bytes(instance.location, 'UTF-8'))
        import intersys.pythonbind3


    return intersys.pythonbind3

def connect(bindings,username,password,namespace,instance):
    url = '%s[%i]:%s' % (instance.host, instance.port, namespace)
    conn = bindings.connection()
    conn.connect_now(url, username, password, None)
    database = bindings.database(conn)
    return database

def deleteRoutine(database,routineName):
    database.run_class_method('%Library.Routine',"Delete",[routineName])

def deleteClass(database,className,verbose):
    flags = "d" if verbose else "-d"
    database.run_class_method('%SYSTEM.OBJ', 'Delete', [className,flags])

def routineExists(database,routineName):
    exists = database.run_class_method('%Library.Routine','Exists',[routineName])
    return exists

def classExists(database,className):
    exists = database.run_class_method('%Dictionary.ClassDefinition', '%ExistsId', [className])
    return exists

def classNameForText(text):
    match = re.search(r'^Class\s',text,re.MULTILINE)
    if match:
        classNameIndexBegin = match.end()
        classNameIndexEnd = text.find(' ', classNameIndexBegin)
        className = text[classNameIndexBegin:classNameIndexEnd]
        return className
    return None
        
def chunkString(string,chunkSize=32000):
    return [string[i:i+chunkSize] for i in range(0, len(string), chunkSize)]

# def outputIfFile(string,openFile):
#     if openFile:
#         openFile.write(string)
#     else:
#         print(string,end="")

def uploadRoutine(pythonbind,database,verbose,text):
    match = re.search(r'^(#; )?(?P<routine_name>(\w|%|\.)+)',text,re.MULTILINE)
    routineName = match.group('routine_name')

    # if routineExists(database,routineName):
        # if verbose: print('Deleting %s' % routineName)
        # deleteRoutine(database,routineName)

    routine = database.run_class_method('%Library.Routine', '%New', [routineName])

    crlfText = text.replace('\n','\r\n')

    for chunk in chunkString(crlfText):
        routine.run_obj_method('Write',[chunk])

    if verbose: print('Uploading %s' % routineName)
    routine.run_obj_method('Save',[])
    routine.run_obj_method('Compile',['cko'])

def uploadClass(pythonbind,database,verbose,text):
    stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
    name = classNameForText(text)

    if classExists(database,name):
        deleteClass(database,name,verbose)

    crlfText = text.replace('\n','\r\n')

    for chunk in chunkString(crlfText):
        stream.run_obj_method('Write',[chunk])

    if verbose: print('Uploading %s' % name)
    database.run_class_method('%Compiler.UDL.TextServices', 'SetTextFromStream',[None, name, stream])
    flags = "ckd" if verbose else "ck-d"
    database.run_class_method('%SYSTEM.OBJ','Compile',[name,flags])

def uploadOnce(pythonbind,database,verbose,text):
    name = classNameForText(text)
    if name:
        uploadClass(pythonbind,database,verbose,text)
    else:
        uploadRoutine(pythonbind,database,verbose,text)

def uploadStuff(pythonbind,database,verbose,files):
    for openFile in files:
        text = openFile.read()
        uploadOnce(pythonbind,database,verbose,text)

def downloadClass(pythonbind,database,verbose,className):
    stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
    argList = [None,className,stream] #the last None is byref
    database.run_class_method('%Compiler.UDL.TextServices', 'GetTextAsStream', argList)
    outputStream = argList[2]
    total = ""
    while True:
        content = outputStream.run_obj_method('Read',[])
        if content:
            lfcontent = content.replace('\r\n','\n')
            total = total + lfcontent
        else:
            break
    return total

def downloadRoutine(pythonbind,database,verbose,routineName):
    routine = database.run_class_method('%Library.Routine','%OpenId',[routineName])
    total = ""
    if routine:
        while True:
            content = routine.run_obj_method('Read',[])
            if content:
                lfcontent = content.replace('\r\n','\n')
                total += lfcontent
            else:
                break
    return total

def downloadOnce(pythonbind,database,verbose,name):
    content = downloadClass(pythonbind,database,verbose,name)
    if not content:
        content = downloadRoutine(pythonbind,database,verbose,name)
    return content

def downloadStuff(pythonbind,database,verbose,names):
    for name in names:
        print(downloadOnce(pythonbind,database,verbose,name))

def executeCode(pythonbind,database,verbose,code):
    stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
    className = "ISCZZZZZZZZZZZZZZCSTUD.cstud"
    methodName = "xecute"
    classCode = """Class {0} Extends %RegisteredObject {{
    ClassMethod {1}() {{
        {2}
    }}
    }}
    """.format(className,methodName,code).replace("\n","\r\n")

    if classExists(database,className):
        deleteClass(database,className,verbose)

    for chunk in chunkString(classCode):
        stream.run_obj_method('Write',[chunk])

    database.run_class_method('%Compiler.UDL.TextServices', 'SetTextFromStream',[None, className, stream])
    flags = "ckd" if verbose else "ck-d"
    database.run_class_method('%SYSTEM.OBJ','Compile',[className,flags])
    database.run_class_method(className,methodName,[])
    print()

def executeFile(pythonbind,database,verbose,theFile):
    executeCode(pythonbind,database,verbose,theFile.read())

def executeStuff(pythonbind,database,verbose,stdin,files):
    if stdin:
        inlineCode = sys.stdin.read().replace("\n","\r\n")
        executeCode(pythonbind,database,verbose,inlineCode)
    for f in files:
        print(executeFile(pythonbind,database,verbose,f))

def editOnce(pythonbind,database,name):
    initialContent = downloadOnce(pythonbind,database,False,name)

    editor = subprocess.Popen([os.environ['EDITOR']], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    finalContentTuple = editor.communicate(bytes(initialContent,'UTF-8'))
    finalContent = finalContentTuple[0].decode('UTF-8')

    uploadOnce(pythonbind,database,False,finalContent)

def editStuff(pythonbind,database,names):
    threads = []
    for name in names:
        threads.append(threading.Thread(target=editOnce, args=[pythonbind,database,name]))
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]

def listClasses(pythonbind,database,system):
    sql = 'SELECT Name FROM %Dictionary.ClassDefinition'
    if not system:
        sql = sql + " WHERE NOT Name %STARTSWITH '%'"
    query = pythonbind.query(database)
    sql_code = query.prepare(sql)
    sql_code = query.execute()
    while True:
        cols = query.fetch([None])
        if len(cols) == 0: break
        print(cols[0])

def listRoutines(pythonbind,database,type,system):
    sql = "SELECT Name FROM %Library.Routine_RoutineList('*.{0},%*.{0}',1,0)".format(type)
    if not system:
        sql = sql + " WHERE NOT Name %STARTSWITH '%'"
    query = pythonbind.query(database)
    sql_code = query.prepare(sql)
    sql_code = query.execute()
    while True:
        cols = query.fetch([None])
        if len(cols) == 0: break
        print(cols[0])


def listStuff(pythonbind,database,types,system):
    if types == None:
        types = ['cls','mac','int','inc','bas']
    for theType in types:
        if theType.lower() == 'cls':
            listClasses(pythonbind,database,system)
        else:
            listRoutines(pythonbind,database,theType,system)

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
    mainParser.add_argument('--force-install', action='store_true')

    subParsers = mainParser.add_subparsers(help='cstud commands')

    uploadParser = subParsers.add_parser('upload', help='Upload and compile classes or routines')
    uploadParser.add_argument('-v','--verbose',action='store_true',help='output details')
    uploadParser.add_argument("files", metavar="F", type=argparse.FileType('r'), nargs="+", help="files to upload")
    uploadParser.set_defaults(func=uploadStuff)

    downloadParser = subParsers.add_parser('download', help='Download classes or routines')
    downloadParser.add_argument('-v','--verbose',action='store_true',help='output details')
    # downloadParser.add_argument('-n','--routineName',type=str,help='name for uploaded routines')
    downloadParser.add_argument("names", metavar="N", type=str, nargs="+", help="Classes or Routines to download")
    downloadParser.set_defaults(func=downloadStuff)

    executeParser = subParsers.add_parser('execute', help='Execute arbitrary COS code')
    executeParser.add_argument('-v','--verbose', action='store_true', help='output details')
    executeParser.add_argument('-', dest="stdin", action='store_true', help='Take code from stdin')
    executeParser.add_argument("files", metavar="N", type=str, nargs="*", help="Execute routine specified in a file")
    executeParser.set_defaults(func=executeStuff)

    editParser = subParsers.add_parser('edit', help='Download classes')
    editParser.add_argument("names", metavar="N", type=str, nargs="+", help="Classes or Routines to edit")
    editParser.set_defaults(func=editStuff)

    listParser = subParsers.add_parser('list', help='List all classes and routines in namespace')
    listParser.add_argument('-t','--type',action='append',help='cls|mac|int|obj|inc|bas',dest="types",choices=['cls','obj','mac','int','inc','bas'])
    listParser.add_argument('-s','--noSystem',action='store_false', help='hide system classes',dest="system")
    listParser.set_defaults(func=listStuff)

    results = mainParser.parse_args()
    kwargs = dict(results._get_kwargs())

    instance = CacheInstance(kwargs.pop('instance'), kwargs.pop('host'), kwargs.pop('port'), kwargs.pop('directory'))
    bindings = install(instance,force=kwargs.pop('force_install'))
    database = connect(bindings, kwargs.pop('username'), kwargs.pop('password'), kwargs.pop('namespace'), instance)
    kwargs.pop('func')(bindings,database,**kwargs)

if __name__ == "__main__":
    __main()