# relation-extraction
Relation Extraction approach using the dependency trees to identify and extract relationships between two named entities under Mexican Spanish news documents.

## Corpus
The experiments were carried using <code>data/political_corpus_labeled.txt</code> with 10K documents and <code>data/random_political_corpus_labeled.txt</code> with 300 documents. The documents are about political news in Mexican Spanish.

## Requirements
The requirements include some Python libraries that are listed below:

- Install Spacy, to use the Dependency Parser in Spanish language
	- <code>pip install -U pip setuptools wheel</code>
	- <code>pip install -U spacy</code>
	- <code>python -m spacy download es_core_news_md</code>
- Install <code>pip install -U networkx</code> for use graphs
- To draw the dependency tree install:
	- <code>sudo apt install graphviz</code>
	- <code>pip install -U graphviz</code>

## Results
The experiment with the dataset <code>data/random_political_corpus_labeled.txt</code> to extract relationships is depicted in the next table. Showing the methods to extract relationships as well as the number of relatios extracted.

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

The top 20 frequency relationships extracted are shown below. Most of them are relationships previously defined like job relationships and acronyms. Besides some automatic relationships extracted are in the Table (like numbers 3, 6, 7, 8, and 9).

| No. | Entity1 | Tag1 | Relationship | Entity2 | Tag2 | Frequency |
| ---: | :--- | :---: | :---: | :--- | :---: | ---: |
| 1 | presidente | TIT | *es el t??tulo de* | Andr??s Manuel L??pez Obrador | PER | 61 |
| 2 | gobernador | TIT | *es el t??tulo de* | Ad??n Augusto L??pez Hern??ndez | PER | 32 |
| 3 | UNAM | ORG | *expertos resolver??n preguntas a partir de las* | 15 : 00 horas | TIM | 31 |
| 4 | diputada | TIT | *es el t??tulo de* | Martha Tagle | PER | 25 |
| 5 | secretaria de Cultura | TIT | *es el t??tulo de* | Yolanda Osuna Huerta | PER | 17 |
| 6 | Sinaloa | GPE | *el municipio podr??a recibir una nueva visita de* | AMLO | PER | 16 |
| 7 | Sistema DIF Tabasco | ORG | *sostuvo que con este acto contribuye al crecimiento de la* | biblioteca Pino Su??rez | FAC | 15 |
| 8 | Gobernador | TIT | *entreg?? una en el poblado de* | Comalcalco | GPE | 15 |
| 9 | Gobierno del Estado | ORG | *adelant?? que realiza las gestiones la* | biblioteca Pino Su??rez | FAC | 15 |
| 10 | director general de la Red Estatal de Bibliotecas | TIT | *es el t??tulo de* | Ariel Guti??rrez Valencia | PER | 15 |
| 11 | Instituto Nacional Electoral | ORG | *es acr??nimo de* | INE | ORG | 13 |
| 12 | Gabriela Jim??nez | PER | *desempe??a sus funciones en* | El Sol de M??xico | ORG | 11 |
| 13 | presidente electo | TIT | *es el t??tulo de* | Andr??s Manuel L??pez Obrador | PER | 11 |
| 14 | Partido Acci??n Nacional | PEX | *es acr??nimo de* | PAN | PEX | 10 |
| 15 | Presidente | TIT | *es el t??tulo de* | Andr??s Manuel L??pez Obrador | PER | 10 |
| 16 | Partido Revolucionario Institucional | PEX | *es acr??nimo de* | PRI | PEX | 7 |
| 17 | Partido de la Revoluci??n Democr??tica | PEX | *es acr??nimo de* | PRD | PEX | 7 |
| 18 | presidente de M??xico | TIT | *es el t??tulo de* | Andr??s Manuel L??pez Obrador | PER | 7 |
| 19 | Movimiento de Regeneraci??n Nacional | PEX | *es acr??nimo de* | Morena | PEX | 6 |
| 20 | presidente de Estados Unidos | TIT | *es el t??tulo de* | Donald Trump | PER | 6 |

---
The source paper is [here](https://orlandxrf.github.io/publications/2021_Extraccion_Relaciones.pdf)

Please cite this work as:
<pre>
@article{ramos2021identificacion,
	title={Identificaci{\'o}n y extracci{\'o}n de relaciones entre entidades empleando {\'a}rboles de dependencia},
	author={Ramos-Flores, Orlando and Pinto, David},
	journal={Revista Colombiana de Computaci{\'o}n},
	volume={22},
	number={2},
	pages={22--36},
	year={2021}
}
</pre>
