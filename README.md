JFX Bridge for JEB (JEBBridge)
=====================
I like scripting my RE as much as possible, and JEB is pretty handy for Android reverse-engineering. But JEB's Python scripting is based on Jython, which isn't in a great state these days. Installing new packages is a hassle, if they can even run in a Jython environment, and it's only going to get worse as Python 2 slowly gets turned off.

Like [Ghidra Bridge](https://github.com/justfoxing/ghidra_bridge/) and [IDABridge](https://github.com/justfoxing/jfx_bridge_ida/), JEBBridge is a Python RPC bridge that aims to break you out of the JEB Python environment, so you can more easily integrate with up-to-date Python with all the packages you need to do your work as well as tools like IPython and Jupyter, while being as transparent as possible so you don't have to rewrite too much of your scripts.

How to use for JEB
======================

## Install the jfx_bridge_jeb package and server scripts
1. Install the jfx_bridge_jeb package (packaged at https://pypi.org/project/jfx-bridge-jeb/):
```
pip install jfx_bridge_jeb
```

2. Install the server scripts to a directory you'll run scripts from in JEB.
```
python -m jfx_bridge_jeb.install_server ~/jeb_scripts
```

## Start Server
### JEB Context

1. File->Scripts->Run Script
2. Navigate to where you installed the server scripts
3. Run jfx_bridge_jeb_server.py


## Setup Client
From the client python environment:
```python
import jfx_bridge_jeb

b = jfx_bridge_jeb.JEBBridge() 

ctx = b.get_ctx()
jeb_api = b.get_jeb_api()

prj = ctx.getMainProject()
for dex in prj.findUnits(jeb_api.core.units.code.android.IDexUnit):
    last_string_idx = dex.getStringCount()-1
    last_string = dex.getString(last_string_idx)
    print(last_string.value)
```

Security warning
=====================
Be aware that when running, an JEBBridge server effectively provides code execution as a service. If an attacker is able to talk to the port the bridge server is running on, they can trivially gain execution with the privileges JEB is run with. 

Also be aware that the protocol used for sending and receiving bridge messages is unencrypted and unverified - a person-in-the-middle attack would allow complete control of the commands and responses, again providing trivial code execution on the server (and with a little more work, on the client). 

By default, the server only listens on localhost to slightly reduce the attack surface. Only listen on external network addresses if you're confident you're on a network where it is safe to do so. Additionally, it is still possible for attackers to send messages to localhost (e.g., via malicious javascript in the browser, or by exploiting a different process and attacking the bridge to elevate privileges). You can mitigate this risk by running the bridge server from a JEB process with reduced permissions (a non-admin user, or inside a container), by only running it when needed, or by running on non-network connected systems.

Remote eval
=====================
JEBBridge is designed to be transparent, to allow easy porting of non-bridged scripts without too many changes. However, if you're happy to make changes, and you run into slowdowns caused by running lots of remote queries (e.g., something like `for c in dex.getClasses(): doSomething()` can be quite slow with a large number of classes as each class will result in a message across the bridge), you can make use of the bridge.remote_eval() function to ask for the result to be evaluated on the bridge server all at once, which will require only a single message roundtrip.

If your evaluation is going to take some time, you might need to use the timeout_override argument to increase how long the bridge will wait before deciding things have gone wrong.

If you need to supply an argument for the remote evaluation, you can provide arbitrary keyword arguments to the remote_eval function which will be passed into the evaluation context as local variables. The following example demonstrates getting a list of all the names of all the classes in a binary, passing in the dex unit for a remote_eval:
```python
import jfx_bridge_jeb
b = jfx_bridge_jeb.JEBBridge()

ctx = b.get_ctx()
jeb_api = b.get_jeb_api()

prj = ctx.getMainProject()
name_list = []
for dex in prj.findUnits(jeb_api.core.units.code.android.IDexUnit):
    name_list.extend(b.bridge.remote_eval("[ c.getName() for c in dex.getClasses()]", dex=dex))
```

How it works
=====================
The actual bridge RPC code is implemented in [jfx-bridge](https://github.com/justfoxing/jfx_bridge/). Check it out there and file non-JEB specific issues related to the bridge there.

Tested
=====================
Python 3.6.9->JEB 3.19.1 (Jython 2.7.2)