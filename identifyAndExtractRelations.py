from relationExtractionTask import RelationExtraction
from datetime import datetime

start_general_time = datetime.now()
entitiesAllowed = {'PER','ORG','TIT','GPE','PEX','FAC','EVT','MNY','DOC','PRO','DEM','AGE','DAT','TIM','ADD','PRC','LOC',}
entitiesUnallowed = {'PRC', 'ADD'}
# Methods or cases in which the relationships were extracted are:
methods = {
	'1':	"Job relationships",
	'2':	"Acronym relationships",
	'3':	"Relationship 'located at'",
	'4':	"Relationship 'is represented by'",
	'5':	"Using the universal dependency 'appos'",
	'6':	"Using the universal dependency 'amod'",
	'7':	"Relationship in which at least one verb exists between Entity 1 and Entity 2",
	'8':	"subject (Entity 1), predicate(verb), object(Entity 2)",
	'9':	"subject (Entity 2), predicate(verb), object(Entity 1)",
}

# -----------------------------------------------------------------------------
# inputCorpus = 'data/political_corpus_labeled.txt'
inputCorpus = 'data/random_political_corpus_labeled.txt'
outputCorpus = 'data/result_extracted_relations.txt'
# -----------------------------------------------------------------------------

# interval = [0, 10] # process 10 documents
# re = RelationExtraction(entitiesUnallowed, inputCorpus, outputCorpus, True, False, interval)
re = RelationExtraction(entitiesUnallowed, inputCorpus, outputCorpus, True, False, [])

"""
Create new output relationshis file or reset existing file
File headers:
	id':	ID relationship
	dId:	Documento ID
	sId:	Sentence ID
	ent1:	First Entity Text
	tag1:	First Entity's Tag
	rel:	Relationship extracted
	ent2:	Second Entity Text
	tag2:	Second Entity's Tag
	opt:	The case or method (1-9) used to extract the relationship
	snt:	Sentence Text
"""
headers = f'id\tdId\tsId\tent1\ttag1\trel\tent2\ttag2\topt\tsnt\n'
re.saveToFile(outputCorpus, headers, 'w')

re.getRelations() # identify and extract relationships

myres = re.statistics['methods'].copy()
myres = dict(sorted(myres.items(), key=lambda x:x[0]))

for x in re.statistics:
	if type(re.statistics[x]) == dict:
		print ( '\t{}:'.format(x) )
		for item in myres:
			print ( '\t\t{}:\t{}. {}'.format(format(myres[item],',d'), item, methods[item]) )
	else:
		print ( '\t{}:\t{}'.format(x, format(re.statistics[x],',d')) )

print ('')
print ('-'*70)
print ('Input corpus: {}'.format(inputCorpus))
print ('Output corpus: {}'.format(outputCorpus))
print ('-'*70)

end_general_time = datetime.now()
print ('\nGeneral Time elapsed: {}\n'.format(end_general_time - start_general_time))
