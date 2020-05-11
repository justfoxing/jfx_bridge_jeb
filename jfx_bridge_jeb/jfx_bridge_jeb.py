from jfx_bridge import bridge

from .server.jfx_bridge_jeb_port import DEFAULT_SERVER_PORT


class JEBBridge:
    jeb_api = None
    java_api = None

    def __init__(
        self,
        connect_to_host=bridge.DEFAULT_HOST,
        connect_to_port=DEFAULT_SERVER_PORT,
        loglevel=None,
        response_timeout=bridge.DEFAULT_RESPONSE_TIMEOUT,
    ):
        """ Set up a bridge. Default settings connect to the default jfx_bridge_jeb server

        loglevel for what logging messages you want to capture

        response_timeout is how long to wait for a response before throwing an exception, in seconds
        """
        self.bridge = bridge.BridgeClient(
            connect_to_host=connect_to_host,
            connect_to_port=connect_to_port,
            loglevel=loglevel,
            response_timeout=response_timeout,
        )

    def get_ctx(self):
        """ Get the IClientContext for interacting with the remote JEB instance """
        return self.bridge.remote_import("jfx_bridge_jeb_server").CTX

    def get_jeb_api(self):
        """ Get the JEB api (com.pnfsoftware.jeb) from the remote connection. 
        """
        if self.jeb_api is None:
            self.jeb_api = self.bridge.remote_import("com.pnfsoftware.jeb")

        return self.jeb_api

    def get_java_api(self):
        """ Get the Java namespace from the remote connection. 
        """
        if self.java_api is None:
            self.java_api = self.bridge.remote_import("java")

        return self.java_api
