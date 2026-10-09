import os
import unittest
from unittest.mock import patch
import codex_training_cleanup as cleanup

class Pine:
    def __init__(self, reason=2, error=0, acknowledge=True):
        self.words={cleanup.CONTROL:cleanup.MAGIC,cleanup.CONTROL+4:0,
                    cleanup.CONTROL+8:reason,cleanup.CONTROL+28:0}
        self.error=error;self.acknowledge=acknowledge;self.writes=[]
    def read_u32(self, address):
        if address==cleanup.CONTROL+4 and self.words[address]==8 and self.acknowledge:
            self.words[address]=9;self.words[cleanup.CONTROL+28]=self.error
        return self.words.get(address,0)
    def write_u32(self,address,value):
        self.writes.append((address,value));self.words[address]=value

class Checks(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,PS2X_NATIVE_FRESH_CLEANUP='1');self.environment.start()
    def tearDown(self):self.environment.stop()
    def test_success(self):
        p=Pine();self.assertTrue(cleanup.recover(p));self.assertEqual(p.words[cleanup.CONTROL+4],0)
        self.assertEqual(p.writes,[(cleanup.CONTROL+28,0),(cleanup.CONTROL+4,8),(cleanup.CONTROL+4,0)])
    def test_refused(self):
        p=Pine(error=3)
        with self.assertRaisesRegex(RuntimeError,'ownership: 3'):cleanup.recover(p)
        self.assertEqual(p.words[cleanup.CONTROL+4],0)
    def test_first_match(self):
        p=Pine(reason=0);self.assertFalse(cleanup.recover(p));self.assertFalse(p.writes)
    def test_legacy_runner(self):
        os.environ.pop('PS2X_NATIVE_FRESH_CLEANUP');p=Pine()
        self.assertFalse(cleanup.recover(p));self.assertFalse(p.writes)
    def test_no_ack(self):
        p=Pine(acknowledge=False)
        with self.assertRaises(TimeoutError):cleanup.recover(p,timeout=0)
        self.assertEqual(p.words[cleanup.CONTROL+4],8) # Never cancel an in-flight guest write.
    def test_busy(self):
        p=Pine();p.words[cleanup.CONTROL+4]=3
        with self.assertRaises(RuntimeError):cleanup.recover(p)
        self.assertFalse(p.writes)
    def test_snapshot_order(self):
        events=[];p=Pine()
        class Context:
            def __enter__(self):events.append('request');return p
            def __exit__(self,*args):pass
        class Session:
            native_runtime=True
            def client(self):return Context()
            def snapshot(self,label,*args,**kwargs):
                events.append('capture');return 123
        cleanup.install(Session)
        self.assertEqual(Session().snapshot('original-selected-match',require_running=False),123)
        self.assertEqual(events,['request','capture'])

if __name__=='__main__':unittest.main()
