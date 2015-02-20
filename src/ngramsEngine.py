from nltk.util import ngrams

#This class makes use of nltk library for generating n-grams given a query
class ngramsEngine(object):

	def __init__(self):
		self = self

	# Module to print n-grams
	def printNGrams(self,ngramsList):
		for token in ngramsList:
			print(token.strip())


	# Module that generates n-grams list
	# Input : query
	# Output : Two lists are returned.
	# 1st list : This has all the n-grams arranged hierarchically
	# 2nd list : This is a list that as list of n-grams grouped together based on the length
	# EX:  i/p - a b c d 
	# List1 : ['a b c d', 'a b c', 'b c d', 'a b', 'b c', 'c d', 'a', 'b', 'c', 'd']
	# List2 : [['a', 'b', 'c', 'd'], ['a b', 'b c', 'c d'], ['a b c', 'b c d'], ['a b c d']]

	def generateNGrams(self,query):

		ngramsNLTKList = []
		for n in range(len(query),0,-1):
			ngramsNLTKList.extend(ngrams(query.split(),n))

		lookupList = []
		ngramList = []


		for ngram in ngramsNLTKList:
			ngramList.append((' '.join(ngram)).strip())

		if(len(ngramsNLTKList)>0):
			maxLength = len(ngramsNLTKList[0])
			for i in range(maxLength):
				lookupList.append([])

		for token in ngramsNLTKList:
			joinedToken = ' '.join(token).strip()
			listLength = len(joinedToken)
			currentList = lookupList[len(token)-1]
			currentList.append(' '.join(token))

		return ngramList,lookupList


def main():
	ngramsEngineObject = ngramsEngine()
	query = input(" Enter the query : ")

	ngramsList,lookupList = ngramsEngineObject.generateNGrams(query.strip())
	ngramsEngineObject.printNGrams(ngramsList)

if __name__ == '__main__':
	main()













