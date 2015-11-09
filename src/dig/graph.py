#!/usr/bin/env python

from collections import defaultdict
from collections import namedtuple
import json
from queue import Queue
import re
import sys, os
from pprint import pprint

from Levenshtein import distance
# from StringMatcher import distance
# from Levenshtein.StringMatcher import distance
from networkx import Graph, DiGraph

from SteinerTree import make_steiner_tree
from hybridJaccard import HybridJaccard

LEAF_VOCAB_CACHE = "/Users/philpot/Documents/project/graph-keyword-search/src/dig/data/cache"

def loadLeafVocab(pathdesc, root=LEAF_VOCAB_CACHE):
    pathname = os.path.join(root, pathdesc  + ".json")
    with open(pathname, 'r') as f:
        j = json.load(f)
    # dict of (value, count)
    byCount = sorted([(v,q) for (q,v) in j['histo'].items()], reverse=True)
    return [t[1] for t in byCount]

def localPath(suffix):
    return os.path.join(os.path.dirname(__file__), suffix)

# http://stackoverflow.com/a/9283563/2077242
def camelCaseWords(label):
    label = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', label)
    return label

class KGraph(DiGraph):
    def __init__(self):
        super(KGraph, self).__init__()

    def __str__(self):
        return "<{} {} nodes {} edges>".format(type(self).__name__,
                                               self.number_of_nodes(),
                                               self.number_of_edges())

    def maybe_add_edge(self, root, node1, node2, rootScope=None, **kwargs):
        if rootScope == None:
            rootScope = []
        print("root {}, root scope {}".format(root, rootScope))
        if root in rootScope:
            print(">> for {}, add link between {} and {}".format(root, node1, node2))
            self.add_edge(node1, node2, **kwargs)

    def installDomain(self, root, domainType=None):
        if domainType == 'ht':
            allRoots = ['seller', 'phone', 'email', 'offer', 'adultservice', 'webpage']
            self.add_node('seller', nodeType='Class', className='PersonOrOrganization', indexRoot='seller')
        
            self.add_node('phone', nodeType='Class', className='PhoneNumber', indexRoot='phone')
            self.maybe_add_edge(root, 'seller', 'phone', edgeType='ObjectProperty', relationName='telephone', 
                                rootScope=['seller', 'offer', 'adultservice', 'webpage'])
            self.maybe_add_edge(root, 'phone', 'seller', edgeType='ObjectProperty', relationName='owner', 
                                rootScope=['phone'])
        
            self.add_node('phone.name', nodeType='leaf', vocabDescriptor='seller_telephone_name')
            self.add_edge('phone', 'phone.name', edgeType='DataProperty', relationName='name')
        
            self.add_node('email', nodeType='Class', className='EmailAddress', indexRoot='email')
            self.maybe_add_edge(root, 'seller', 'email', edgeType='ObjectProperty', relationName='email', 
                                rootScope=['seller', 'email', 'offer', 'adultservice', 'webpage'])
            self.maybe_add_edge(root, 'email', 'seller', edgeType='ObjectProperty', relationName='owner', 
                                rootScope=['email'])
            # for now this ES query doesn't work
            # self.add_node('email.name', nodeType='leaf', values=loadLeafVocab('seller_email_name'), vocabDescriptor='seller_email_name')
            # so use flat data instead
            self.add_node('email.name', nodeType='leaf', vocabDescriptor='email_name')
            self.add_edge('email', 'email.name', edgeType='DataProperty', relationName='name')
        
            self.add_node('offer', nodeType='Class', className='Offer', indexRoot='offer')
            self.maybe_add_edge(root, 'offer', 'seller', edgeType='ObjectProperty', relationName='seller', 
                                rootScope=allRoots)
            self.maybe_add_edge(root, 'seller', 'offer', edgeType='ObjectProperty', relationName='makesOffer', 
                                rootScope=allRoots)
        
            self.add_node('priceSpecification', nodeType='Class', className='PriceSpecification')
            self.add_node('priceSpecification.billingIncrement', nodeType='leaf', vocabDescriptor='offer_priceSpecification_billingIncrement')
            self.add_edge('priceSpecification', 'priceSpecification.billingIncrement', edgeType='DataProperty', relationName='billingIncrement')
            self.add_node('priceSpecification.price', nodeType='leaf', vocabDescriptor='offer_priceSpecification_price')
            self.add_edge('priceSpecification', 'priceSpecification.price', edgeType='DataProperty', relationName='price')
            self.add_node('priceSpecification.name', nodeType='leaf', vocabDescriptor='offer_priceSpecification_name')
            self.add_edge('priceSpecification', 'priceSpecification.name', edgeType='DataProperty', relationName='name')
            self.add_node('priceSpecification.unitCode', nodeType='leaf', vocabDescriptor='offer_priceSpecification_unitCode')
            self.add_edge('priceSpecification', 'priceSpecification.unitCode', edgeType='DataProperty', relationName='unitCode')

            self.maybe_add_edge(root, 'offer', 'priceSpecification', edgeType='ObjectProperty', relationName='priceSpecification', 
                                rootScope=allRoots)

            self.add_node('adultservice', nodeType='Class', className='AdultService', indexRoot='adultservice')
            self.add_node('adultservice.eyeColor', nodeType='leaf', 
                           vocabDescriptor='adultservice_eyeColor', 
                           matcherDescriptor=HybridJaccard(ref_path=localPath("data/config/hybridJaccard/eyeColor_reference_wiki.txt"), 
                                                           config_path=localPath("data/config/hybridJaccard/eyeColor_config.txt")))
            self.add_edge('adultservice', 'adultservice.eyeColor', edgeType='DataProperty', relationName='eyeColor')
            
            self.add_node('adultservice.hairColor', nodeType='leaf', 
                           vocabDescriptor='adultservice_hairColor', 
                           matcherDescriptor=HybridJaccard(ref_path=localPath("data/config/hybridJaccard/hairColor_reference_wiki.txt"), 
                                                           config_path=localPath("data/config/hybridJaccard/hairColor_config.txt")))
            self.add_edge('adultservice', 'adultservice.hairColor', edgeType='DataProperty', relationName='hairColor')
            self.add_node('adultservice.name', nodeType='leaf', vocabDescriptor='adultservice_name')
            self.add_edge('adultservice', 'adultservice.name', edgeType='DataProperty', relationName='name')
            self.add_node('adultservice.personAge', nodeType='leaf', vocabDescriptor='adultservice_personAge')
            self.add_edge('adultservice', 'adultservice.personAge', edgeType='DataProperty', relationName='personAge')
        
            self.maybe_add_edge(root, 'offer', 'adultservice', edgeType='ObjectProperty', relationName='itemOffered', 
                                rootScope=allRoots)
            self.maybe_add_edge(root, 'adultservice', 'offer', edgeType='ObjectProperty', relationName='offers', 
                                rootScope=allRoots)
        
            self.add_node('place', nodeType='Class', className='Place')
            self.add_node('postaladdress', nodeType='Class', className='PostalAddress')
        
            self.maybe_add_edge(root, 'offer', 'place', edgeType='ObjectProperty', relationName='availableAtOrFrom', 
                                rootScope=allRoots)
            self.maybe_add_edge(root, 'place', 'postaladdress', edgeType='ObjectProperty', relationName='address', 
                                rootScope=allRoots)
        
            self.add_node('postaladdress.addressLocality', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressLocality')
            self.add_edge('postaladdress', 'postaladdress.addressLocality', edgeType='DataProperty', relationName='addressLocality')
            self.add_node('postaladdress.addressRegion', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressRegion')
            self.add_edge('postaladdress', 'postaladdress.addressRegion', edgeType='DataProperty', relationName='addressRegion')
            self.add_node('postaladdress.addressCountry', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressCountry')
            self.add_edge('postaladdress', 'postaladdress.addressCountry', edgeType='DataProperty', relationName='addressCountry')
            
            self.add_node('webpage', nodeType='Class', className='WebPage', indexRoot='webpage')
            self.maybe_add_edge(root, 'offer', 'webpage', edgeType='ObjectProperty', relationName='mainEntityOfPage', 
                                rootScope=allRoots)
            self.maybe_add_edge(root, 'webpage', 'offer', edgeType='ObjectProperty', relationName='mainEntity', 
                                rootScope=allRoots)
            self.add_node('publisher', nodeType='Class', className='Organization')
            self.maybe_add_edge(root, 'webpage', 'publisher', edgeType='ObjectProperty', relationName='publisher', 
                                rootScope=allRoots)
            self.add_node('publisher.name', nodeType='leaf', vocabDescriptor='webpage_publisher_name')
            self.add_edge('publisher', 'publisher.name', edgeType='DataProperty', relationName='name')
            
    def labelInGraph(self, nodeOrEdge):
        try:
            return self.node[nodeOrEdge]['className']
        except:
            try:
                return self.edge[nodeOrEdge[0]][nodeOrEdge[1]]['relationName']
            except:
                return None
            
    def populateValues(self, nodeOrEdge):
        try:
            node = nodeOrEdge
            nodeType = self.node[node]['nodeType']
            if nodeType == 'leaf':
                self.populateLeafNode(node)
            elif nodeType == 'Class':
                self.populateClassNode(node)
        except Exception as _:
            edge = nodeOrEdge
            (node1, node2) = edge
            edgeType = self.edge[node1][node2]['edgeType']
            if edgeType == 'ObjectProperty':
                self.populateRelationEdge(edge)
            elif edgeType == 'DataProperty':
                self.populateAttributeEdge(edge)
    
    # The problem is that "values" is too general.  We can associate values with nodes and edges via a variety of semantics:
    # (1) instances from ES, presumably only for leaf nodes
    # (2) ontology labels, ontology descriptions, presumably only for edges and interior nodes

    def populateLeafNode(self, node):
        self.node[node]['values'] = loadLeafVocab(self.node[node]['vocabDescriptor'])
        self.node[node]['valueOrigin'] = 'leafVocab'

    # The next three probably should use the same methodology/same code
    def populateClassNode(self, node):
        self.node[node]['values'] = list(set([node, self.node[node]['className']]))
        self.node[node]['valueOrigin'] = 'ontology'

    def populateRelationEdge(self, edge):
        (node1, node2) = edge
        self.edge[node1][node2]['values'] = [camelCaseWords(self.edge[node1][node2]['relationName'])]
        self.edge[node1][node2]['valueOrigin'] = 'ontology'

    def populateAttributeEdge(self, edge):
        (node1, node2) = edge
        self.edge[node1][node2]['values'] = [camelCaseWords(self.edge[node1][node2]['relationName'])]  
        self.edge[node1][node2]['valueOrigin'] = 'ontology'

    def isLeaf(self, nodeOrEdge):
        try:
            return self.node[nodeOrEdge]['valueOrigin'] == 'leafVocab'
        except:
            return False

    def populateAll(self):
        for node in self.nodes():
            self.populateValues(node)
        for edge in self.edges():
            self.populateValues(edge)

    def nodeMatch(self, node, label):
        """list generator"""
        return label.lower().replace('_', ' ') in (value.lower() for value in self.node[node]['values'])

    def edgeMatch(self, edge, label):
        """list generator"""
        return label.lower().replace('_', ' ') in (value.lower() for value in self.edge[edge[0]][edge[1]]['values'])

    def nodeEditWithin(self, node, label, within=1, above=None):
        """set above=0 to avoid matching node value exactly identical to label
        Does not find closest node values, just any values within interval"""
        l = label.lower().replace('_', ' ') 
        for value in self.node[node]['values']:
            value = value.lower().replace('_', ' ')
            actual = distance(l, value)
            if (above==None or actual>above) and actual <= within:
                # if levenshtein is 0, return true value 0.0
                # return actual or 0.0
                return(value, actual)
              
    def edgeEditWithin(self, edge, label, within=1, above=None):
        """set above=0 to avoid matching edge value exactly identical to label"""
        l = label.lower().replace('_', ' ') 
        for value in self.edge[edge[0]][edge[1]]['values']:
            value = value.lower().replace('_', ' ')
            actual = distance(l, value)
            if (not above or actual>above) and actual <= within:
                # if levenshtein is 0, return true value 0.0
                return actual or 0.0
            
    def nodeNearMatch(self, node, label, allowExact=False):
        """set allowExact to True to look up values directly here"""
        label = label.lower().replace('_', ' ') 
        # print(self.node[node])
        try:
            hjMatcher = self.node[node]['matcherDescriptor']
            best = hjMatcher.findBestMatch(label)
            if best != "NONE":
                for value in self.node[node]['values']:
                    value = value.lower().replace('_', ' ')
                    if ((label != value) or allowExact) and (best==value):
                        # HJ(label)== a value from node and 
                        # either we allow exact or see that label is not exactly the retrieved value
                        # print(best)
                        return best
        except KeyError:
            pass
                
    def edgeNearMatch(self, edge, label, allowExact=False):
        """set allowExact to True to look up values directly here"""
        label = label.lower().replace('_', ' ')
        try:
            hjMatcher = self.edge[edge[0]][edge[1]]['matcherDescriptor']
            best = hjMatcher.findBestMatch(label)
            if best != "NONE":
                for value in self.edge[edge[0]][edge[1]]['values']:
                    value = value.lower().replace('_', ' ')
                    if ((label != value) or allowExact) and (best==value):
                        # HJ(label)== a value from edge and 
                        # either we allow exact or see that label is not exactly the retrieved value
                        return best
        except KeyError:
            pass

    def generateSubgraph(self, node):
        seen = set()
        def visitNode(n1):
            if n1 in seen:
                pass
            else:
                yield(("node",n1))
                seen.add(n1)
                for n2 in self.edge[n1]:
                    yield from visitEdge((n1,n2))
        def visitEdge(e):
            (_,n2) = e
            if e in seen:
                pass
            else:
                yield(("edge",e))
                seen.add(e)
                yield from visitNode(n2)
        return visitNode(node)
                
"""SPECS=[ {"docType": "adultservice", "fieldName": "eyeColor", "size": 10},
        {"docType": "adultservice", "fieldName": "hairColor", "size": 10},
        {"docType": "adultservice", "fieldName": "name", "size": 200},
        {"docType": "adultservice", "fieldName": "personAge", "size": 20},

        {"docType": "phone", "fieldName": "name", "size": 200},
        
        {"docType": "email", "fieldName": "name", "size": 200},

        {"docType": "webpage", "innerPath": "publisher", "fieldName": "name", "size": 200},
        # Ignore webpage.description, webpage.dateCreated

        # Ignore offer.identifier
        {"docType": "offer", "innerPath": "priceSpecification", "fieldName": "billingIncrement", "size": 10},
        {"docType": "offer", "innerPath": "priceSpecification", "fieldName": "price", "size": 200},
        {"docType": "offer", "innerPath": "priceSpecification", "fieldName": "name", "size": 200},
        {"docType": "offer", "innerPath": "priceSpecification", "fieldName": "unitCode", "size": 10},
        {"docType": "offer", "innerPath": "availableAtOrFrom.address", "fieldName": "addressLocality", "size": 200},
        {"docType": "offer", "innerPath": "availableAtOrFrom.address", "fieldName": "addressRegion", "size": 200},
        {"docType": "offer", "innerPath": "availableAtOrFrom.address", "fieldName": "addressCountry", "size": 200},
        # Ignore offer.availableAtOrFrom.name
        # Ignore offer.availableAtOrFrom.geo.lat, offer.availableAtOrFrom.geo.lon
    ]"""
    
wg = None

nodeDesig = namedtuple('nodeDesig', 'nodeType, nodeRefs')

def truenodeDesig(node):
    """Render a kgraph node as a wgraph node"""
    return nodeDesig(nodeType='truenode', nodeRefs=(node,))

def edgenodeDesig(edge):
    """Render a kgraph edge as a wgraph node"""
    return nodeDesig(nodeType='edgenode', nodeRefs=edge)
    
class ImpossibleGraph(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ImpossibleGraph, self).__init__(message)
        
        # PythonDecorators/entry_exit_class.py

class entry_exit(object):

    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        print("Entering", self.f.__name__)
        r = self.f(*args)
        print("Exited", self.f.__name__)
        return(r)

def minimalSubgraph(kgraph, root, query, verbose=False):
    # transform into weighted nondirected graph
    # all nodes become nodes ("truenode")
    # all edges also become nodes ("edgenode")
    # induce edge with weight 1 for each node/edge and edge/node
    # except: traverse starting at root, dropping any backlinks [?]

    # required contains nodes/edges from original kgraph
    required = defaultdict(list)
    # To start with, we don't know if root has any cands
    required[truenodeDesig(root)]=[]
    for a in query.ngrams.values():
        for cand in a["candidates"]:
            if cand.referentType == 'node':
                #required.add(truenodeDesig(cand.referent))
                required[truenodeDesig(cand.referent)].append(cand)
            elif cand.referentType == 'edge':
                #required.add(edgenodeDesig(cand.referent))
                required[edgenodeDesig(cand.referent)].append(cand)
    if verbose:
        print("Steiner tree must contain:")
        for n, c in required.items():
            print("  ", n.nodeRefs[0], c)

    # seen contains nodes/edges from original kgraph
    seen = set()
    
    # q contains nodes/edges from original kgraph
    q = Queue(maxsize=kgraph.number_of_nodes() + 3*kgraph.number_of_edges())
    q.put(root)
    
    # wg contains wgnodes, wgedges
    global wg
    wg = Graph()

    while not q.empty():
        # print("Queue size: {}; wg size {}".format(q.qsize(), len(wg)), file=sys.stderr)
        obj = q.get()
        # print("Dequeue {}".format(obj), file=sys.stderr)
        if not obj in seen:
            if isinstance(obj, (str)):
                # unseen kgraph node
                seen.add(obj)
                node = obj
                # print("wg: add true node {}".format(node), file=sys.stderr)
                wg.add_node(truenodeDesig(node))
                for node2 in kgraph.edge[node]:
                    # print("Enqueue edge {} {}".format(node, node2), file=sys.stderr)
                    q.put((node,node2))
            elif isinstance(obj, (list, tuple)) and len(obj)==2:
                # unseen kgraph edge
                seen.add(obj)
                # edge = obj
                # create a node representing original edge
                (node1, node2) = obj
                truenode1 = truenodeDesig(node1)
                truenode2 = truenodeDesig(node2)
                edge = obj
                # print("wg: add edge node {}".format(edge), file=sys.stderr)
                edgenode = edgenodeDesig(edge)
                wg.add_node(edgenode)
                wg.add_edge(truenode1, edgenode, weight=1)
                wg.add_edge(edgenode, truenode2, weight=1)
                # print("Enqueue node {}".format(node2), file=sys.stderr)
                q.put(node2)
            else:
                print("Unexpected {}".format(obj), file=sys.stderr)
        else:
            # print("Obj {} already seen".format(obj), file=sys.stderr)
            pass

    # print("Weighted non-directed graph")
    # pprint(wg.nodes())
    # return (None, wg)
    # generate minimal steiner tree
    try:
        requiredNodes = list(required.keys())
        st = make_steiner_tree(wg, requiredNodes)
        # convert back to directed graph
        neededTruenodes = [nd.nodeRefs[0] for nd in st.nodes() if nd.nodeType=='truenode']
        subg = kgraph.subgraph(neededTruenodes)
        return (st, wg, subg)
    except ValueError as ve:
        if "not in original graph" in str(ve):
            raise ImpossibleGraph("Cannot generate subgraph of {} containing {}".format("weightedGraph", requiredNodes))
        else:
            raise(ve)
    
g = None
    
def htGraph(root, **kwargs):
    global g
    g = KGraph()
    g.installDomain(root, domainType='ht')
    g.populateAll()
    return g
