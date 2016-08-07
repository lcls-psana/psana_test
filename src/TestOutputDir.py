import sys
import os
import shutil

class TestOutputDir(object):
    def __init__(self, prefix=None):
        self.rm = False
        self.prefix = prefix
        self.tmpdir = None
        
    def __enter__(self):
        self.tmpdir = os.environ.get('PSANA_TEST_OUTDIR', None)
        if self.tmpdir is None:
            self.tmpdir = os.tempnam(None, self.prefix)
            sys.stdout.write("psanaTestLib - generated random dir %s for tests - set environment variable PSANA_TEST_OUTDIR to override\n" % self.tmpdir)
            self.rm = True
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

