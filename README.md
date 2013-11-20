cstud
=====

Command line development tool for InterSystems Caché (Studio for UNIX)

#Introduction

InterSystems Caché is a high-performance post-relational database. It's awesome, but all serious development tasks require the use of Caché Studio, which only runs on Windows. This command line utility opens up Caché to allow for the development of plugins for various IDEs and Editors, as well as direct command-line usage.

#Usage

cstud \[CONNECTION_ARGUMENTS\] COMMAND \[COMMAND_ARGUMENTS\]

###CONNECTION_ARGUMENTS
    
    -U, --username - a valid Caché Username. Default: _SYSTEM
    -P, --password - the password for the Caché user. Default: SYS
    -H, --host - the host name or IP Address of the Caché server. Default: 127.0.0.1
    -S, --port - the SuperServer port number of the Caché server. Default: 1972
    -D, --cache-directory - the Caché install directory. Default: /intersystems/cache

###COMMANDs and COMMAND_ARGUMENTS

    list - list all available classes in the namespace
    upload - upload all files specified in COMMAND_ARGUMENTS to the Caché server
    download - download all classes specificed in COMMAND_ARGUMENTS from the Caché server, and output to stdout

###Notes

If the Python 3 bindings are not installed, running cstud will automatically install them. LD_LIBRARY_PATH, DYLD_LIBRARY_PATH, and PATH will automatically be set appropriately if needed.

#Implementation

cstud is written in Python3 and makes use of the Caché Python bindings (not included). Its primary inteface on the Caché side is the class %Compiler.UDL.TextServices.

#Limitations

The Caché Python bindings must be installed on the local machine. cstud relies on %Compiler.UDL.TextServices, which will be added to Caché in version 2014.2. In other words, cstud does not run on any currently-released version of Caché. 