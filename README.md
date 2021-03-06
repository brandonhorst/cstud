#cstud

##Introduction

InterSystems Caché is a high-performance post-relational database. It's awesome, but all serious development tasks require the use of Caché Studio, which only runs on Windows.

This command line utility opens up Caché to allow for the development of plugins for various IDEs and Editors, as well as direct command-line usage.

Current version: 0.0.3

##Usage

    cstud [CONNECTION_ARGUMENTS] COMMAND [COMMAND_ARGUMENTS]

###`CONNECTION_ARGUMENTS`
    
* `-U, --username` - a valid Caché Username.
    - Default: `_SYSTEM`
* `-P, --password` - the password for the Caché user.
    - Default: `SYS`
* `-N, --namespace` - the Namespace to work in.
* `-V` - verbose output.

Additionally, you need to specify either an Instance Name, or a Hostname/Ports:
        
* `-I, --instance` - the instance name of a local cache instance.
    - Default: the results of `ccontrol default`
* `-H, --host` - the host name or IP Address of the Caché server.
* `-S, --super-server-port` - the SuperServer port number of the Caché server.
* `-W, --web-server-port` - the Web Server port number of the Caché server.

###`COMMAND`s and `COMMAND_ARGUMENTS`

* `list`
    * `list classes` - list all classes in the namespace
    * `list routines` - list all routines in the namespace. You can specify a type with the `-t` flag
    * `list namespaces` - list all namespaces on this instance. It doesn't matter which namespace you call this from.
* `info` - get information about the configuration
* `upload` - upload all files specified in `COMMAND_ARGUMENTS` to the Caché server
* `download` - download all classes specificed in `COMMAND_ARGUMENTS` from the Caché server, and output to stdout
* `edit` - download all classes specificed in `COMMAND_ARGUMENTS` from the Caché server, and open up the editor specified by the `EDITOR` environment variable. After the editor closes, upload that result to the server and compile. This has been tested with `EDITOR=subl` (for Sublime Text) and `EDITOR=mate` (for TextMate) and works well
* `import` - import all files specified in COMMAND_ARGUMENTS using $system.OBJ.Load()
* `export` - export all classes/routines/globals specificed in `COMMAND_ARGUMENTS` from the Caché server, via `$system.OBJ.Export()`. You must specify a filetype (`.CLS`, `.MAC`, `.GBL`, etc.)
    * use `-o` to specify an output file. If not specified, export to `STDOUT`.
* `find` - find things on the server.
    * use `-t` to only search for specific types. Options are property|parameter|method|class|routine|macro|table.
    * use `-c` to supply a class context to search for properties, parameters, and methods.
    * omit `-t` to execute a find-in-files.
* `execute` - Execute arbitrary COS code, either from a file or passed into `STDIN`. For ease of use, I would recommend adding the following code to your `.bash_profile`:
    * `function cx { (echo "$1" | cstud execute -) }`
    * Then you can run it like `cx 'write $job'`
* `loadWSDL` - Load a WSDL from a URL, and generate Cache classes. Due to Cache system limitations, this must be specified as URLs, not as local files.
    * This limitation could be kludged around by generating a temporary CSP Page, and then referencing localhost. I'd rather not do that if possible.

###Notes

If the Python 3 bindings are not installed, running cstud will automatically install them. `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`, and `PATH` will automatically be set appropriately if needed.

##Implementation

`cstud` is written in Python 3 and makes use of the Caché Python bindings (not included). Its primary inteface on the Caché side is the class `%Compiler.UDL.TextServices`.

##Limitations

* The Caché Python bindings must be installed on the local machine.
* `cstud` relies on `%Compiler.UDL.TextServices`, which will be added to Caché in version 2014.1. 
* cstud cannot upload files containing `XData` blocks or `SqlComputeCode`s to Cache running on UNIX. This is a limitation of `%Compiler.UDL.TextServices`
* At the moment, it has been tested on OS X (Mavericks) and Linux (RHEL 6).

##Goals

* Allow for all functionality that Studio provides (hard functionality, not wizards and such) on all Caché-supported platforms (including OSX, UNIX, and Windows).
    - ~~Listing available classes by namespace~~
    - ~~Download classes by name~~
    - ~~Download routines (int, cls...)~~
    - ~~Upload classes~~
    - ~~Edit classes using system editor~~
    - Download generated code given class name (Currently requires a separate command)
* Allow for essential Wizard-implemented Studio functionality
    - Create empty templates for new classes.
* Soft functionality is being pursued in independent projects:
    - Syntax Highlighting: https://github.com/seanklingensmith/CacheColors
    - IDE Features: https://github.com/brandonhorst/SublimeCache
