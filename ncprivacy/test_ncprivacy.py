import sqlite3
import unittest

from ncprivacy import ncprivacy  # pycharm not main test fails with . import


class NCPrivacyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = ncprivacy.get_db_path()

    def setUp(self):
        source = sqlite3.connect(self.db_path)
        dest = sqlite3.connect(':memory:')
        source.backup(dest)
        source.close()
        self.cur = dest.cursor()
        self.conn = dest

    def tearDown(self):
        self.cur.close()
        self.conn.close()

    def test_apps(self):
        tuple(ncprivacy.iter_apps(self.cur))

    def test_records(self):
        cur = self.cur
        cpr = ncprivacy.count_privacy_records(cur)
        self.assertLessEqual(len(tuple(ncprivacy.iter_records(cur))), cpr)
        self.assertEqual(cpr, ncprivacy.rm_privacy_records(cur))


if __name__ == '__main__':
    unittest.main()
