import sqlite3
import unittest

from ncdata import ncdata  # pycharm not main test fails with . import


class NCDataTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = ncdata.get_db_path()

    def setUp(self):
        src = sqlite3.connect(self.db_path)
        dest = sqlite3.connect(':memory:')
        src.backup(dest)
        src.close()
        self.cur = dest.cursor()
        self.conn = dest

    def tearDown(self):
        self.cur.close()
        self.conn.close()

    def test_apps(self):
        tuple(ncdata.iter_apps(self.cur))

    def test_records(self):
        cur = self.cur
        n = ncdata.count_all_records(cur)
        self.assertLessEqual(len(tuple(ncdata.iter_records(cur))), n)
        self.assertEqual(n, ncdata.rm_all_records(cur))


if __name__ == '__main__':
    unittest.main()
