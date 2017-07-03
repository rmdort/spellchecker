# Ola Spellchecker


Reference for Word probability
http://www.katrinerk.com/courses/python-worksheets/language-models-in-python

1. Need to match word case (DONE)
2. Preserve spaces (DONE)
3. Word not in corpus wont be spell corrected
4. Handle multiple spelling mistakes in one sentence `Ther is nthing wrng` (DONE)

### Questions
Following https://www.microsoft.com/cognitive-services/en-us/bing-spell-check-api

1. To handle broken words (microso ft) => Use this https://github.com/grantjenks/wordsegment ?
2. Slang => Synonyms
3. Names => Our lookup store
4. Homonyms => Supported
5. Brands => Our lookup store

## Usage

````
pip install -e git+ssh://git@gitlab.com/olasearch/ola_spellchecker.git#egg=ola_spellchecker
````

## Requirements

1. Python
2. NLTK


## Usage

````
from ola_language_tools import SpellCheck

# Create an instance of the class
spellchecker = SpellCheck(corpus='spellcheck-corpus.txt')

print spellchecker.correct('Wher is everone?')
````

## How it works

1. Create a dictionary out of a large corpus of text
2. Identify spell mistake for each word in the query
3. Find the probability of co-occurence of each mis-spelled word correction
4. Use the best probable match as replacement
