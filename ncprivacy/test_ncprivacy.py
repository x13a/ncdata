#!/usr/bin/env python3

import os
import shutil
import sqlite3
import tempfile
import unittest

import ncprivacy


class NCPrivacyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = ncprivacy.get_db_path()

    def setUp(self):
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=f'{ncprivacy.__name__}.')
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
        self.assertTrue(
            len(tuple(ncprivacy.iter_apps(cur))) ==
            ncprivacy.count_apps(cur) ==
            ncprivacy.rm_apps(cur)
        )

    def test_records(self):
        cur = self.cur
        count_privacy_records = ncprivacy.count_privacy_records(cur)
        self.assertLessEqual(len(tuple(ncprivacy.iter_records(cur))),
                             count_privacy_records)
        self.assertEqual(count_privacy_records,
                         ncprivacy.rm_privacy_records(cur))


if __name__ == '__main__':
    unittest.main()
