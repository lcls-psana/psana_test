from __future__ import print_function
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

TESTDATADIR = ptl.getTestDataDir()
MULTIDATADIR = ptl.getMultiFileDataDir()

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
        assert os.path.exists(TESTDATADIR), "Data dir: %s does not exist, cannot run unit tests" % TESTDATADIR
        assert os.path.exists(MULTIDATADIR), "Data dir: %s does not exist, cannot run unit tests" % MULTIDATADIR
        self.outputDir = tempfile.mkdtemp()
        self.cleanUp = True    # delete intermediate files if True
        self.verbose = False   # print psana output, ect

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

    def test_smlDataDamageContributed(self):
        '''
        JIRA PSAS-237 - the contributed damage was
        causing smldata problems
        '''
        testdir = os.path.join(MULTIDATADIR, 'test_030_amoc0113')
        xtc = os.path.join(testdir, 'e331-r0071-s05-c00.xtc')
        assert os.path.exists(xtc), "testfile: %s doesn't exist" % xtc
        xtcdir = os.path.join(self.outputDir, "contrib_damage")
        smldatadir = os.path.join(xtcdir, 'smalldata')
        if not os.path.exists(xtcdir):
            os.mkdir(xtcdir)
        if not os.path.exists(smldatadir):
            os.mkdir(smldatadir)
        try:
            os.symlink(xtc, os.path.join(xtcdir, os.path.basename(xtc)))
        except OSError:
            pass
        smloutput = os.path.join(smldatadir, 'e331-r0071-s05-c00.smd.xtc')
        cmd = 'smldata -f %s -o %s' % (xtc, smloutput)
        stdout, stderr = ptl.cmdTimeOut(cmd)
        assert stderr.strip()=='', "error with cmd=%s err=%s" % (cmd, stderr)
        cmd = 'psana -n 3 -m psana_test.dump '
        cmd += 'exp=amoc0113:run=71:smd:dir=%s' % xtcdir
        stdout, stderr = ptl.cmdTimeOut(cmd)
        self.assertTrue(stderr.strip()=='', msg="error from cmd = %s, err=%s" % (cmd, stderr))

    def test_smldata(self):
        def write2file(fname, txt):
            f = open(fname,'w')
            f.write(txt)
            f.close()

        def fmtErr(cmd, stdout, stderr):
            msg = "== error ==\n"
            msg += "cmd: %s\n" % cmd
            if stdout:
                msg += "== stdout ==\n"
                msg += stdout
                msg += '\n'
            if stderr:
                msg += "== stderr ==\n"
                msg += stderr
                msg += '\n'
            return msg
        xtcs = glob.glob(os.path.join(TESTDATADIR, "test_*_*.xtc"))
        smdbases = [os.path.basename(xtc)[0:-3] + "smd.xtc" for xtc in xtcs]
        try:
            os.mkdir(os.path.join(self.outputDir, "smalldata"))
        except OSError:
            pass
        lastTestTime = 0.0
        testsWithSameEventKeys = [0,2,13, 90]
        testsWithDifferentEventKeys = [62,65,91]  # 90 and 91 are meck test files,
        tests2do = testsWithSameEventKeys + testsWithDifferentEventKeys
        # 91 is 90 but with damage added to a later dgram
        for xtc, smdbase in zip(xtcs, smdbases):
            testNo = int(os.path.basename(xtc).split("_")[1])
            if testNo not in tests2do: continue
            # make soft link to process small data proxys
            try:
                os.symlink(xtc, os.path.join(self.outputDir, os.path.basename(xtc)))
            except OSError:
                pass
            smdpath = os.path.join(self.outputDir, "smalldata", smdbase)
            sys.stdout.write("==== last time=%.2f sec, testing %s ====\n" % (lastTestTime, smdpath))
            sys.stdout.flush()
            t0 = time.time()
            evKeysOrigCmd = "psana -m PrintEventId,EventKeys %s" % xtc
            smlDataCmd = "smldata -f %s -o %s" % (xtc, smdpath)
            evKeysSmdCmd = "psana -m PrintEventId,EventKeys %s | grep -v SmlData::ConfigV1" % smdpath
            evKeysOrigOut, evKeysOrigErr = ptl.cmdTimeOut(evKeysOrigCmd)
            smlDataOut,    smlDataErr    = ptl.cmdTimeOut(smlDataCmd)
            evKeysSmdOut,  evKeysSmdErr  = ptl.cmdTimeOut(evKeysSmdCmd)
            evKeysOrigErr = '\n'.join([ln for ln in evKeysOrigErr.split('\n') if not ptl.filterPsanaStderr(ln)])
            evKeysSmdErr  = '\n'.join([ln for ln in evKeysSmdErr.split('\n')  if not ptl.filterPsanaStderr(ln)])
            self.assertEqual(evKeysOrigErr.strip(), "", msg=fmtErr(evKeysOrigCmd, evKeysOrigOut, evKeysOrigErr))
            self.assertEqual(smlDataErr.strip(), "", msg=fmtErr(smlDataCmd, smlDataOut, smlDataErr))
            self.assertEqual(evKeysSmdErr.strip(),"", msg=fmtErr(evKeysSmdCmd, evKeysSmdOut, evKeysSmdErr))
            evKeysXtcOutFname = os.path.join(self.outputDir, "test_%3.3d_evKeys_xtc.out" % testNo)
            evKeysSmdOutFname = os.path.join(self.outputDir, "test_%3.3d_evKeys_smd.out" % testNo)
            write2file(evKeysXtcOutFname, evKeysOrigOut)
            write2file(evKeysSmdOutFname, evKeysSmdOut)
            diffout, differr = ptl.cmdTimeOut("diff -u %s %s" % (evKeysXtcOutFname, evKeysSmdOutFname))
            if testNo in testsWithSameEventKeys:
                self.assertEqual(diffout, "", msg="evKeys output differ. dir=%s:\n%s" % (self.outputDir, diffout))
            elif diffout != '':
                print("== diffout error ==")
                print(diffout)
            lastTestTime = time.time()-t0

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0], '-v'])
