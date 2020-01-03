from __future__ import print_function
from __future__ import absolute_import
from builtins import map
import io
import os
import sys
import time
import glob
import copy
from . import psanaTestLib as ptl
from psmon.plots import Image
from psmon import publish
import socket
import numpy as np

#def createMapFile(mapfile, inputdir, run):
#    assert os.path.exists(inputdir), "no input dir: %s" % inputdir
#    smdFiles = glob.glob(os.path.join(inputdir, "*-r%4.4d*.smd.xtc" % run))
#    assert len(smdFiles)>0, "no smd files"
#    
#def parseSmldDataEventOffsets(inputdir, run):
#    return None

#def setStreamPos(stream2chunkFiles, chunk, offset):
#    stream2next = {}
#    streamsSet = set()
#    for stream, chunkList in stream2chunkFiles.iteritems():
#        for curChunk, chunkfname in chunkList:
#            if chunk==curChunk:
#                stream2next[stream] = (chunk, curfname, offset)
#                streamsSet.add(stream)
#    assert streamsSet == set(stream2chunkFiles.keys()), ("note all" + \
#    "not all streams set. set=%r, but all=%r") % \
#        (streamsSet, set(stream2chunkFiles.keys()))
#    return streamsSet

def indexStreamChunk2fsize(smdFiles):
    stream2chunk = {}
    for smdFile in smdFiles:
        run, stream, chunk = ptl.parseXtcFileName(smdFile)
        if stream not in stream2chunk:
            stream2chunk[stream] = {}
        stream2chunk[stream][chunk] = {'fname':smdFile, 'size':os.stat(smdFile).st_size}
    return stream2chunk

def getSmlDataFiles(inputdir, run, verbose):
    assert os.path.exists(inputdir), "inputdir=%s doesn't exist" % inputdir
    smdFiles = glob.glob(os.path.join(inputdir, '*-r%4.4d*.smd.xtc' % run))
    assert len(smdFiles)>0, ("no smd files found for run=%d inputdir=%s. "+\
        "All files are: %r") % (run, inputdir, 
                                glob.glob(os.path.join(inputdir, '*.xtc')))
    result = indexStreamChunk2fsize(smdFiles)
    if verbose:
        for stream, chunk2fsize in result.items():
            for chunk, finfo in chunk2fsize.items():
                print("stream=%2d chunk=%2d fsize=%.2fMB fname=%s" % \
                    (stream, chunk, finfo['size']/float(1<<20), finfo['fname']))
    return result

class MapFile(object):
    def __init__(self, mapfilename, verbose):
        self.mapfile = open(mapfilename, 'r')
        self.verbose = verbose
        self.lastEventNum, self.lastStreamPos = self.parseLine(self.mapfile.readline())
        assert self.lastEventNum == 0
        for stream, streamPos in self.lastStreamPos.items():
            streamPos['offset']=0
        if verbose:
            print("mapfile initialized with streams: %s" % list(self.lastStreamPos.keys()))

    def parseLine(self, ln):
        stream2pos = {}
        flds = ln.split()
        assert len(flds)%2==0
        assert flds.pop(0) == 'evt='
        eventNum = int(flds.pop(0))
        while len(flds)>0:
            streamChunkEqual = flds.pop(0)
            streamChunk = streamChunkEqual.split('=')[0]
            stream,chunk = list(map(int, streamChunk.split('.')))
            offset = int(flds.pop(0))
            stream2pos[stream]={'chunk':chunk, 'offset':offset}
        return eventNum, stream2pos

    def evt2streamPos(self, eventNum):
        assert eventNum > 0
        assert eventNum >= self.lastEventNum
        if eventNum == self.lastEventNum:
            return self.lastStreamPos
        ln = self.mapfile.readline()
        while len(ln)>0:
            nextEventNum, nextStreamPos = self.parseLine(ln)
            if nextEventNum >= eventNum:
                self.lastEventNum = nextEventNum
                self.lastStreamPos = nextStreamPos
                return nextStreamPos
            ln = self.mapfile.readline()
        return None

    def streams(self):
        return list(self.lastStreamPos.keys())

class FileHandler(object):
    def __init__(self, outputdir, stream2chunk2finfo, verbose):
        self.stream2chunk2finfo = stream2chunk2finfo
        self.outputdir = outputdir
        self.stream2inprogress = {}
        self.verbose = verbose

    def clearOutputDirAndStartChunk0InProgressFiles(self):
        for stream, chunk2finfo in self.stream2chunk2finfo.items():
            for chunk, finfo in chunk2finfo.items():
                fname = finfo['fname']
                fsize = finfo['size']
                basename = os.path.basename(fname)
                outputfile = os.path.join(self.outputdir, basename)
                assert outputfile != fname, "outputfile=%s and fname=%s" % (outputfile, fname)
                inprogress = outputfile + ".inprogress"
                if os.path.exists(outputfile): 
                    os.unlink(outputfile)
                    if self.verbose: print("removed %s" % outputfile)
                if os.path.exists(inprogress): 
                    os.unlink(inprogress)
                    if self.verbose: print("removed %s" % inprogress)
                if chunk == 0:
                    os.system('touch %s' % inprogress)
                    if self.verbose: print("started writing %s" % inprogress)
                    self.stream2inprogress[stream] = {'chunk':chunk,
                                                      'infilename':fname,
                                                      'outinprogress':inprogress,
                                                      'outfinal':outputfile,
                                                      'infile':io.open(fname, 'rb'),
                                                      'outfile':io.open(inprogress, 'wb')}

    def updateChunk(self, stream, oldChunk, newChunk):
        self.stream2inprogress[stream]['chunk'] = newChunk
        oldEnd = '-c%2.2d.smd.xtc' % oldChunk
        newEnd = '-c%2.2d.smd.xtc' % newChunk
        infilename = self.stream2inprogress[stream]['infilename']
        assert infilename.endswith(oldEnd)
        infilename = infilename[0:-len(oldEnd)] + newEnd
        basename = os.path.basename(infilename)
        outfinal = os.path.join(self.outputdir, basename)
        outinprogress = outfinal + '.inprogress'
        self.stream2inprogress[stream]['infilename'] = infilename
        self.stream2inprogress[stream]['outfinal'] = outfinal
        self.stream2inprogress[stream]['outinprogress'] = outinprogress
        del self.stream2inprogress[stream]['infile']
        del self.stream2inprogress[stream]['outfile']
        self.stream2inprogress[stream]['infile'] = io.open(infilename, 'rb')
        self.stream2inprogress[stream]['outfile'] = io.open(outinprogress, 'wb')

    def copyLastBytes(self, stream):
        lastBytesInFile = self.stream2inprogress[stream]['infile'].read()
        self.stream2inprogress[stream]['outfile'].write(lastBytesInFile)
        self.stream2inprogress[stream]['outfile'].close()
        
    def mvInprogressToFinal(self, stream):
        outinprogress = self.stream2inprogress[stream]['outinprogress']
        outfinal = self.stream2inprogress[stream]['outfinal']
        os.system('mv %s %s' % (outinprogress, outfinal))
        assert os.stat(outfinal).st_size == os.stat(self.stream2inprogress[stream]['infilename']).st_size
        if self.verbose: print("moved inprogress to final: %s" % outfinal)

    def copyBlock(self, stream, lastPos, nextPos):
        lastChunk, lastOffset = lastPos['chunk'], lastPos['offset']
        nextChunk, nextOffset = nextPos['chunk'], nextPos['offset']
        if nextChunk != lastChunk:
            assert lastChunk == self.stream2inprogress[stream]['chunk']
            assert lastOffset == self.stream2inprogress[stream]['outfile'].tell()
            assert lastOffset == self.stream2inprogress[stream]['infile'].tell()
            assert nextChunk == lastChunk+1
            self.copyLastBytes(stream)
            self.mvInprogressToFinal(stream)
            self.updateChunk(stream, lastChunk, nextChunk)
            lastChunk = nextChunk
            lastOffset = 0
        assert lastChunk == self.stream2inprogress[stream]['chunk']
        assert lastOffset == self.stream2inprogress[stream]['outfile'].tell()
        assert lastOffset == self.stream2inprogress[stream]['infile'].tell()
        nextBytes = self.stream2inprogress[stream]['infile'].read(nextOffset-lastOffset)
        assert len(nextBytes)==nextOffset-lastOffset
        self.stream2inprogress[stream]['outfile'].write(nextBytes)
        self.stream2inprogress[stream]['outfile'].flush()
        
BEHIND_WARNINGS = 0
def wait(sec):
    if sec <=0: 
        if BEHIND_WARNINGS == 20:
            print("falling behind, not waiting (last warning)")
        elif BEHIND_WARNINGS < 20:
            print("falling behind, not waiting")
        return
    time.sleep(sec)

def smallDataMover(inputdir, outputdir, run, numEventsToWrite, rate, mapfilename, verbose):
    stream2chunk2finfo = getSmlDataFiles(inputdir, run, verbose)

    mapFile = MapFile(mapfilename, verbose)
    streams = mapFile.streams()
    assert set(streams)==set(stream2chunk2finfo.keys())

    fileHandler = FileHandler(outputdir, stream2chunk2finfo, verbose)
    fileHandler.clearOutputDirAndStartChunk0InProgressFiles()
    
    nextEvent = rate
    stream2lastPos = mapFile.lastStreamPos
    stream2nextPos = mapFile.evt2streamPos(nextEvent)
    
    earlyEnd = False

    if verbose:
        print("enter: psplot -s %s EVTCOUNTER" % socket.gethostname())

    while (stream2nextPos is not None):
        t0 = time.time()
        for stream, nextPos in stream2nextPos.items():
            fileHandler.copyBlock(stream, stream2lastPos[stream], nextPos)
        if verbose:
            print("copied stream blocks to about event=%8d" % nextEvent)
            img = Image(nextEvent, "EventCounter", np.zeros((2,2)))
            publish.send("EVTCOUNTER", img)
        if ((numEventsToWrite > 0) and (numEventsToWrite < nextEvent)): 
            earlyEnd = True
            break
        stream2lastPos = stream2nextPos
        nextEvent += rate
        stream2nextPos = mapFile.evt2streamPos(nextEvent)
        wait(t0 + 1.0 - time.time())
    
    for stream in mapFile.streams():
        if not earlyEnd:
            fileHandler.copyLastBytes(stream)
        fileHandler.mvInprogressToFinal(stream)
        
