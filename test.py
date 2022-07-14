import unittest

if __name__ == '__main__':
    dir1 = "./secure/tests"
    suite1 = unittest.defaultTestLoader.discover(dir1, pattern='test*.py')
    runner1 = unittest.TextTestRunner()
    runner1.run(suite1)
