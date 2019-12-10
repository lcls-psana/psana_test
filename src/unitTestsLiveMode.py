from __future__ import print_function
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
from psana_test.TestOutputDir import outputDir

DATADIR = ptl.getTestDataDir()


#-------------------------------
#  Unit test class definition --
#-------------------------------
class LiveMode( unittest.TestCase ) :

    def setUp(self) :
        """
        Method called to prepare the test fixture. This is called immediately
        before calling the test method; any exception raised by this method
        will be considered an error rather than a test failure.
        """
        assert os.path.exists(DATADIR), "Data dir: %s does not exist, cannot run unit tests" % DATADIR
        self.cleanUp = True    # delete intermediate files if True
        self.verbose = False    # print psana output, ect

        self.expname = 'sxrh4315'
        self.run = 128
        srcDir = os.path.join(ptl.getMultiFileDataDir(), 'test_018_%s' % self.expname)
        self.srcSmallDataDir = os.path.join(srcDir, 'smalldata')
        assert os.path.exists(self.srcSmallDataDir), "srcSmallDataDir=%s doesn't exist" % \
            self.srcSmallDataDir
        self.srcDataset = 'exp=%s:run=%d:smd:dir=%s' % \
                          (self.expname, self.run, srcDir)

        self.outdir = outputDir('psliv')

    def setupWithinContext(self):
        Base = self.outdir.make_subdir('liveModeSim')
        destDir = self.outdir.make_subdir('destdir')
        destSmallDataDir = self.outdir.make_subdir(os.path.join(destDir, 'smalldata'))
        mapfile = os.path.join(destDir, "test_018.mapfile")
        cmd = "makeMapFileForPsanaTestSmlDataMover -d %s -m %s" % \
              (self.srcDataset, mapfile)
        if not os.path.exists(mapfile):
            stdout, stderr = ptl.cmdTimeOut(cmd)

            self.assertTrue(os.path.exists(mapfile))
            self.assertTrue(stderr.strip()=='')

        self.destDataset = 'exp=%s:run=%d:smd:live:dir=%s' % \
                      (self.expname, self.run, destDir)

        self.moverCmdWithoutRate = 'psanaTestSmlDataMover -m %s -i %s -o %s -r %d' % \
                                   (mapfile, self.srcSmallDataDir, destSmallDataDir, self.run)

        for fname in glob.glob(os.path.join(destSmallDataDir, '*')):
            os.unlink(fname)

        self.destDir = destDir

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
        '''Test that liveAvail works. Sleep enough with each event to skip some to keep up.
        '''
        with self.outdir:
            self.setupWithinContext()
            print(self.moverCmdWithoutRate)
            os.system("%s --hertz 120&" % self.moverCmdWithoutRate)

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

            print("finished liveAvail loop with processing delay of %.3f" % delay)
            print("skipped=%d processed=%d total=%d" % (skipped, processed, skipped + processed))
            self.assertEqual(processed+skipped, 2338, msg='expected 2338 events in test data, but got %d' % (processed+skipped))
            self.assertGreater(skipped, 0, msg="with delay of 9ms, should have skipped some events?")

    def testLiveDeadSameOrder(self):
        '''check that the live and dead give the same order for events.
        '''
        with self.outdir:
            self.setupWithinContext()
            t0 = time.time()
            ds = psana.DataSource(self.srcDataset)
            deadEventTimes = []
            for evt in ds.events():
                evtId = evt.get(psana.EventId)
                if evtId is not None:
                    deadEventTimes.append(str(evtId))
            print("finished dead dset=%s in %.2f sec #events=%d" % (self.srcDataset,
                                                                     time.time()-t0,
                                                                     len(deadEventTimes)))

            os.system("%s --hertz 500&" % self.moverCmdWithoutRate)
            t0 = time.time()
            ds = psana.DataSource(self.destDataset)
            liveEventTimes = []
            for evt in ds.events():
                evtId = evt.get(psana.EventId)
                if evtId is not None:
                    liveEventTimes.append(str(evtId))
            print("finished live: dset=%s in %.2f sec #events=%d" % (self.destDataset,
                                                                     time.time()-t0,
                                                                     len(liveEventTimes)))


            self.assertEqual(len(liveEventTimes), len(deadEventTimes),
                             msg="live and dead event time lengths differ")
            for liveTm, deadTm in zip(liveEventTimes, deadEventTimes):
                self.assertEqual(liveTm, deadTm)

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], '-v'])

