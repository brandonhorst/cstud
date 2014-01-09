#cstud

##Introduction

InterSystems Caché is a high-performance post-relational database. It's awesome, but all serious development tasks require the use of Caché Studio, which only runs on Windows.

This command line utility opens up Caché to allow for the development of plugins for various IDEs and Editors, as well as direct command-line usage.

Current version: 0.0.2

##Usage

    cstud [CONNECTION_ARGUMENTS] COMMAND [COMMAND_ARGUMENTS]

###`CONNECTION_ARGUMENTS`
    
* `-U, --username` - a valid Caché Username.
    - Default: `_SYSTEM`
* `-P, --password` - the password for the Caché user.
    - Default: `SYS`

Additionally, you need to specify either an Instance Name, or a Hostname/Port/Directory:
        
* `-I, --instance` - the instance name of a local cache instance.
    - Default: the results of `ccontrol default`
* `-H, --host` - the host name or IP Address of the Caché server.
* `-S, --port` - the SuperServer port number of the Caché server.
* `-D, --directory` - the Caché install directory. 

###`COMMAND`s and `COMMAND_ARGUMENTS`

* `list` - list all available classes in the namespace
* `upload` - upload all files specified in `COMMAND_ARGUMENTS` to the Caché server
* `download` - download all classes specificed in `COMMAND_ARGUMENTS` from the Caché server, and output to stdout
* `edit` - download all classes specificed in `COMMAND_ARGUMENTS` from the Caché server, and open up the editor specified by the EDITOR environment variable. After the editor closes, upload that result to the server and compile. This has been tested with EDITOR=subl (for Sublime Text) and EDITOR=mate (for TextMate) and works well.

###Notes

If the Python 3 bindings are not installed, running cstud will automatically install them. `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`, and `PATH` will automatically be set appropriately if needed.

##Implementation

`cstud` is written in Python 3 and makes use of the Caché Python bindings (not included). Its primary inteface on the Caché side is the class `%Compiler.UDL.TextServices`.

##Limitations

* The Caché Python bindings must be installed on the local machine.
* `cstud` relies on `%Compiler.UDL.TextServices`, which will be added to Caché in version 2014.2. In other words, `cstud` does not run on any currently-released version of Caché. 
* `%Compiler.UDL.TextServices` does not currently support `XDATA` blocks or `SqlComputeCode` attributes. Once that functionality is added, `cstud` will automatically support it.
* At the moment, it only works on OSX. It was tested on Mavericks, but should work with any version.

##Goals

* Allow for all functionality that Studio provides (hard functionality, not wizards and such) on all Caché-supported platforms (including OSX, UNIX, and Windows).
    - ~~Listing available classes by namespace~~
    - ~~Download classes by name~~
    - Download generated code (int, cls...)
    - Upload classes (does not yet support XDATA and SqlComputeCode)
* Handle errors well.
* Soft functionality (syntax highlighting, wizards, snippets, and the like) will be pursued in independent projects. I hope to add functionality for Sublime Text, a solid multi-platform editor.