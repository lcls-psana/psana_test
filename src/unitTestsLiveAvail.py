#--------------------------------------------------------------------------
# Description:
#   Test script for psana_test
#   
#------------------------------------------------------------------------


#--------------------------------
#  Imports of standard modules --
#--------------------------------
import sys
import os
import glob
import tempfile
import unittest
import psana
import time
import shutil
import psana_test.psanaTestLib as ptl

from AppUtils.AppDataPath import AppDataPath

DATADIR = ptl.getTestDataDir()
OUTDIR = ptl.getDataArchDir(pkg='psana_test', datasubdir='test_output')


def getH5OutfileName(path):
    basename = os.path.basename(path)
    h5basename = os.path.splitext(basename)[0] + '.h5'
    return os.path.join(OUTDIR,h5basename)

#-------------------------------
#  Unit test class definition --
#-------------------------------
class LiveAvail( unittest.TestCase ) :

    def setUp(self) :
    	""" 
    	Method called to prepare the test fixture. This is called immediately 
    	before calling the test method; any exception raised by this method 
    	will be considered an error rather than a test failure.  
    	"""
        assert os.path.exists(DATADIR), "Data dir: %s does not exist, cannot run unit tests" % DATADIR
        assert os.path.exists(OUTDIR), "Output directory: %s does not exist, can't run unit tests" % OUTDIR
        self.cleanUp = True    # delete intermediate files if True
        self.verbose = False    # print psana output, ect

        expname = 'sxrh4315'
        run = 128
        srcDir = os.path.join(ptl.getMultiFileDataDir(), 'test_018_%s' % expname)
        srcSmallDataDir = os.path.join(srcDir, 'smalldata')
        assert os.path.exists(srcSmallDataDir), "srcSmallDataDir=%s doesn't exist" % \
            srcSmallDataDir
        self.srcDataset = 'exp=%s:run=%d:smd:dir=%s' % \
                          (expname, run, srcDir)

        destDirBase = ptl.getDataArchDir(pkg='psana_test', 
                                         datasubdir='test_output', 
                                         archsubdir='liveModeSim')

        # make a random directory for the testing that we will remove when done
        destDir = os.path.join(destDirBase, 'outdir')  #tempfile.mkdtemp(dir=destDirBase)
        if not os.path.exists(destDir):
            os.mkdir(destDir)
        destSmallDataDir = os.path.join(destDir, 'smalldata')
        if not os.path.exists(destSmallDataDir):
            os.mkdir(destSmallDataDir)
        mapfile = os.path.join(destDir, "test_018.mapfile")
        cmd = "makeMapFileForPsanaTestSmlDataMover -d %s -m %s" % \
              (self.srcDataset, mapfile)
        if not os.path.exists(mapfile):
            stdout, stderr = ptl.cmdTimeOut(cmd)

            self.assertTrue(os.path.exists(mapfile))
            self.assertTrue(stderr.strip()=='')

        self.destDataset = 'exp=%s:run=%d:smd:live:dir=%s' % \
                      (expname, run, destDir)

        self.moverCmd = 'psanaTestSmlDataMover -m %s -i %s -o %s -r %d  --hertz 120' % \
                        (mapfile, srcSmallDataDir, destSmallDataDir, run)
        
        for fname in glob.glob(os.path.join(destSmallDataDir, '*')):
            os.unlink(fname)

    def tearDown(self) :
        """
        Method called immediately after the test method has been called and 
        the result recorded. This is called even if the test method raised 
        an exception, so the implementation in subclasses may need to be 
        particularly careful about checking internal state. Any exception raised 
        by this method will be considered an error rather than a test failure. 
        This method will only be called if the setUp() succeeds, regardless 
        of the outcome of the test method. 
        """
        pass

    def testLiveAvail(self):
        '''Test that liveAvail works
        '''

        print self.moverCmd
        os.system("%s&" % self.moverCmd)

        ########### LiveAvail Usage Below #############
        liveAvail = psana.LiveAvail()
        ds = psana.DataSource(self.destDataset, module=liveAvail)
        skipped = 0
        processed = 0
        delay = 0.009  # we should definitely fall behind and need to skip
        for evt in ds.events():
            if liveAvail.toFarBehind(): 
                skipped += 1
                continue
            time.sleep(delay)
            processed += 1

        print "finished liveAvail loop with processing delay of %.3f" % delay
        print "skipped=%d processed=%d total=%d" % (skipped, processed, skipped + processed)
        self.assertEqual(processed+skipped, 2338, msg='expected 2338 events in test data, but got %d' % (processed+skipped))
        self.assertGreater(skipped, 0, msg="with delay of 9ms, should have skipped some events?")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], '-v'])

