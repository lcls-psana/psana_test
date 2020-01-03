import sys
import os
import shutil
import six

NOCLEAN = os.environ.get('NOCLEAN',False)
if not NOCLEAN:
    sys.stdout.write("%s: set environment variable NOCLEAN=1 to keep temporary directories and from unit tests" % __file__)

class TestOutputDir(object):
    def __init__(self, prefix=None):
        self.rm = False
        self.prefix = prefix
        self.tmpdir = None
        
    def __enter__(self):
        global NOCLEAN
        if six.PY3:
            import tempfile
            with tempfile.NamedTemporaryFile() as tf:
                self.tmpdir = self.prefix + os.path.basename(tf.name)
        else:
            self.tmpdir = os.tempnam(None, self.prefix)
        self.rm = not NOCLEAN
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)
        return self
    
    def make_subdir(self, subdir):
        subdir_path = os.path.join(self.tmpdir, subdir)
        os.makedirs(subdir_path)
        return subdir_path

    def fullpath(self, fname):
        return os.path.join(self.tmpdir, fname)
    
    def root(self):
        return self.tmpdir
    
    def __exit__(self, exType, value, traceback):
        if self.rm:
            shutil.rmtree(self.tmpdir)

def outputDir(prefix=None):
    return TestOutputDir(prefix)

