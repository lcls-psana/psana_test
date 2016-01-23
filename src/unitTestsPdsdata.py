#--------------------------------------------------------------------------
# Description:
#   Test script for pdsdata
#   
#------------------------------------------------------------------------


#--------------------------------
#  Imports of standard modules --
#--------------------------------
import sys
import os
import unittest
import psana_test.psanaTestLib as ptl
import tempfile
import shutil
import glob
import time

DATADIR = ptl.getTestDataDir()
OUTDIR = ptl.getDataArchDir(pkg='psana_test', datasubdir='test_output')

#-------------------------------
#  Unit test class definition --
#-------------------------------
class Pdsdata( unittest.TestCase ) :

    def setUp(self) :
    	""" 
    	Method called to prepare the test fixture. This is called immediately 
    	before calling the test method; any exception raised by this method 
    	will be considered an error rather than a test failure.  
    	"""
        assert os.path.exists(DATADIR), "Data dir: %s does not exist, cannot run unit tests" % DATADIR
        assert os.path.exists(OUTDIR), "Output directory: %s does not exist, can't run unit tests" % OUTDIR
        self.outputDir = tempfile.mkdtemp(dir=OUTDIR)
        self.cleanUp = False#True    # delete intermediate files if True
        self.verbose = True #False    # print psana output, ect

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
        if self.cleanUp:
            shutil.rmtree(self.outputDir)

    def test_smldata(self):
        def write2file(fname, txt):
            f = file(fname,'w')
            f.write(txt)
            f.close()

        xtcs = glob.glob(os.path.join(DATADIR, "test_*_*.xtc"))
        smdbases = [os.path.basename(xtc)[0:-3] + "smd.xtc" for xtc in xtcs]
        os.mkdir(os.path.join(self.outputDir, "smalldata"))
        lastTestTime = 0.0
        tests2do =  [0,2,13]
        for xtc, smdbase in zip(xtcs, smdbases):
            testNo = int(os.path.basename(xtc).split("_")[1])
            if testNo not in tests2do: continue
            # make soft link to process small data proxys
            os.symlink(xtc, os.path.join(self.outputDir, os.path.basename(xtc)))
            smdpath = os.path.join(self.outputDir, "smalldata", smdbase)
            sys.stdout.write("==== last time=%.2f sec, testing %s ====\n" % (lastTestTime, smdpath))
            sys.stdout.flush()
            t0 = time.time()
            evKeysOrigOut, evKeysOrigErr = ptl.cmdTimeOut("psana -m EventKeys %s" % xtc)
            smlDataOut,    smlDataErr    = ptl.cmdTimeOut("smldata -f %s -o %s" % (xtc, smdpath))
            evKeysSmdOut, evKeysSmdErr   = ptl.cmdTimeOut("psana -m EventKeys %s | grep -v SmlData::ConfigV1" % smdpath)
            evKeysOrigErr = '\n'.join([ln for ln in evKeysOrigErr.split('\n') if not ptl.filterPsanaStderr(ln)])
            evKeysSmdErr  = '\n'.join([ln for ln in evKeysSmdErr.split('\n')  if not ptl.filterPsanaStderr(ln)])
            self.assertEqual(evKeysOrigErr.strip(), "", msg="error in evKeys:\n%s" % evKeysOrigErr)
            self.assertEqual(smlDataErr.strip(), "", msg="error in smldata cmd:\n%s" % smlDataErr)
            self.assertEqual(evKeysSmdErr.strip(),"", msg="error in smd evKeys\n%s" % evKeysSmdErr)
            evKeysXtcOutFname = os.path.join(self.outputDir, "test_%3.3d_evKeys_xtc.out" % testNo)
            evKeysSmdOutFname = os.path.join(self.outputDir, "test_%3.3d_evKeys_smd.out" % testNo)
            write2file(evKeysXtcOutFname, evKeysOrigOut)
            write2file(evKeysSmdOutFname, evKeysSmdOut)
            diffout, differr = ptl.cmdTimeOut("diff -u %s %s" % (evKeysXtcOutFname, evKeysSmdOutFname))
            self.assertEqual(diffout, "", msg="evKeys output differs:\n%s" % diffout)
            lastTestTime = time.time()-t0
