# SendCmdClient and SendCmdServer

## SendCmdClient
#### Usage
usage: SendCmdClient.exe [-h] [-p [PORT]] [-f CONFIGFILE] [-c COMMANDSET] [hostname] [command]

Run commands on one or more hosts

positional arguments:
  hostname              Server IP address.
  command               Command to send. If command is multiple words, enclose in " ".

options:
  -h, --help            show this help message and exit
  -p, --port [PORT]     The port to connect to the server. Default is 52000.
  -f, --configfile CONFIGFILE
                        JSON config file with multiple hosts
  -c, --commandset COMMANDSET
                        command set

### Examples:
```
SendCmdClient.exe gp7 dir
```

if command is has a space character in it, it must be enclosed in quotes:

```
SendCmdClient.exe gp7 "cd c:\Lightning"
```

Alternatively,a configuration json file can be used to load a command set:

```
SendCmdTCP>SendCmdClient.exe -f sendcmdconfig.json -c load
```

If a config file is not specified, sendcmdconfig.json will be used by default. 

```
SendCmdTCP>SendCmdClient.exe -c load
```

Using the config file will send commands to all computers in parallel.


## SendCmdServer
SendCmdServer needs to be running on the remote computer. Two options are available:

- SendCmdServer.exe
- SendCmdServer_NC.exe - a non-console version.

the port can be specified using the -p or --port argument.

### Usage
usage: SendCmdServer.exe [-h] [-p PORT]

Server for receiving commands from the client.

options:
  -h, --help       show this help message and exit
  -p, --port PORT  The port to connect to the server. Default is 52000.


### Examples:

starting Sendcmdserver with no arguments will load the default port of 52000
```
SendCmdServer.exe
```

A port can be specified using the -p or --port argument
```
SendCmdServer.exe -p 52001
```