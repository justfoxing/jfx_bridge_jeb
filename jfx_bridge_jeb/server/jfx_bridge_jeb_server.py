import importlib
import logging
import subprocess
import threading

from jfx_bridge import bridge
from jfx_bridge_jeb_port import DEFAULT_SERVER_PORT

""" Need to manually import all of the JEB API packages to ensure they're loaded in the namespace.
    From our client, <javapackage>.<unimported javapackage> doesn't work, but <javapackage>.<imported javapackage>
    and <javapackage>.<unimported javaclass> work just fine. Note that the java classes won't appear in a dir of the
    javapackage until they've been loaded.
    
    Package list grabbed from https://www.pnfsoftware.com/jeb/apidoc/reference/packages.html - left out the
    packages marked as deprecated. Only using the leaf packages - Jython auto-imports the parent packages just fine.
    
    If there's a package not on the list that's needed, a) open an issue/PR on github.com/justfoxing/jfx_bridge_jeb
        b) you can get it from the client with <jfx_bridge_jeb_client>.bridge.remote_import("<full package path>")
"""
JEB_PACKAGE_LIST = [
    "com.pnfsoftware.jeb.client.api",
    "com.pnfsoftware.jeb.client.events",
    "com.pnfsoftware.jeb.client.floating",
    "com.pnfsoftware.jeb.client.jebio",
    "com.pnfsoftware.jeb.client.script",
    "com.pnfsoftware.jeb.client.telemetry",
    "com.pnfsoftware.jeb.core.actions",
    "com.pnfsoftware.jeb.core.dao.impl",
    "com.pnfsoftware.jeb.core.events",
    "com.pnfsoftware.jeb.core.exceptions",
    "com.pnfsoftware.jeb.core.input",
    "com.pnfsoftware.jeb.core.output.code.coordinates",
    "com.pnfsoftware.jeb.core.output.table.impl",
    "com.pnfsoftware.jeb.core.output.text.impl",
    "com.pnfsoftware.jeb.core.output.tree.impl",
    "com.pnfsoftware.jeb.core.properties.impl",
    "com.pnfsoftware.jeb.core.units.code.android.controlflow",
    "com.pnfsoftware.jeb.core.units.code.android.dex",
    "com.pnfsoftware.jeb.core.units.code.android.render",
    "com.pnfsoftware.jeb.core.units.code.asm.analyzer",
    "com.pnfsoftware.jeb.core.units.code.asm.cfg",
    "com.pnfsoftware.jeb.core.units.code.asm.decompiler.ast.emulator",
    "com.pnfsoftware.jeb.core.units.code.asm.decompiler.exceptions",
    "com.pnfsoftware.jeb.core.units.code.asm.decompiler.ir.opt.comp",
    "com.pnfsoftware.jeb.core.units.code.asm.decompiler.opt",
    "com.pnfsoftware.jeb.core.units.code.asm.items",
    "com.pnfsoftware.jeb.core.units.code.asm.mangling",
    "com.pnfsoftware.jeb.core.units.code.asm.memory",
    "com.pnfsoftware.jeb.core.units.code.asm.processor.arch",
    "com.pnfsoftware.jeb.core.units.code.asm.processor.memory",
    "com.pnfsoftware.jeb.core.units.code.asm.render",
    "com.pnfsoftware.jeb.core.units.code.asm.sig",
    "com.pnfsoftware.jeb.core.units.code.asm.simulator",
    "com.pnfsoftware.jeb.core.units.code.asm.type",
    "com.pnfsoftware.jeb.core.units.code.debug.impl",
    "com.pnfsoftware.jeb.core.units.code.java",
    "com.pnfsoftware.jeb.core.units.code.wincommon",
    "com.pnfsoftware.jeb.core.units.impl",
    "com.pnfsoftware.jeb.core.util",
    "com.pnfsoftware.jeb.util.base",
    "com.pnfsoftware.jeb.util.collect",
    "com.pnfsoftware.jeb.util.concurrent",
    "com.pnfsoftware.jeb.util.encoding.java",
    "com.pnfsoftware.jeb.util.encoding.jflex",
    "com.pnfsoftware.jeb.util.encoding.json.parser",
    "com.pnfsoftware.jeb.util.encoding.zip.fsr",
    "com.pnfsoftware.jeb.util.events",
    "com.pnfsoftware.jeb.util.format",
    "com.pnfsoftware.jeb.util.interpreter",
    "com.pnfsoftware.jeb.util.io",
    "com.pnfsoftware.jeb.util.logging",
    "com.pnfsoftware.jeb.util.math",
    "com.pnfsoftware.jeb.util.net",
    "com.pnfsoftware.jeb.util.primitives",
    "com.pnfsoftware.jeb.util.reflect",
    "com.pnfsoftware.jeb.util.serialization.objects",
]

from com.pnfsoftware.jeb.client.api import IScript  # IScript for starting the server


def import_jeb_packages():
    """ Carry out the bulk import, printing errors if there are any """
    for package in JEB_PACKAGE_LIST:
        try:
            importlib.import_module(package)
        except ImportError as ie:
            print(ie)


# Record the jeb ctx used to start the server, so we can access it from the client
CTX = None


class jfx_bridge_jeb_server(IScript):
    """ IScript class triggered by JEB when script is launched """

    def run(self, ctx):
        global CTX

        CTX = ctx

        import_jeb_packages()

        threading.Thread(target=run_server).start()
        print(
            "Server launching in background - will continue to run after launch script finishes...\n"
        )


def run_server(
    server_host=bridge.DEFAULT_HOST,
    server_port=DEFAULT_SERVER_PORT,
    response_timeout=bridge.DEFAULT_RESPONSE_TIMEOUT,
):
    """ Run a jfx_bridge_jeb server (forever, or until shutdown by remote client)
        server_host - what address the server should listen on
        server_port - what port the server should listen on
        response_timeout - default timeout in seconds before a response is treated as "failed"
    """
    bridge.BridgeServer(
        server_host=server_host,
        server_port=server_port,
        loglevel=logging.INFO,
        response_timeout=response_timeout,
    ).run()


def run_script_across_bridge(script_file, ctx, python="python", argstring=""):
    """ Spin up a jfx_bridge_jeb_server and spawn the script in external python to connect back to it.
    
        Need to pass in the JEB ctx from wherever's calling this script, so the other end can access it

        The called script needs to handle the --connect_to_host and --connect_to_port command-line arguments and use them to start
        a jfx_bridge_jeb client to talk back to the server.

        Specify python to control what the script gets run with. Defaults to whatever python is in the shell - if changing, specify a path
        or name the shell can find.
        Specify argstring to pass further arguments to the script when it starts up.
    """
    global CTX

    CTX = ctx

    import_jeb_packages()

    # spawn a jfx_bridge_jeb server - use server port 0 to pick a random port
    server = bridge.BridgeServer(
        server_host="127.0.0.1", server_port=0, loglevel=logging.INFO
    )
    # start it running in a background thread
    server.start()

    try:
        # work out where we're running the server
        server_host, server_port = server.get_server_info()

        print("Running " + script_file)

        # spawn an external python process to run against it
        try:
            output = subprocess.check_output(
                "{python} {script} --connect_to_host={host} --connect_to_port={port} {argstring}".format(
                    python=python,
                    script=script_file,
                    host=server_host,
                    port=server_port,
                    argstring=argstring,
                ),
                stderr=subprocess.STDOUT,
                shell=True,
            )
            print(output)
        except subprocess.CalledProcessError as exc:
            print("Failed ({}):{}".format(exc.returncode, exc.output))

        print(script_file + " completed")

    finally:
        # when we're done with the script, shut down the server
        server.shutdown()
