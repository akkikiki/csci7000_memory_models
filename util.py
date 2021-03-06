from collections import defaultdict
from itertools import count
import mmap
import six

class Vocab:
    def __init__(self, w2i=None):
        if w2i is None: w2i = defaultdict(count(0).next)
        self.w2i = dict(w2i)
        self.i2w = {i:w for w,i in w2i.items()}
    @classmethod
    def from_corpus(cls, corpus):
        counter = count(0)
        w2i = defaultdict(lambda: six.next(counter))
        for sent in corpus:
            [w2i[word] for word in sent]
        return Vocab(w2i)

    def size(self): return len(self.w2i.keys())

#This corpus reader can be used when reading large text file into a memory can solve IO bottleneck of training.
#Use it exactly as the regular CorpusReader from the rnnlm.py
class FastCorpusReader:
    def __init__(self, fname):
        self.fname = fname
        self.f = open(fname, 'rb')
    def __iter__(self):
        #This usage of mmap is for a Linux\OS-X 
        #For Windows replace prot=mmap.PROT_READ with access=mmap.ACCESS_READ
        m = mmap.mmap(self.f.fileno(), 0, prot=mmap.PROT_READ)
        data = m.readline()
        while data:
            line = data
            data = m.readline()
            line = line.lower()
            line = line.strip().split()
            yield line    
    
class CorpusReader:
    def __init__(self, fname):
        self.fname = fname
    def __iter__(self):
        for line in file(self.fname):
            #line = line.strip().split()
            line = [c for c in line.strip()] # Char level
            #line = [' ' if x == '' else x for x in line]
            yield line

class CharsCorpusReader:
    def __init__(self, fname, begin=None):
        self.fname = fname
        self.begin = begin
    def __iter__(self):
        begin = self.begin
        for line in open(self.fname):
            line = list(line)
            if begin:
                line = [begin] + line
            yield line
