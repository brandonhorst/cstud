#!/usr/local/bin/python3

import argparse
#import intersys.pythonbind3 as pythonbind
import subprocess
import sys
import os
import os.path

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

def install(directory):
    binDirectory = os.path.join(directory,'bin')
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

def connect(bindings,username,password,host,port,namespace):
    url = '%s[%i]:%s' % (host,port,namespace)
    conn = bindings.connection()
    conn.connect_now(url, username, password, None)
    database = bindings.database(conn)
    return database

def deleteClass(database,className):
    database.run_class_method('%SYSTEM.OBJ', 'Delete', [className])

def classExists(database,className):
    exists = database.run_class_method('%Dictionary.ClassDefinition', '%ExistsId', [className])
    return exists

def uploadClasses(database,verbose,files):
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
        x = database.run_class_method('%Compiler.UDL.TextServices', 'SetTextFromStream',[None,'Test.Class',stream])
        print(x)

def downloadClasses(database,verbose,classes):
    for className in classes:

        stream = database.run_class_method('%Stream.GlobalCharacter', '%New', [])
        argList = [None,className,stream] #the last None is byref
        x = database.run_class_method('%Compiler.UDL.TextServices', 'GetTextAsStream', argList)
        outputStream = argList[2]
        content = outputStream.run_obj_method('Read',[])
        print(content)

def listClasses(database):
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
    mainParser.add_argument('-H', '--host', type=str, default='127.0.0.1')
    mainParser.add_argument('-S', '--port', type=int, default=1972)
    mainParser.add_argument('-N', '--namespace', type=str, default='USER')
    mainParser.add_argument('-D', '--cache-directory', type=str, default='/intersystems/cache')

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

    bindings = install(kwargs.pop('cache_directory'))
    database = connect(bindings, kwargs.pop('username'), kwargs.pop('password'), kwargs.pop('host'), kwargs.pop('port'), kwargs.pop('namespace'))
    kwargs.pop('func')(database,**kwargs)

if __name__ == "__main__":
    __main()