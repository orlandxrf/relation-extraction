# relation-extraction
Relation Extraction approach using the dependency trees to identify and extract relationships between two named entities under Mexican Spanish news documents.

## Corpus
The experiments were carried using <code>data/political_corpus_labeled.txt</code> with 10K documents and <code>data/random_political_corpus_labeled.txt</code> with 300 documents. The documents are about political new in Mexican Spanish.

## Requirements
The requirements include some Python libraries that are listed below:

- Install Spacy
	<code>pip install -U pip setuptools wheel</code>
	<code>pip install -U spacy</code>
	<code>python -m spacy download es_core_news_md</code>

## Results
The experiment with the dataset **data/random_political_corpus_labeled** to extract relationships is depicted in the next tables. In the first Table

| Code | Method used | Total
| ---: | :--- | ---: |
| 1 | Job relationships | 622 |
| 8 | subject (Entity 1), predicate(verb), object(Entity 2) | 604 |
| 2 | Acronym relationships | 159 |
| 9 | subject (Entity 2), predicate(verb), object(Entity 1) | 137 |
| 7 | Relationship in which at least one verb exists between Entity 1 and Entity 2 | 88 |
| 5 | Using the universal dependency 'appos' | 23 |
| 6 | Using the universal dependency 'amod' | 19 |
| 3 | Relationship 'located at' | 4 |

