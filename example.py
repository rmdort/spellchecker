import os
from ola_spellchecker import SpellCheck
import time

# parser = SyntaxParser()
# parser.parse('Show all award winners from Singapore')
# print (parser.parse('I am 21 years old. Can I hire 2 fdw?'))

# Create an instance of the class
spellchecker = SpellCheck(corpus='spellcheck-corpus.txt')

start = time.clock()
print (spellchecker.correct('Can i hire a few from united statesd'))
print (time.clock() - start)
print (spellchecker.correct('phillips is the best compandy I have seen in companyd'))

