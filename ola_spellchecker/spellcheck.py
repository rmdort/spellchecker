# encoding=utf8
import nltk
import os
import re
import logging
from nltk.tokenize import WhitespaceTokenizer
from .symspell_python import get_suggestions, create_dictionary
import inflect

# Enable logging
logging.basicConfig(level=logging.DEBUG)

# Tokenizer
tokenizer = WhitespaceTokenizer()
sentence_tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer()
engine = inflect.engine()

class SpellCheck ():
  def __init__ (self, corpus = os.path.join(os.path.dirname(__file__), 'big.txt')):
    # create a 2 gram from brown corpus
    # This is used to check probability of words next to each other
    logging.info ('Loading corpus')
    # Add brown + corpus words
    with open(corpus) as c:
      text = c.read()
      corpus_sentences = sentence_tokenizer.tokenize(text.decode('utf-8'))
      corpus_words = [word for sent in corpus_sentences for word in tokenizer.tokenize(sent)]

      # final_words = [word for word in brown.words() + corpus_words]
      final_words = corpus_words
      self.cfreq_brown_2gram = nltk.ConditionalFreqDist(nltk.bigrams(final_words))
      self.cprob_brown_2gram = nltk.ConditionalProbDist(self.cfreq_brown_2gram, nltk.MLEProbDist)
      self.freq_brown_1gram = nltk.FreqDist(final_words)
      self.len_brown = len(final_words)

      self.cache = dict()
      self.cache_suggestion = dict()

      # Create dictionary
      create_dictionary(corpus_sentences)

    ## Create homonym dictionary
    logging.info ('Creating homonym dictionary')
    homonym_file = os.path.join(os.path.dirname(__file__), 'homonyms.txt')
    self.homonym_dictionary = {}
    with open(homonym_file) as file:
      for line in file:
        words = line.rstrip('\n').split(' / ')
        for word in words:
          if word in self.homonym_dictionary:
            self.homonym_dictionary[word].append((word, (0,1)))
          else:
            self.homonym_dictionary[word] = [(word, (0,1)) for word in words]

  def unigram_prob (self, word):
    return float(self.freq_brown_1gram[word])/self.len_brown

  def full_sentence_prob (self, words):
    len_words = len(words)
    prob = 0
    for x in range(0, len_words):
      prob += float(self.adjacent_prob(words[x], words[x + 1]) if x != len_words - 1 else self.unigram_prob(words[len_words - 1]))
    return prob

  def bigram_prob (self, idx, word, words):
    len_words = len(words) - 1
    unigram_prob = self.unigram_prob(word)

    if idx == 0:
      return unigram_prob * (self.adjacent_prob(word, words[idx + 1]) if idx != len_words else 1)

    if idx == len_words:
      last_word_adj_prob = self.adjacent_prob(word, words[idx - 1], True)
      return unigram_prob * (1 if last_word_adj_prob == 0 else last_word_adj_prob)

    return (self.adjacent_prob(word, words[idx - 1], True) + self.adjacent_prob(word, words[idx + 1])) + unigram_prob

  def adjacent_prob (self, word, adjacent_word, reverse=False):
    if reverse:
      key = ''.join([adjacent_word, word])
    else:
      key = ''.join([word, adjacent_word])

    if key in self.cache:
      return self.cache[key]

    spell_sug = [(term, freq) for term, freq in self.get_word_suggestions(adjacent_word) if freq[1] > 0]
    final_prob = 0
    max_prob = 0
    if len(spell_sug) > 0:
      for suggestion, freq in spell_sug:
        word_prob = self.calculate_prob(word, suggestion) if reverse is False else self.calculate_prob(suggestion, word)
        if word_prob > max_prob:
          max_prob = word_prob
      final_prob = max_prob
    else:
      final_prob = self.calculate_prob(word, adjacent_word) if reverse is False else self.calculate_prob(adjacent_word, word)

    self.cache[key] = final_prob

    return self.cache[key]

  def calculate_prob (self, a, b):
    return (
      self.cprob_brown_2gram[a].prob(b) +
      self.cprob_brown_2gram[a].prob(engine.plural(b)) +
      self.cprob_brown_2gram[engine.plural(a)].prob(b)
    )

  def match_case (self, source_word, corrected_word):
    if source_word[0].isupper():
      return corrected_word[:1].upper() + corrected_word[1:]
    return corrected_word

  def get_word_homonyms (self, word):
    if word in self.homonym_dictionary:
      return self.homonym_dictionary[word]
    return []

  def word_case_probability (self, suggestions):
    def find_max_prob (sug):
      word, freq = sug
      variations = [word] + [word[:1].upper() + word[1:]]
      max_prob = 0
      correct_word = word
      for word in variations:
        prob = self.unigram_prob(word)
        if prob > max_prob:
          max_prob = prob
          correct_word = word
      return correct_word, freq
    return map(find_max_prob, suggestions)

  def get_word_suggestions (self, word):
    if word in self.cache_suggestion:
      return self.cache_suggestion[word]
    self.cache_suggestion[word] = get_suggestions(word, True) + self.get_word_homonyms(word)
    return self.cache_suggestion[word]

  def correct (self, sentence, debug=False):
    words_case_preserved = [word for word in tokenizer.tokenize(sentence)]
    words = [word for word in words_case_preserved]
    # sentence_prob = self.full_sentence_prob(words)
    # Todo: Addon sentence probability
    for idx, word in enumerate(words):
      correct_word = None
      max_prob = 0
      suggestions = self.word_case_probability(self.get_word_suggestions(word))[:5]
      suggestions = list(set(suggestions))
      fqs = [freq[1] for _, freq in suggestions]

      if len(fqs) > 0 and fqs.count(fqs[0]) == len(fqs) and len(fqs) > 1:
        suggestions = []

      for suggestion, freq in suggestions:
        if freq[0] <=0:
          continue
        if freq[1] > 0:
          word_prob = self.bigram_prob(idx, suggestion, words) # * sentence_prob
          # print (suggestion, word_prob)
          if word_prob <= 0:
            continue
          # Debug
          if debug:
            logging.info (idx, word, suggestion, freq, word_prob)
          if word_prob > max_prob:
            max_prob = word_prob
            correct_word = self.match_case(words_case_preserved[idx], suggestion)
      if correct_word is not None:
        sentence = re.sub(r'\b' + word + r'\b', correct_word, sentence, flags=re.IGNORECASE)

    return sentence
