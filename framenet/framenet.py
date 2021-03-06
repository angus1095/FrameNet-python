from settings import *


def loadXMLAttributes(d, attributes):
    for attr in attributes.keys():
        sattr = str(attr)
        val = attributes[attr].value
        try:
            sval = str(val)
            if sval.isdigit():
                d[sattr] = int(sval)
            else:
                d[sattr] = sval
        except:
            d[sattr] = val
    return d

def getNoneTextChildNodes(xmlNode):
    """
    """

    return filter(lambda x:x.nodeType != x.TEXT_NODE, xmlNode.childNodes)

def testLU(fileName):
    a = LexicalUnit()

    try:
        if not a.loadXML(FRAMENET_PATH+"/"+LU_DIR_ENV+"/"+fileName):
            print >> sys.stderr, 'loading:', fileName, 'failed'
    except:
        print >> sys.stderr, 'loading:', fileName, 'failed'
    print a.getLexemes()
    return a


def initialize():
     """
     """

     fn = FrameNet()
     fn.initialize()

     pass

from lexical_unit import LexicalUnit
from frame import Frame
from frame_relation import FrameRelation

     
class FrameNet(dict):
    """
    This the master class for FrameNet
    """

    def __init__(self):
        """
        Constructor, loads the frames and the frame relations.
        """
        pickledFramePath = FRAMENET_PATH + '/' + PICKLED_FRAME_FILE
        pickledFrameRelationPath = FRAMENET_PATH  + '/' + PICKLED_FRAME_RELATIONS_FILE
        pickledLUPath = FRAMENET_PATH + '/' + PICKLED_LU_FILE
            
        try:
            print >> sys.stderr, 'Loading the frames ...',
            frames = cPickle.load(open(pickledFramePath))
            self['frames'] = frames
            print >> sys.stderr, 'done'
            
            print >> sys.stderr, 'Loading the frame relations ...',
            frRelations = cPickle.load(open(pickledFrameRelationPath))
            self['frameRelations'] = frRelations
            print >> sys.stderr, 'done'

            print >> sys.stderr, 'Loading the lexical units data ...',
            luData = cPickle.load(open(pickledLUPath))
            print >> sys.stderr, 'done'
            self['luIndex'] = luData
            
        except:
            print >> sys.stderr, 'Framenet not initialized, doing it now'
            self.initialize()
            print >> sys.stderr, 'Loading the frames ...',
            frames = cPickle.load(open(pickledFramePath))
            self['frames'] = frames
            print >> sys.stderr, 'done'
            
            print >> sys.stderr, 'Loading the frame relations ...',
            frRelations = cPickle.load(open(pickledFrameRelationPath))
            self['frameRelations'] = frRelations
            print >> sys.stderr, 'done'
            
            print >> sys.stderr, 'Loading the lexical units data ...',
            luData = cPickle.load(open(pickledLUPath))
            print >> sys.stderr, 'done'
            self['luIndex'] = luData

        self['luCache'] = {}
        self._generateFrameIndex()
        pass


    def _generatePickledFrames(self):
        """
        Initialises all the frames
        """

        framePath = FRAMENET_PATH+ '/' + FRAME_DIR_ENV + '/' + FRAME_FILE
        pickledFramePath = FRAMENET_PATH + '/' + PICKLED_FRAME_FILE

        print >> sys.stderr, 'Loading xml for frames ...',
        doc = xml.dom.minidom.parse(framePath)
        frameNodes = getNoneTextChildNodes(doc.childNodes[1])
        print >> sys.stderr, 'done',
        
        frames = {}
        print >> sys.stderr, 'parsing each frame ...',
        for fn in frameNodes:
            f = Frame()
            f.loadXMLNode(fn)
            frames[f['ID']] = f
        print >> sys.stderr, 'done',

        print >> sys.stderr, 'saving the frames ...',
        cPickle.dump(frames, open(pickledFramePath, 'w'), cPickle.HIGHEST_PROTOCOL)
        print >> sys.stderr, 'done'

        pass

    def _generatePickledFrameRelations(self):
        """
        Initialises all the frames
        """

        frRelationPath = FRAMENET_PATH + '/' + FRAME_DIR_ENV + '/' + FRAME_RELATION_FILE
        pickledFrameRelationPath = FRAMENET_PATH + '/' + PICKLED_FRAME_RELATIONS_FILE

        print >> sys.stderr, 'Loading xml for frame relations ...',
        frRelations = FrameRelation()
        frRelations.loadXML(frRelationPath)
        print >> sys.stderr, 'done',
        
        print >> sys.stderr, 'saving the frame relationships ...',
        cPickle.dump(frRelations, open(pickledFrameRelationPath, 'w'), cPickle.HIGHEST_PROTOCOL)
        print >> sys.stderr, 'done'

        pass


    def _generatePickledLexicalUnitsIndex(self):
        """
        Initialises all the frames
        """

        baseDir = FRAMENET_PATH + '/' + LU_DIR_ENV
        pickledLUPath = FRAMENET_PATH + '/' + PICKLED_LU_FILE

        lexicalUnitsIndexByName = {}
        for _f in os.listdir(baseDir):
            if _f.lower().startswith('lu') and _f.lower().endswith('.xml'):
                print >> sys.stderr, 'Loading:', _f, ": ",
                lu = LexicalUnit()
                lu.loadXML(baseDir + '/' + _f)
                print >> sys.stderr, lu['name'], '...', 
                print >> sys.stderr, 'done'

                if lexicalUnitsIndexByName.has_key(lu['name']):
                    lexicalUnitsIndexByName[lu['name']][lu['ID']] = 1
                else:
                    lexicalUnitsIndexByName[lu['name']] = {lu['ID']:1}

        print >> sys.stderr, 'Saving the pickled lu files ...',
        cPickle.dump(lexicalUnitsIndexByName, open(pickledLUPath, 'w'), cPickle.HIGHEST_PROTOCOL)
        print >> sys.stderr, 'done'
        pass

    def _generateFrameIndex(self):
        """
        Generate an index from frame name to Frame objects
        """

        self['frameIndex'] = {}

        for _id in self['frames'].keys():
            f = self['frames'][_id]
            name = f['name']
            if self['frameIndex'].has_key(name):
                print >> sys.stderr, 'Error, multiple frame name:', name, 'found'
                sys.exit()

            self['frameIndex'][name] = f

        pass

    def initialize(self):
        """
        This function should be called only once before the whole thing can be used.
        """
        self._generatePickledFrames()
        self._generatePickledFrameRelations()
        self._generatePickledLexicalUnitsIndex()

        return True


    def lookupLexicalUnit(self, headWord, pos):
        """
        This function will look up a given word by its pos. The word must be already
        lemmatised and in lower case. The pos must also be in lower case and it can be
        one of the following:
        (1) v  -- for verb
        (2) n  -- for noun
        (3) a  -- for adjective
        (4) adv -- for adverb
        (5) prep -- for preposition
        (6) num -- for numbers
        (7) intj -- for interjections

        This function will return a dictionary of lexical units which match the (headWord, pos)
        pair. The keys to the dictionary will be the IDs of the lexical units, and the values of
        the dictionary will be LexicalUnit objects.
        """

        pickledLUPath = FRAMENET_PATH + '/' + LU_DIR_ENV

        w = headWord + '.' + pos

        if self['luCache'].has_key(w):
            return self['luCache'][w]
        
        if not self['luIndex'].has_key(w):
            return {}

        objects = {}
        for _id in self['luIndex'][w].keys():
            inputFile = pickledLUPath + '/lu' + str(_id) + '.xml'
            lu = LexicalUnit()
            lu.loadXML(inputFile)
            objects[lu['ID']] = lu

        self['luCache'][w] = objects
        return objects

    def getFrameGraph(self, frameText):
        import networkx as nx
        frame = self.lookupFrame(frameText)
        g = nx.DiGraph()
        frame_ids = frame.keys()
        for relations in self['frameRelations']['relation-types'].values():
            relationName = relations['name']
            superFrameName = relations['superFrameName']
            childFrameName = relations['subFrameName']
            rels = relations['frame-relations']
            print "Loading", relationName, superFrameName, childFrameName
            for frame_id in frame_ids:
                if True:
                #for k,rel in rels.items():
                    for k2, rel2 in rels.items():
                        if rel2['subFrameName'] == frame['name']:
                            print rel2
                    
                        if rel2['ID'] == frame_id:
                            print "MATCH ON ID"
                            print rel2['subFrameName']
                        if int(rel2['subId']) == frame_id:
                            print rel2
                        elif int(rel2['supId']) == frame_id:
                            print rel2


    def lookupFrame(self, frame):
        """
        This function takes a string as input, the string should be the name
        of the Frame that you want to lookup, and its case sensitive. If not
        found, None will be returned.
        """

        if self['frameIndex'].has_key(frame):
            return self['frameIndex'][frame]

        return None

#----------------------------------------------------------------------------
