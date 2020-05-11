import logging
import unittest

from . import jfx_bridge_jeb
from .server.jfx_bridge_jeb_port import DEFAULT_SERVER_PORT


class TestBridge(unittest.TestCase):
    """ Assumes there's a JEB running a JEBBridge server at DEFAULT_SERVER_PORT, with an apk loaded """

    @classmethod
    def setUpClass(cls):
        TestBridge.test_bridge = jfx_bridge_jeb.JEBBridge(
            connect_to_port=DEFAULT_SERVER_PORT, loglevel=logging.DEBUG
        )

    def test_example(self):

        ctx = TestBridge.test_bridge.get_ctx()
        jeb_api = TestBridge.test_bridge.get_jeb_api()

        prj = ctx.getMainProject()
        for dex in prj.findUnits(jeb_api.core.units.code.android.IDexUnit):
            last_string_idx = dex.getStringCount() - 1
            last_string = dex.getString(last_string_idx)
            print(last_string.value)

    def test_remote_eval_example(self):

        ctx = TestBridge.test_bridge.get_ctx()
        jeb_api = TestBridge.test_bridge.get_jeb_api()

        prj = ctx.getMainProject()
        name_list = []
        for dex in prj.findUnits(jeb_api.core.units.code.android.IDexUnit):
            name_list.extend(
                TestBridge.test_bridge.bridge.remote_eval(
                    "[ c.getName() for c in dex.getClasses()]", dex=dex
                )
            )

        self.assertTrue(len(name_list) > 0)
