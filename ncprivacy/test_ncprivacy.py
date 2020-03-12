import os
import shutil
import sqlite3
import tempfile
import unittest

from . import (
    __name__ as lib_name,
    ncprivacy,
)


class NCPrivacyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = ncprivacy.get_db_path()

    def setUp(self):
        tmp_fd, tmp_path = tempfile.mkstemp(prefix=f'{lib_name}.')
        os.close(tmp_fd)
        self.tmp_path = tmp_path
        shutil.copy2(self.db_path, tmp_path)
        conn = sqlite3.connect(tmp_path)
        self.cur = conn.cursor()
        self.conn = conn

    def tearDown(self):
        self.cur.close()
        self.conn.close()
        os.unlink(self.tmp_path)

    def test_apps(self):
        cur = self.cur
        ca = ncprivacy.count_apps(cur)
        self.assertEqual(len(tuple(ncprivacy.iter_apps(cur))), ca)
        self.assertEqual(ca, ncprivacy.rm_apps(cur))

    def test_records(self):
        cur = self.cur
        cpr = ncprivacy.count_privacy_records(cur, identifiers=('_',))
        self.assertEqual(cpr, 0)
        cpr2 = ncprivacy.count_privacy_records(cur)
        self.assertLessEqual(len(tuple(ncprivacy.iter_records(cur))), cpr2)
        self.assertEqual(cpr2, ncprivacy.rm_privacy_records(cur))


if __name__ == '__main__':
    unittest.main()
