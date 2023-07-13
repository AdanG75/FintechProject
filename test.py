import unittest

from core.config import charge_settings

if __name__ == '__main__':
    settings = charge_settings()

    dir1 = "./secure/tests"
    suite1 = unittest.defaultTestLoader.discover(dir1, pattern='test*.py')
    runner1 = unittest.TextTestRunner()
    runner1.run(suite1)
