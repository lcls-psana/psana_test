import re
from psana import DgramList
from XtcInput.PyDgramListUtil import xtcFileNameStreamChunk, getDgramInfo

class MapFile(object):
    '''psana module to produce map file of offsets into each stream
    for each event. Used for testing with psanaTestSmlDataMover
    '''
    def __init__(self, mapfilename):
        self.mapfile = open(mapfilename,'w')
        self.stream2pos = {}
        self._eventNumber = -1

    def beginrun(self, evt, env):
        file2offset = getDgramInfo(evt)
        for fname in file2offset.keys():
            stream, chunk = xtcFileNameStreamChunk(fname)
            self.stream2pos[stream] = (chunk,0)

    def event(self, evt, env):
        self._eventNumber += 1

        fname2offset = getDgramInfo(evt)

        for fname, offset in fname2offset.items():
            stream, chunk = xtcFileNameStreamChunk(fname)
            curChunk, curOffset = self.stream2pos[stream]
            if chunk == curChunk:
                self.stream2pos[stream] = (chunk, max(offset, curOffset))
            else:
                self.stream2pos[stream] = (chunk, offset)
        
        ln = 'evt= %10d' % self._eventNumber
        streams = list(self.stream2pos.keys())
        streams.sort()
        for stream in streams:
            chunk, offset = self.stream2pos[stream]
            ln += '   %d.%d=  %d' % (stream, chunk, offset)
        self.mapfile.write("%s\n" % ln)

