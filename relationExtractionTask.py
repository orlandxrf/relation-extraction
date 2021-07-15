class RelationExtraction():
	"""Class to extract relations using the tree dependency from spacy"""
	def __init__(self, entitiesUnallowed, inputData, outputData, flagtosave=False, makeTree=False, interval=[]):
		self.entitiesUnallowed = entitiesUnallowed # {'PER','ORG','LOC'}
		self.inputData = inputData # file-path from corpus tagged with named entities
		self.outputData = outputData # file-path from corpus tagged with relations
		self.flagtosave = flagtosave
		# self.verbose = verbose
		self.makeTree = makeTree
		self.countSntsUsed = 0
		self.countSntsRejected = 0
		self.interval = interval
		# ----------------------------------------------------------------------------
		self.nlp = self.loadDependencyModelSpacy() # store Spacy Dependency parser
		self.dpDocument = None # store Spacy source dependency tree
		self.allEntities = {}
		self.twoEntities = [] # list of tuples e.g. [(idEntity1, "entity1"),(idEntity2, "entity2")]
		self.entityTag1 = None # entity tag 1
		self.entityTag2 = None # entity tag 2
		self.entityName1 = None # entity name 1
		self.entityName2 = None # entity name 2
		self.entityNode1 = None # entity node of entity 1
		self.entityNode2 = None # entity node of entity 2
		self.G = None # store Graph from dependency tree (networkx)
		self.nodeLabels = {} # nodes from G
		self.edgeLabels = {} # edges from G
		self.posLabels = [] # Part-of-Speech
		self.entitiesPattern = "" # pattern from two entities
		# ----------------------------------------------------------------------------
		self.pathBetweenTwoEntities = []
		# ----------------------------------------------------------------------------
		self.idDocument = 0
		self.idSentence = 0
		self.candidates = []
		self.indexSntCorpus = 0 # borrar despues
		# ----------------------------------------------------------------------------
		self.statistics = {'documents':0, 'snts_used':0, 'snts_diss':0, 'methods':{} }
		self.sentence = ''

	def saveToFile(self, filename, data, mode='a'):
		"""Save data to specific filename"""
		g = open(filename, mode)
		g.write(data)
		g.close()

	def removeEntitiesFromSentence(self, sentence):
		"""Remove entity tags inside the one sentence"""
		sentence = sentence.split()
		for a, word in enumerate(sentence):
			if '_' in word:
				word = word.split('_')
				if word[-1] in self.entitiesUnallowed:
					word.pop()
					word = ' '.join(word)
					sentence[a] = word
		sentence = ' '.join(sentence)
		return sentence

	def generateSentencesWithTwoEntities(self, sentence):
		"""Just allowed two entities per sentence. Generate all sentences with two entitties from one sentence with at least two entities"""
		tmp_snts = []
		count = 0
		entities = list(self.allEntities.items())
		if len(entities) == 2:
			tmp_snts.append( sentence )
		elif len(entities) > 2:
			for i in range(1, len(entities)):
				tmp_snt = []
				for k, word in enumerate(sentence.split()):
					if '_' in word:
						if (k, word) not in entities[i-1:i+1]:
							word = ' '.join(word.split('_')[:-1])
							tmp_snt.append(word)
						else: tmp_snt.append(word)
					else: tmp_snt.append(word)
				tmp_snts.append( ' '.join(tmp_snt) )
		return tmp_snts

	def loadDependencyModelSpacy(self):
		"""Load Dependency Model from Spacy"""
		from datetime import datetime
		import spacy
		start_time = datetime.now()
		print ('\n|---------------------------------|')
		print ('| Loading dependency parser model |')
		nlp = spacy.load('es_core_news_md')
		end_time = datetime.now()
		print ('| Model loaded in {}  |'.format(end_time - start_time))
		print ('|---------------------------------|\n')
		return nlp

	def json2digraph(self, data, dep=None, color='black'):
		"""Convert dependency json (Spacy) to Digraph format (Graphviz)"""

		root = 0
		digraph = """digraph G{
		edge [dir=forward]
		node [shape=plaintext]

		"""
		# -------------------------------------------------------------
		# set the nodes
		digraph += '0 [label="0 (None)"]\n'
		for item in data['tokens']:
			token = data['text'][item['start']:item['end']]
			if '_' in token:
				digraph += '\t{} [label="{} ({}) {}" fontcolor="blue"]\n'.format(item['id']+1, item['id']+1, token, item['pos'])
			# if item['pos'] == 'VERB' or item['pos'] == 'AUX':
			elif item['pos'] == 'VERB' or item['pos'] == 'AUX':
				digraph += '\t{} [label="{} ({}) {}" fontcolor="forestgreen"]\n'.format(item['id']+1, item['id']+1, token, item['pos'])
			# if dep == item['dep'] and '_' not in token and item['pos'] != 'VERB' and item['pos'] != 'AUX':
			elif dep == item['dep']:
				digraph += '\t{} [label="{} ({}) {}" fontcolor="{}"]\n'.format(item['id']+1, item['id']+1, token, item['pos'], color)
			if item['dep']=='ROOT':
				root = item['id']+1
			digraph += '\t{} [label="{} ({}) {}"]\n'.format(item['id']+1, item['id']+1, token, item['pos'])

		# set the edges
		digraph += '\t0 -> {} [label="ROOT"]\n'.format( root )
		for item in data['tokens']:
			if item['dep'] != 'ROOT' and item['dep'] != dep:
				digraph += '\t{} -> {} [label="{}"]\n'.format(item['head']+1, item['id']+1, item['dep'] )
			if item['dep'] == dep:
				digraph += '\t{} -> {} [label="{}" color="{}" fontcolor="{}"]\n'.format(item['head']+1, item['id']+1, item['dep'], color, color )
		digraph += '}\n'

		return digraph

	def drawDependecyTree(self, digraph, figurename='tmp_tree', fmt='png', view=False):
		from graphviz import Source
		source = Source(digraph, filename='{}.{}'.format(figurename, 'dot'), format='{}'.format(fmt))
		if view: source.view()
		else: source.render()

	def jsonToMultiDigraph(self, json_data):
		"""Convert Json tree to Graph"""
		import networkx as nx
		G = nx.MultiDiGraph()
		G.add_node(0, pos='None', text='None')
		for item in json_data['tokens']: # nodes
			G.add_node(item['id']+1, pos=item['pos'], text=json_data['text'][item['start']:item['end']])
		for item in json_data['tokens']: # edges
			if item['dep'] == 'ROOT': G.add_edge(item['id']+1, 0, dep=item['dep'])
			else: G.add_edge(item['id']+1, item['head']+1, dep=item['dep'])
		return G

	def setResult(self, relationResult, methodResult, order=True):
		"""set the result"""
		original = list(dict(self.twoEntities.copy()).values())
		if type(relationResult['result'])==list:
			if len(relationResult['result'])>0:
				if order: self.candidates.append('("{}", "{}", "{}", "{}")'.format(original[0], original[1], relationResult['result'], methodResult))
				else: self.candidates.append('("{}", "{}", "{}", "{}")'.format(original[1], original[0], relationResult['result'], methodResult))
		elif type(relationResult['result'])==str:
			if len(relationResult['result'])!="":
				if order: self.candidates.append('("{}", "{}", "{}", "{}")'.format(original[0], original[1], relationResult['result'], methodResult))
				else: self.candidates.append('("{}", "{}", "{}", "{}")'.format(original[1], original[0], relationResult['result'], methodResult))

	def getEntitiesFromJson(self, json_data):
		"""return a tuple with the two entities; name and id-word in the sentence"""
		entities = []
		text = json_data['text']
		for item in json_data['tokens']:
			token = text[item['start']:item['end']]
			if '_' in token:
				entities.append( (item['id']+1, token) )
		return entities

	def getSimplePathBetweenNodes(self, source, target):
		"""Return simple path between two entities"""
		import networkx as nx
		path = list( nx.all_simple_paths(self.G, source, target) )
		if len(path) >= 1: # just return the first simple path founded
			return path[0]
		else:
			return path

	def replaceHypenToUnderscore(self, sentence):
		"""Replace the hyphen iside the entity words (e.g. 2018-2019_EVT) to underscore (2018_2019_EVT)"""
		sentence = sentence.split()
		for index, word in enumerate(sentence):
			if '_' in word and '-' in word: sentence[index] = word.replace('-','_')
		sentence = ' '.join(sentence)
		return sentence

	def setCurrentEntityParameters(self, keyTag1, keyTag2, nodeIdEnt1, nodeIdEnt2):
		self.entityTag1 = self.twoEntities[keyTag1][1].split('_')[-1]
		self.entityTag2 = self.twoEntities[keyTag2][1].split('_')[-1]
		self.entitiesPattern = '{}-{}'.format(self.entityTag1, self.entityTag2)
		self.entityName1 = self.twoEntities[keyTag1][1]
		self.entityName2 = self.twoEntities[keyTag2][1]
		self.entityNode1 = nodeIdEnt1
		self.entityNode2 = nodeIdEnt2

	def checkConjunction(self):
		"""Check conjunction between two entities. If there's exist, avoid this relationship"""
		if (self.entityNode2, self.entityNode1) in list(self.edgeLabels.keys()) and self.edgeLabels[((self.entityNode2, self.entityNode1))]=='conj':
			return True
		else:
			return False

	def getTextFromNodeList(self, nodeList, order=True):
		result = []
		if order:
			nodeList = list(set(nodeList)) # remove duplicates
			nodeList.sort()
		else: nodeList = list(dict.fromkeys(nodeList)) # remove duplicates keeping the order
		if len(nodeList)>0:
			result = [self.nodeLabels[node]['text'] for node in nodeList if '_' not in self.nodeLabels[node]['text']]
			return '_'.join(result)
		else:
			return []

	def toolGetFatherNode(self, child, father, edge, pos):
		if self.entityNode1 != father:
			if self.edgeLabels[child, father] in edge and self.nodeLabels[father]['pos'] in pos: return {'status':True, 'node':father}
			else: return {'status':False, 'node':0}
		else: return {'status':False, 'node':0}

	def toolGetFocusNodeDescendants(self, focusNode, edgeLabels=[], posLabels=[], nounEL=[], nounPL=[], nodeTowardsE2=0, pronoun=False, propernoun=False, adjective=False, adverb=False):
		listresult = []
		nodeDescendants = list( self.G.predecessors(focusNode) )
		if self.entityNode2 in nodeDescendants: nodeDescendants.remove(self.entityNode2)
		if self.entityNode1 in nodeDescendants: nodeDescendants.remove(self.entityNode1)
		if len(nodeDescendants)>0:
			for descendant in nodeDescendants:
				if self.edgeLabels[descendant,focusNode] in edgeLabels and self.nodeLabels[descendant]['pos'] in posLabels:
					if self.nodeLabels[descendant]['pos']=='NOUN':
						listresult.append(descendant)
						listresult += self.toolGetNodeDescendants(descendant, nounEL, nounPL)
					elif self.nodeLabels[descendant]['pos']=='PRON' and pronoun:
						listresult.append(descendant)
						listresult += self.toolGetNodeDescendants(descendant, ['case','det'], ['ADP','DET'])
					elif self.nodeLabels[descendant]['pos']=='PROPN' and propernoun:
						listresult.append(descendant)
						listresult += self.toolGetNodeDescendants(descendant, ['case','det'], ['ADP','DET'])
					elif self.nodeLabels[descendant]['pos']=='ADJ' and adjective:
						listresult.append(descendant)
						listresult += self.toolGetNodeDescendants(descendant, ['case','det','cc','mark','cop'], ['ADP','DET','CONJ','AUX'])
					elif self.nodeLabels[descendant]['pos']=='ADV' and adverb:
						listresult.append(descendant)
						listresult += self.toolGetNodeDescendants(descendant, ['fixed'], ['SCONJ','ADP'])
					else:
						# don't extract 'advmod' when the edge is after E2 edge
						if nodeTowardsE2>0 and self.edgeLabels[descendant,focusNode]=='advmod' and descendant>nodeTowardsE2: continue
						else: listresult.append(descendant)
		return listresult

	def toolGetNodeDescendants(self, node, edgeLabels=[], posLabels=[], fixed=False, aux=False):
		"""
		get a specific descendants from the node
		node = number of node father/ancestor
		edgeLabels = list of edges allow to get nodes
		posLabels = list of pos (part of speech) allow to check specific pos node
		"""
		listresult = []
		posFixed = ['NOUN', 'ADP','DET','ADV']
		posAux = ['ADP','DET']
		nounDescendants = list( self.G.predecessors(node) )
		if self.entityNode2 in nounDescendants: nounDescendants.remove(self.entityNode2)
		if len(nounDescendants)>0:
			for descendant in nounDescendants:
				if self.edgeLabels[descendant, node] in edgeLabels and self.nodeLabels[descendant]['pos'] in posLabels:
					listresult.append(descendant)
				if fixed: # get fixed edges between nodes
					if self.nodeLabels[descendant]['pos']=='ADP':
						fixedDescendants = list( self.G.predecessors(descendant))
						if len(fixedDescendants)>0:
							for fixnode in fixedDescendants:
								if self.edgeLabels[fixnode, descendant]=='fixed' and self.nodeLabels[fixnode]['pos'] in posFixed:
									listresult.append(fixnode)
				if aux: # get fixed edges between nodes
					if self.nodeLabels[descendant]['pos']=='AUX':
						markDescendants = list( self.G.predecessors(descendant))
						if len(markDescendants)>0:
							for markNode in markDescendants:
								if self.edgeLabels[markNode, descendant]=='mark' and self.nodeLabels[markNode]['pos'] in posAux:
									listresult.append(markNode)
		return listresult

	def toolGetNodeDescendantsNode1IsLargerThatNode2(self, edgeLabels=[], posLabels=[]):
		listresult = []
		if self.entityNode1 > self.entityNode2:
			descentdantsNode1 = list(self.G.predecessors(self.entityNode1))
			for dnode1 in descentdantsNode1:

				if dnode1 <self.entityNode1:
					if self.edgeLabels[dnode1, self.entityNode1] in edgeLabels and self.nodeLabels[dnode1]['pos'] in posLabels:
						listresult.append(dnode1)
		return listresult

	def toolRemoveNodesBiggerThanNode(self, tmpList, focusNode):
		newList = [item for item in tmpList if int(item) < int(focusNode)]
		return newList

	def getIntersectionNode(self, pos='VERB'):
		set1 = self.getSimplePathBetweenNodes(self.entityNode1, 0)
		set2 = self.getSimplePathBetweenNodes(self.entityNode2, 0)
		set1.remove(0)
		set2.remove(0)
		focusNode = [nd1 for nd1 in set1 if nd1 in set2]
		if len(focusNode)>0:
			# verify pos label and the node musn't be an entity (using the underscore character)
			if self.nodeLabels[focusNode[0]]['pos']==pos and '_' not in self.nodeLabels[focusNode[0]]['text']: return focusNode[0]
			else: return 0
		else: return 0

	def verbBetweenEntities(self):
		result = []
		udrNode = ['nsubj','obj','obl','aux','advmod','appos','compound','mark','det','case','amod']
		posNode = ['PRON','ADJ','VERB','AUX','ADV','NOUN','ADP','DET','SCONJ','PROPN']
		udrNoun, posNoun = ['case','det','amod','mark'], ['ADP','DET','ADJ','SCONJ']
		udrEnt2, posEnt2 = ['case','det','cc','mark','aux','amod'], ['ADP','DET','CONJ','SCONJ','AUX','ADJ','NOUN']
		simplePathE1toE2 = self.getSimplePathBetweenNodes(self.entityNode2, self.entityNode1)
		if len(simplePathE1toE2) > 0: # A simple path was found
			simplePathE1toE2.pop(0) # remove node E2
			simplePathE1toE2.pop() # remove node E1
			for node in simplePathE1toE2:
				if self.nodeLabels[node]['pos'] == 'VERB':

					result.append(node)
					verbAncestors = list(self.G.successors(node)) # father from this node
					if len(verbAncestors)>0:
						posAncestorList = ['VERB']
						udrAncestorList = ['ccomp','xcomp','advcl']
						if self.nodeLabels[verbAncestors[0]]['pos'] in posAncestorList and self.edgeLabels[node,verbAncestors[0]] in udrAncestorList:
							result += [verbAncestors[0]]
							result += self.toolGetFocusNodeDescendants(verbAncestors[0], udrNode, posNode, udrNoun, posNoun, pronoun=True, propernoun=True)
						# if nfather['status']: result.append(nfather['node'])
					result += self.toolGetFocusNodeDescendants(node, udrNode, posNode, udrNoun, posNoun, pronoun=True)
					if len(result)>0: # if was found some relations
						result += self.toolGetNodeDescendants(self.entityNode2, udrEnt2, posEnt2, fixed=True)
						result = self.getTextFromNodeList(result)

						self.setResult({'result':result}, 7)
						break

	def apposBetweenEntities(self):
		result = []
		udrNode = ['case','det','amod','cc','nmod','nummod','conj','acl','cop','aux']
		posNode = ['ADP','DET','ADJ','ADV','CONJ','NOUN','NUM','PROPN','AUX','VERB']
		udrNoun, posNoun = ['case','det','amod','nummod'], ['ADP','DET','ADJ','NUM']
		udrEnt2, posEnt2 = ['case','det','cc','mark','aux','amod'], ['ADP','DET','CONJ','SCONJ','AUX','ADJ']
		simplePathE1toE2 = self.getSimplePathBetweenNodes(self.entityNode2, self.entityNode1)

		if len(simplePathE1toE2) > 2: # A simple path was found
			simplePathE1toE2.pop() # remove node E1
			for node in simplePathE1toE2:
				apposAncestors = list(self.G.successors(node))
				if len(apposAncestors) > 0:
					for ancestor in apposAncestors:
						# universal dependency relations and part of speech allowed are:
						if self.edgeLabels[node, ancestor]=='appos' and self.nodeLabels[ancestor]['pos']=='NOUN':

							if node==self.entityNode2: focusNode = ancestor
							elif ancestor==self.entityNode1: focusNode = node
							else: focusNode = node
							result.append(focusNode)

							# check if the node1 is larger that node2
							result += self.toolGetNodeDescendantsNode1IsLargerThatNode2(['cop','aux','case','advmod'],['AUX','VERB','ADP','ADV'])

							# check if the father is POS: ADJ and rel: nmod
							focusNodeAncestor = list(self.G.successors(focusNode))[0]

							if (self.edgeLabels[focusNode, focusNodeAncestor]=='nmod'\
								or self.edgeLabels[focusNode, focusNodeAncestor]=='obj'\
								or self.edgeLabels[focusNode, focusNodeAncestor]=='obl'\
								or self.edgeLabels[focusNode, focusNodeAncestor]=='appos')\
							and (self.nodeLabels[focusNodeAncestor]['pos']=='ADJ'\
								or self.nodeLabels[focusNodeAncestor]['pos']=='NOUN'\
								or self.nodeLabels[focusNodeAncestor]['pos']=='AUX'):

								result.append(focusNodeAncestor)
								result += self.toolGetFocusNodeDescendants(focusNodeAncestor, udrNode, posNode, udrNoun, posNoun)

							focusNodeDescendants = list(self.G.predecessors(focusNode))
							if focusNodeAncestor==self.entityNode1 and self.entityNode2 in focusNodeDescendants:
								# case in which the first entity has just one node between it and the second entity

								udrNodeCopy, posNodeCopy = udrNode.copy(), posNode.copy()
								udrNodeCopy.remove('det'); udrNodeCopy.remove('case')
								posNodeCopy.remove('DET'); posNodeCopy.remove('ADP')

								result += self.toolGetFocusNodeDescendants(focusNodeAncestor, udrNodeCopy, posNodeCopy, udrNoun, posNoun, propernoun=True, adjective=True, adverb=True)
								result += self.toolGetFocusNodeDescendants(focusNode, udrNode, posNode, udrNoun, posNoun, propernoun=True, adjective=True, adverb=True)
							else:

								# get the node descendants from the focused node including the descendants noun node
								result += self.toolGetFocusNodeDescendants(focusNode, udrNode, posNode, udrNoun, posNoun, propernoun=True, adjective=True, adverb=True)
					if len(result)>0: # if appos was found then

						# get the node descendants from the second entity
						result += self.toolGetNodeDescendants(self.entityNode2, udrEnt2, posEnt2, fixed=True)

						if self.entityNode2 > self.entityNode1: result = self.toolRemoveNodesBiggerThanNode(result, self.entityNode2)
						if self.entityNode1 > self.entityNode2: result = self.toolRemoveNodesBiggerThanNode(result, self.entityNode1)
						result = self.getTextFromNodeList(result)

						# when someone (second entity) said something about the first entity using punctuation symbols (:)
						if self.entityNode1 < self.entityNode2:
							checkLst = list(self.G.predecessors(self.entityNode2))
							# print ("checkLst: ", checkLst)
							for ck in checkLst:
								if self.edgeLabels[ck, self.entityNode2]=='punct'\
									and self.nodeLabels[ck]['pos']=='PUNCT'\
									and self.nodeLabels[ck]['text']==':':
									result = '{}_dice'.format(result)

						self.setResult({'result':result}, 5)
						break

	def amodBetweenEntities(self):
		simplePathE1toE2 = self.getSimplePathBetweenNodes(self.entityNode2, self.entityNode1)
		result = []
		udrNode, posNode = ['obl','obj','advmod','nmod','advcl'], ['NOUN','ADV','ADJ']
		udrNoun, posNoun = ['case','det','amod','mark','aux'], ['ADP','DET','ADJ','AUX']
		udrEnt2, posEnt2 = ['case','det','cc','mark','aux','amod','cop'], ['ADP','DET','CONJ','SCONJ','AUX','ADJ']
		if len(simplePathE1toE2) > 2: # A simple path was found

			for node in simplePathE1toE2:
				amodAncestors = list(self.G.successors(node))
				if len(amodAncestors) > 0:
					for ancestor in amodAncestors:
						# universal dependency relations and part of speech allowed are:
						if self.edgeLabels[node, ancestor]=='amod' and self.nodeLabels[node]['pos']=='ADJ':

							ancestorEnt2 = list(self.G.successors(self.entityNode2))[0]
							if ancestor==self.entityNode1 and ancestorEnt2==node:
								if self.nodeLabels[node]['pos']=='ADJ':
									result.append(node)
								else:
									result += self.toolGetFocusNodeDescendants(node, udrNode, posNode, udrNoun, posNoun)
							else:
								result.append(node)
								result += self.toolGetFocusNodeDescendants(node, udrNode, posNode, udrNoun, posNoun, adjective=True)

								# check if the ancestor node would be part of the relationship
								nfather = self.toolGetFatherNode(node, ancestor, ['amod','nmod'], ['NOUN'])
								if nfather['status']:
									result += [nfather['node']]
									result += self.toolGetFocusNodeDescendants(nfather['node'], udrNoun+['cc'], posNoun+['CONJ'], [], [])

					if len(result)>0: # if amod was found then

						# check for nmod NOUN from enttity2
						ancestorEnt2 = list(self.G.successors(self.entityNode2))[0]

						# get the node descendants from the second entity
						result += self.toolGetNodeDescendants(self.entityNode2, udrEnt2, posEnt2, fixed=True)

						result = self.getTextFromNodeList(result)
						self.setResult({'result':result}, 6)
						break

	def subjectPredicateObjectRelationship(self, nmethod):
		result = []
		method = ""
		udrNode = ['aux','advmod','appos','compound','mark','case','det','obj','obl','nsubj'] # 'obj' and 'obl' are special cases
		posNode = ['NOUN','ADV','AUX','PRON','ADP','DET','ADJ','SCONJ','PROPN']
		udrNoun, posNoun = ['case','det','amod','mark'], ['ADP','DET','ADJ','SCONJ']
		udrEnt2, posEnt2 = ['case','det','cc','mark','aux','amod','cop','nmod'], ['ADP','DET','CONJ','SCONJ','AUX','ADJ','NOUN']

		focusNode = self.getIntersectionNode('VERB')
		if focusNode>0:
			pathent1 = list(self.getSimplePathBetweenNodes(self.entityNode1, focusNode))
			pathent2 = list(self.getSimplePathBetweenNodes(self.entityNode2, focusNode))
			rel1 = self.edgeLabels[pathent1[-2],focusNode]
			rel2 = self.edgeLabels[pathent2[-2],focusNode]
			if rel1 in ['nsubj'] and rel2 in ['obl','obj']: # first entity is the subject and the second entity is the object/obl

				ancestorFocusNode = list(self.G.successors(focusNode))[0]
				nfather = self.toolGetFatherNode(focusNode, ancestorFocusNode, ['ccomp','xcomp'], ['VERB'])
				if nfather['status']:
					result.append(nfather['node'])
					result.append(focusNode)
				else: result.append(focusNode)

				result += self.toolGetFocusNodeDescendants(focusNode, udrNode, posNode, udrNoun, posNoun, nodeTowardsE2=pathent2[-2], pronoun=True, propernoun=True, adjective=True, adverb=True)
				tmp = self.toolGetNodeDescendants(self.entityNode2, udrEnt2, posEnt2, fixed=True, aux=True)
				result = self.getTextFromNodeList(result, True)
				if len(tmp)>0:
					tmp = self.getTextFromNodeList(tmp, order=True)
					result = '{}_{}'.format(result, tmp)
				# method = '{} E1'.format(method)
				self.setResult({'result':result}, 8)

			elif rel2 in ['nsubj'] and rel1 in ['obl','obj']: # first entity is the subject and the second entity is the object/obl

				ancestorFocusNode = list(self.G.successors(focusNode))[0]
				nfather = self.toolGetFatherNode(focusNode, ancestorFocusNode, ['ccomp','xcomp'], ['VERB'])
				if nfather['status']:
					result.append(nfather['node'])
					result.append(focusNode)
				else: result.append(focusNode)

				result += self.toolGetFocusNodeDescendants(focusNode, udrNode, posNode, udrNoun, posNoun, nodeTowardsE2=pathent1[-2], pronoun=True,propernoun=True, adjective=True, adverb=True)
				lastNodes = self.toolGetNodeDescendants(self.entityNode1, udrEnt2, posEnt2, fixed=True, aux=True)

				result.sort()
				lastNodes.sort()
				result = self.getTextFromNodeList(result+lastNodes, order=False)
				# method = '{} E2'.format(method)
				self.setResult({'result':result}, 9, order=False)

	def jobRelation(self):
		"""Job Relation"""
		flag = True
		relationPattern = {
			'PER-ORG': 'desempeña_sus_funciones_en',
			'PER-PEX': 'desempeña_sus_funciones_en',
			'TIT-PER': 'es_el_título_de',
			'ORG-PER': 'es_donde_desempeña_sus_funciones',
			'PEX-PER': 'es_donde_desempeña_sus_funciones',
			'TIT-ORG': 'es_un_puesto_de_trabajo_en',
			'TIT-PEX': 'es_un_puesto_de_trabajo_en',
			'PER-TIT': 'tiene_el_título_de',
			'ORG-TIT': 'tiene_un_puesto_de_trabajo_con_el_título_de',
			'PEX-TIT': 'tiene_un_puesto_de_trabajo_con_el_título_de',
		}

		childs = list(self.G.predecessors(self.entityNode2))

		# option 1 to find job relationships
		for child in childs:
			if self.nodeLabels[child]['pos']=='PUNCT' \
				and (self.nodeLabels[child]['text']==',' \
					or self.nodeLabels[child]['text']=='(' \
					or self.nodeLabels[child]['text']==';') \
				and self.entitiesPattern in relationPattern:
				self.setResult({'result':relationPattern[self.entitiesPattern]}, 1)
				flag = False
				break
		# option 2 to find job relationships
		if flag:
			father = list(self.G.successors(self.entityNode2))[0]
			if self.edgeLabels[(self.entityNode2, father)]=='flat' and self.entitiesPattern in relationPattern:
				self.setResult({'result':relationPattern[self.entitiesPattern]}, 1)


	def acronymOfRelation(self):
		"""Acronym relation"""
		tmpRes = 0
		result = {}
		acronymTagsUnallowed = ['MNY','DAT','TIM','AGE','PRC','DEM'] # entities without acronym
		childs = list(self.G.predecessors(self.entityNode2))
		if len(childs)>=2:
			for child in childs:
				if self.nodeLabels[child]['pos']=='PUNCT' \
					and (self.nodeLabels[child]['text']=='(' or self.nodeLabels[child]['text']==')') \
					and self.entityTag1==self.entityTag2 \
					and (self.entityTag1 not in acronymTagsUnallowed \
					and self.entityTag2 not in acronymTagsUnallowed):
					tmpRes += 1 # counting parentheses
			if tmpRes==2:
				self.setResult({'result':'es_acrónimo_de'}, 2)

	def representativeOfRelation(self):
		"""Is representative of"""
		import networkx as nx

		relationPattern = ['GPE-PER']
		if self.entitiesPattern in relationPattern:
			path = list(nx.all_simple_paths(self.G, source=self.entityNode2, target=self.entityNode1))
			if len(path) > 0:
				path = path.pop(0)
				tmp_udrs = {}
				tmp_udrs.update({
					(self.edgeLabels[(path[0],path[1])], path[0], path[1]):
					[self.nodeLabels[path[0]], self.nodeLabels[path[1]]],
				})
				childs = list(self.G.predecessors(self.entityNode2))
				childs = list(self.G.predecessors(self.entityNode2))
				if len(path) == 2 and len(childs) > 0:
					tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
					tmp_keys = [item[0] for item in tmp_udrs]
					if len(tmp_udrs)==3:
						if tmp_keys[0]=='flat'\
							and (tmp_keys[1]=='punct'\
								or tmp_keys[1]=='case'):
							tmp_aux_text = [tmp_udrs[k][0]['text'] for k in tmp_udrs]
							tmp_aux_pos = [tmp_udrs[k][0]['pos'] for k in tmp_udrs]
							if tmp_aux_text[2]==',': # verify if there's comma: ,
								self.setResult({'result':'es_representado_por'}, 4)
							elif tmp_aux_pos[2]=='ADP': # verify if there's comma: ,
								self.setResult({'result':'es_representado_por'}, 4)
				elif len(path) == 3:
					tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
					tmp_keys = [item[0] for item in tmp_udrs]
					if len(tmp_udrs)==3:
						if tmp_keys[0]=='appos'\
							and tmp_keys[1]=='appos':
							tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs]
							if tmp_aux_text[1]=='NOUN':
								self.setResult({'result':'es_representado_por'}, 4)

	def isLocatedAtRelation(self):
		"""Is located at"""
		import networkx as nx

		relationPattern = {
			'FAC-GPE': 'se_localiza_en',
			'ORG-GPE': 'que_pertenece_a'
		}
		result = relationPattern.get(self.entitiesPattern, '')
		if self.entitiesPattern in relationPattern:
			path = list(nx.all_simple_paths(self.G, source=self.entityNode2, target=self.entityNode1))
			if len(path) > 0:
				path = path.pop(0)
				tmp_udrs = {}
				tmp_udrs.update({
					(self.edgeLabels[(path[0],path[1])], path[0], path[1]):
					[self.nodeLabels[path[0]], self.nodeLabels[path[1]]],
				})
				childs = list(self.G.predecessors(self.entityNode2))
				if len(path) == 2:
					if len(childs) > 0:
						tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
						tmp_keys = [item[0] for item in tmp_udrs]
						if len(tmp_udrs)==3:
							if (tmp_keys[0]=='flat'\
								or tmp_keys[0]=='nmod'\
								or tmp_keys[0]=='appos')\
								and ('case' in tmp_keys\
								or 'det' in tmp_keys\
								or 'punct' in tmp_keys):
								if 'punct' in tmp_keys: # verify if there're parenthesis: ( )
									tmp_aux = [tmp_udrs[k][0]['text'] for k in tmp_udrs if k[0][0]=='punct']
									if '(' in tmp_aux and ')' in tmp_aux:
										self.setResult({'result':result}, 3)
								elif 'det' in tmp_keys: # verify if there're: case and det
									tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs if k[0][0]=='case' or k[0][0]=='det']
									if 'ADP' in tmp_aux and 'DET' in tmp_aux:
										self.setResult({'result':result}, 3)
								else:
									self.setResult({'result':result}, 3)
						elif len(tmp_udrs)<3:
							if (tmp_keys[0]=='flat'\
								or tmp_keys[0]=='nmod'\
								or tmp_keys[0]=='appos')\
								and (tmp_keys[1]=='case'\
								or tmp_keys[1]=='det'):
								if 'det' in tmp_keys: # verify if there're: case and det
									tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs if k[0][0]=='case' or k[0][0]=='det']
									if 'ADP' in tmp_aux and 'DET' in tmp_aux:
										self.setResult({'result':result}, 3)
								else:
									self.setResult({'result':result}, 3)


					# -------------------------------------------------------------------
				elif len(path) == 3:
					if len(childs) > 0:
						tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
						tmp_keys = [item[0] for item in tmp_udrs]
						if len(tmp_keys)==3:
							if tmp_keys[0]=='appos'\
								and tmp_keys[1]=='nmod'\
								and tmp_keys[2]=='case':
								tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs]
								if tmp_aux[1]=='NOUN' and tmp_aux[3]=='ADP':
									self.setResult({'result':'se_localiza_en'}, 3)
							if tmp_keys[0]=='conj'\
								and tmp_keys[1]=='flat'\
								and tmp_keys[2]=='case':
								tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs]
								if tmp_aux[1]=='PROPN' and tmp_aux[3]=='ADP':
									self.setResult({'result':'se_localiza_en'}, 3)
				elif len(path) == 4:
					if len(childs) > 0:
						tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
						tmp_keys = [item[0] for item in tmp_udrs]
						if len(tmp_keys)==4:
							if tmp_keys[0]=='amod'\
								and tmp_keys[1]=='obj'\
								and tmp_keys[2]=='nmod'\
								and tmp_keys[3]=='case'\
								and tmp_keys[4]=='det':
								tmp_aux = [tmp_udrs[k][0]['pos'] for k in tmp_udrs]
								if tmp_aux[1]=='ADJ' and tmp_aux[2]=='NOUN' and tmp_aux[4]=='ADP' and tmp_aux[5]=='DET':
									self.setResult({'result':'se_localiza_en'}, 3)

				elif len(path) > 4:
					if len(childs) > 0:
						tmp_udrs.update({(self.edgeLabels[(child,self.entityNode2)], child, self.entityNode2):[self.nodeLabels[child], self.nodeLabels[self.entityNode2]] for child in childs})
						tmp_keys = [item[0] for item in tmp_udrs]
						if len(tmp_keys)>4:
							flag = False
							for key in tmp_keys[:-2]:
								if key=='flat': flag=True
								else:
									flag = False
									break
							if flag:
								self.setResult({'result':'se_localiza_en'}, 3)


	def getRelations(self):
		"""main function, read data and extract relations"""
		import sys, json
		import networkx as nx
		print ("The main process has started!\n")
		with open(self.inputData, 'r') as f:
			for indxdoc, document in enumerate(f):
				if len(self.interval)>0:
					if indxdoc<(self.interval[0]-1): continue
					if indxdoc>(self.interval[1]-1): break
				sys.stdout.write('\tProcessing {} documents...\r'.format(format(indxdoc+1),',d'))
				sys.stdout.flush()
				document = document.replace('\n','').split('\t')
				self.indexSntCorpus = indxdoc + 1
				self.idDocument = int(document.pop(0))
				self.statistics['documents'] += 1
				for self.idSentence, sentence in enumerate(document):
					sentence = self.removeEntitiesFromSentence(sentence)
					self.allEntities = {nent:word for nent, word in enumerate(sentence.split()) if '_' in word}

					if len(self.allEntities) >= 2:
						sentences = self.generateSentencesWithTwoEntities(sentence)
						for genidx, genSentence in enumerate(sentences):
							genSentence = self.replaceHypenToUnderscore(genSentence)
							genSentence = genSentence.replace('-',' ') # a mistake is avoided when the sentence words are recovered from the json format
							self.sentence = genSentence # store sentence for print in any function
							self.dpDocument = self.nlp(genSentence)
							self.G = self.jsonToMultiDigraph(self.dpDocument.to_json())
							self.twoEntities = self.getEntitiesFromJson(self.dpDocument.to_json())

							# ENTITIES EXCEPTIONS: NOT compute this kind of entities
							sameException = self.twoEntities[0][1]
							sameException = ' '.join(sameException.split('_')[:-1]).lower()
							if sameException=='grupo puntual': continue

							self.nodeLabels = {i:t for i, t in self.G.nodes(data=True)}
							self.edgeLabels = {item[:2] : item[2]['dep'] for item in self.G.edges.data()}
							self.posLabels = [npos for __, npos in list(self.G.nodes(data='pos'))]

							# ......................................................................................................................
							if self.makeTree: # draw dependency tree per sentence
								# drawDependecyTree(digraph, figurename='tmp_tree', fmt='png', view=False)
								self.drawDependecyTree(self.json2digraph(self.dpDocument.to_json()), "imgs/{}_{}_{}_{}_borrar".format(indxdoc+1, self.idDocument, self.idSentence, genidx))
							# ......................................................................................................................

							if len(self.getSimplePathBetweenNodes(self.twoEntities[0][0], self.twoEntities[1][0])) > 0:
								self.setCurrentEntityParameters(1,0,self.twoEntities[1][0], self.twoEntities[0][0]) # set current ORDER from entities to do the relation extraction process

								if self.checkConjunction(): continue # There's a conjunction between two entities (nodes), relation doesn't exist
								# self.nodesSameBranch()

								self.pathBetweenTwoEntities = self.getSimplePathBetweenNodes(self.twoEntities[0][0], self.twoEntities[1][0])
								if self.entityNode1 in self.pathBetweenTwoEntities: self.pathBetweenTwoEntities.remove(self.entityNode1)
								if self.entityNode2 in self.pathBetweenTwoEntities: self.pathBetweenTwoEntities.remove(self.entityNode2)

								if len(self.candidates)==0: self.jobRelation()
								if len(self.candidates)==0: self.acronymOfRelation()
								if len(self.candidates)==0: self.representativeOfRelation()
								if len(self.candidates)==0: self.isLocatedAtRelation()

								if len(self.candidates)==0: self.verbBetweenEntities()
								if len(self.candidates)==0: self.apposBetweenEntities()
								if len(self.candidates)==0: self.amodBetweenEntities()

							elif len(self.getSimplePathBetweenNodes(self.twoEntities[1][0], self.twoEntities[0][0])) > 0:
								self.setCurrentEntityParameters(0,1,self.twoEntities[0][0], self.twoEntities[1][0]) # set current ORDER from entities to do the relation extraction process

								if self.checkConjunction(): continue # There's a conjunction between two entities (nodes), relation doesn't exist

								self.pathBetweenTwoEntities = self.getSimplePathBetweenNodes(self.twoEntities[1][0], self.twoEntities[0][0])
								if self.entityNode1 in self.pathBetweenTwoEntities: self.pathBetweenTwoEntities.remove(self.entityNode1)
								if self.entityNode2 in self.pathBetweenTwoEntities: self.pathBetweenTwoEntities.remove(self.entityNode2)

								if len(self.candidates)==0: self.jobRelation()
								if len(self.candidates)==0: self.acronymOfRelation()
								if len(self.candidates)==0: self.representativeOfRelation()
								if len(self.candidates)==0: self.isLocatedAtRelation()

								if len(self.candidates)==0: self.verbBetweenEntities()
								if len(self.candidates)==0: self.apposBetweenEntities()
								if len(self.candidates)==0: self.amodBetweenEntities()

							else:
								if len(self.candidates)==0:
									self.setCurrentEntityParameters(0,1,self.twoEntities[0][0], self.twoEntities[1][0]) # set current ORDER from entities
									self.subjectPredicateObjectRelationship('E1')
								if len(self.candidates)==0:
									self.setCurrentEntityParameters(1,0,self.twoEntities[1][0], self.twoEntities[0][0]) # set current ORDER from entities
									self.subjectPredicateObjectRelationship('E2')

							if len(self.candidates)>0:
								self.countSntsUsed += 1
								candidates = eval(self.candidates[0])
								data = {
									'id': self.countSntsUsed,
									'dId': self.idDocument,
									'sId': self.idSentence,
									'ent1': '_'.join( candidates[0].split('_')[:-1] ),
									'tag1': candidates[0].split('_')[-1],
									'ent2': '_'.join( candidates[1].split('_')[:-1] ),
									'tag2': candidates[1].split('_')[-1],
									'rel': candidates[2],
									'opt': candidates[3],
									'snt': genSentence,
								}
								if candidates[3] not in self.statistics['methods']:
									self.statistics['methods'][candidates[3]] = 1
								else:
									self.statistics['methods'][candidates[3]] += 1

								if self.flagtosave: # if true save results to file
									my_data = f"{data['id']}\t{data['dId']}\t{data['sId']}\t{data['ent1']}\t{data['tag1']}\t{data['rel']}\t{data['ent2']}\t{data['tag2']}\t{data['opt']}\t{data['snt']}\n"
									self.saveToFile(self.outputData, my_data)

								self.candidates = []
								self.statistics['snts_used'] += 1
							else:
								self.statistics['snts_diss'] += 1
								self.countSntsRejected += 1
		f.close() # close inputData file
		print ('\n\nThe main process has finished!\n')
