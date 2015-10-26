#!/usr/bin/env python

from collections import defaultdict
from collections import namedtuple
import json
from queue import Queue
import re
import sys, os
from pprint import pprint

from Levenshtein import distance
from networkx import Graph, DiGraph

from SteinerTree import make_steiner_tree
from hybridJaccard import HybridJaccard


LEAF_VOCAB_CACHE = "/Users/philpot/Documents/project/graph-keyword-search/src/dig/data/cache"

def loadLeafVocab(pathdesc, root=LEAF_VOCAB_CACHE):
    pathname = os.path.join(root, pathdesc  + ".json")
    with open(pathname, 'r') as f:
        j = json.load(f)
    # dict of (value, count)
    byCount = sorted([(v,k) for (k,v) in j['histo'].items()], reverse=True)
    return [t[1] for t in byCount]

def localPath(suffix):
    return os.path.join(os.path.dirname(__file__), suffix)

# http://stackoverflow.com/a/9283563/2077242
def camelCaseWords(label):
    label = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', label)
    return label

class KGraph(DiGraph):
    def __init__(self, domainType=None):
        super(KGraph, self).__init__()
        self.domainType = domainType
        self.installDomain(domainType)

    def installDomain(self, domainType=None):
        if domainType == 'ht':
            self.add_node('seller', nodeType='Class', className='PersonOrOrganization', indexRoot='seller')
        
            self.add_node('phone', nodeType='Class', className='PhoneNumber', indexRoot='phone')
            self.add_edge('seller', 'phone', edgeType='ObjectProperty', relationName='telephone')
        
            self.add_node('phone.name', nodeType='leaf', vocabDescriptor='seller_telephone_name')
            self.add_edge('phone', 'phone.name', edgeType='DataProperty', relationName='name')
        
            self.add_node('email', nodeType='Class', className='EmailAddress', indexRoot='email')
            self.add_edge('seller', 'email', edgeType='ObjectProperty', relationName='email')
            # for now this ES query doesn't work
            # self.add_node('email.name', nodeType='leaf', values=loadLeafVocab('seller_email_name'), vocabDescriptor='seller_email_name')
            # so use flat data instead
            self.add_node('email.name', nodeType='leaf', vocabDescriptor='email_name')
            self.add_edge('email', 'email.name', edgeType='DataProperty', relationName='name')
        
            self.add_node('offer', nodeType='Class', className='Offer', indexRoot='offer')
            self.add_edge('offer', 'seller', edgeType='ObjectProperty', relationName='seller')
            self.add_edge('seller', 'offer', edgeType='ObjectProperty', relationName='makesOffer')
        
            self.add_node('priceSpecification', nodeType='Class', className='PriceSpecification')
            self.add_node('priceSpecification.billingIncrement', nodeType='leaf', vocabDescriptor='offer_priceSpecification_billingIncrement')
            self.add_edge('priceSpecification', 'priceSpecification.billingIncrement', edgeType='DataProperty', relationName='billingIncrement')
            self.add_node('priceSpecification.price', nodeType='leaf', vocabDescriptor='offer_priceSpecification_price')
            self.add_edge('priceSpecification', 'priceSpecification.price', edgeType='DataProperty', relationName='price')
            self.add_node('priceSpecification.name', nodeType='leaf', vocabDescriptor='offer_priceSpecification_name')
            self.add_edge('priceSpecification', 'priceSpecification.name', edgeType='DataProperty', relationName='name')
            self.add_node('priceSpecification.unitCode', nodeType='leaf', vocabDescriptor='offer_priceSpecification_unitCode')
            self.add_edge('priceSpecification', 'priceSpecification.unitCode', edgeType='DataProperty', relationName='unitCode')

            self.add_node('adultservice', nodeType='Class', className='AdultService', indexRoot='adultservice')
            self.add_node('adultservice.eyeColor', nodeType='leaf', 
                           vocabDescriptor='adultservice_eyeColor', 
                           matcherDescriptor=HybridJaccard(ref_path=localPath("data/config/hybridJaccard/eyeColor_reference_wiki.txt"), 
                                                           config_path=localPath("data/config/hybridJaccard/eyeColor_config.txt")))
            self.add_edge('adultservice', 'adultservice.eyeColor', edgeType='DataProperty', relationName='eyeColor')
            self.add_node('adultservice.hairColor', nodeType='leaf', vocabDescriptor='adultservice_hairColor')
            self.add_edge('adultservice', 'adultservice.hairColor', edgeType='DataProperty', relationName='hairColor')
            self.add_node('adultservice.name', nodeType='leaf', vocabDescriptor='adultservice_name')
            self.add_edge('adultservice', 'adultservice.name', edgeType='DataProperty', relationName='name')
            self.add_node('adultservice.personAge', nodeType='leaf', vocabDescriptor='adultservice_personAge')
            self.add_edge('adultservice', 'adultservice.personAge', edgeType='DataProperty', relationName='personAge')
        
            self.add_edge('offer', 'adultservice', edgeType='ObjectProperty', relationName='itemOffered')
            self.add_edge('adultservice', 'offer', edgeType='ObjectProperty', relationName='offers')
        
            self.add_node('place', nodeType='Class', className='Place')
            self.add_node('postaladdress', nodeType='Class', className='PostalAddress')
        
            self.add_edge('offer', 'place', edgeType='ObjectProperty', relationName='availableAtOrFrom')
            self.add_edge('place', 'postaladdress', edgeType='ObjectProperty', relationName='address')
        
            self.add_node('postaladdress.addressLocality', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressLocality')
            self.add_edge('postaladdress', 'postaladdress.addressLocality', edgeType='DataProperty', relationName='addressLocality')
            self.add_node('postaladdress.addressRegion', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressRegion')
            self.add_edge('postaladdress', 'postaladdress.addressRegion', edgeType='DataProperty', relationName='addressRegion')
            self.add_node('postaladdress.addressCountry', nodeType='leaf', vocabDescriptor='offer_availableAtOrFrom_address_addressCountry')
            self.add_edge('postaladdress', 'postaladdress.addressCountry', edgeType='DataProperty', relationName='addressCountry')
            
            self.add_node('webpage', nodeType='Class', className='WebPage', indexRoot='webpage')
            self.add_node('publisher', nodeType='Class', className='Organization')
            self.add_edge('webpage', 'publisher', edgeType='ObjectProperty', relationName='publisher')
            self.add_node('publisher.name', nodeType='leaf', vocabDescriptor='webpage_publisher_name')
            self.add_edge('publisher', 'publisher.name', edgeType='DataProperty', relationName='name')
            
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
    
    def populateLeafNode(self, node):
        self.node[node]['values'] = loadLeafVocab(self.node[node]['vocabDescriptor'])
    
    def populateClassNode(self, node):
        self.node[node]['values'] = list(set([node, self.node[node]['className']]))
    
    def populateRelationEdge(self, edge):
        (node1, node2) = edge
        self.edge[node1][node2]['values'] = [camelCaseWords(self.edge[node1][node2]['relationName'])]
    
    def populateAttributeEdge(self, edge):
        (node1, node2) = edge
        self.edge[node1][node2]['values'] = [camelCaseWords(self.edge[node1][node2]['relationName'])]  
    
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
        """set above=0 to avoid matching node value exactly identical to label"""
        l = label.lower().replace('_', ' ') 
        for value in self.node[node]['values']:
            value = value.lower().replace('_', ' ')
            actual = distance(l, value)
            if (not above or actual>above) and actual <= within:
                # if levenshtein is 0, return true value 0.0
                return actual or 0.0
              
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
        except KeyError as ke:
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

def minimalSubgraph(kgraph, root, kquery):
    # transform into weighted nondirected graph
    # all nodes become nodes ("truenode")
    # all edges also become nodes ("edgenode")
    # induce edge with weight 1 for each node/edge and edge/node
    # except: traverse starting at root, dropping any backlinks [?]

    # required contains nodes/edges from original kgraph
    required = set()
    required.add(truenodeDesig(root))
    for a in kquery.anchors.values():
        for cand in a["candidates"]:
            if cand.referentType == 'node':
                required.add(truenodeDesig(cand.referent))
            elif cand.referentType == 'edge':
                required.add(edgenodeDesig(cand.referent))
    required = list(required)
    print("Steiner tree must contain all of:")
    for n in required:
        print("  ", n.nodeRefs[0])
            
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
        st = make_steiner_tree(wg, required)
        # convert back to directed graph
        needed = [nd.nodeRefs[0]  for nd in st.nodes() if nd.nodeType=='truenode']
        subg = kgraph.subgraph(needed)
        return (st, wg, subg)
    except ValueError as ve:
        if "not in original graph" in str(ve):
            raise ImpossibleGraph("Cannot generate subgraph of {} containing {}".format("weightedGraph", required))
        else:
            raise(ve)
    
g = None
    
def htGraph():
    global g
    g = KGraph(domainType='ht')
    g.populateAll()
    return g
