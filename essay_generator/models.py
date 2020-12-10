from typing import Dict, Tuple
from math import log
from string import punctuation
import re
from tqdm import tqdm
from heapq import nlargest

from django.db import models
from pymorphy2 import MorphAnalyzer
from transliterate import translit
from spacy.lang.ru import Russian
from spacy.lang.ru import STOP_WORDS
from gensim.summarization import summarize, keywords

from django.core.cache import cache

MORPH = MorphAnalyzer()
punctuation += '«—» '


# Create your models here.
class Document(models.Model):
    title = models.CharField(max_length=1000)
    text = models.TextField(max_length=10000)

    def word_frequencies(self) -> Dict[str, int]:
        key = translit(self.title, 'ru', reversed=True) + ':word_frequencies'
        res = cache.get(key)
        if res is None:
            words = self.text.split()
            frequencies = {}
            for word in words:
                if word not in punctuation:
                    word = word.strip(punctuation)
                    word = MORPH.parse(word)[0].normalized
                    if not ('PREP' in word.tag or 'CONJ' in word.tag or 'PRCL' in word.tag or 'INTJ' in word.tag):
                        if word.word not in frequencies.keys():
                            frequencies[word.word] = 1
                        else:
                            frequencies[word.word] += 1
            res = frequencies
            cache.set(key, res, 300)
        return res

    @staticmethod
    def tf(t: str, text: str) -> int:
        t = MORPH.parse(t)[0].normalized.word
        frequency = 0
        for word in text.split():
            if word not in punctuation:
                word = word.strip(punctuation)
                word = MORPH.parse(word)[0].normalized
                if t == word.word:
                    frequency += 1
        return frequency

    def tf_max(self) -> int:
        key = translit(self.title, 'ru', reversed=True) + ':tf_max'
        res = cache.get(key)
        if res is None:
            res = max(self.word_frequencies().values())
            cache.set(key, res, 300)
        return res

    @staticmethod
    def posd(sent: str, doc: str) -> float:
        return 1 - len(doc.partition(sent)[0]) / len(doc)

    @classmethod
    def posp(cls, sent: str, doc: str) -> float:
        paragraphs = doc.split('\n\n')
        paragraph = ''
        for p in paragraphs:
            if sent in p:
                paragraph = p
                break
        return cls.posd(sent, paragraph)

    @classmethod
    def pos_d_p(cls, sent: str, doc: str) -> Tuple[float, float]:
        return cls.posd(sent, doc), cls.posp(sent, doc)

    @classmethod
    def docs_count(cls) -> int:
        return cls.objects.count()

    @classmethod
    def df(cls, t: str) -> int:
        count = 0
        for doc in cls.objects.all():
            if t in doc.word_frequencies().keys():
                count += 1
        return count

    def w(self, t: str) -> float:
        return 0.5 * (1 + Document.tf(t, self.text) / self.tf_max()) * log(Document.docs_count() / Document.df(t))

    def score(self, sent: str) -> float:
        sc = 0.0
        terms = sent.split()
        for t in terms:
            t = t.strip(punctuation)
            t = MORPH.parse(t)[0].normalized
            if not ('PREP' in t.tag or 'CONJ' in t.tag or 'PRCL' in t.tag or 'INTJ' in t.tag):
                t = t.word
                sc += Document.tf(t, sent) * self.w(t)
        return sc

    def sentence_scores(self) -> Dict[str, float]:
        scores = {}
        sentences = re.split(r'[.!?]\s', self.text)
        for sentence in tqdm(sentences):
            if not sentence == '':
                sentence = sentence.strip(punctuation + '\n')
                scores[sentence] = self.score(sentence)
        return scores

    def spacy_sentence_scores(self) -> Dict[str, float]:
        nlp = Russian()
        sentencizer = nlp.create_pipe('sentencizer')
        nlp.add_pipe(sentencizer)

        raw_text = self.text
        docx = nlp(raw_text)
        stopwords = list(STOP_WORDS)

        word_frequencies = {}
        for word in docx:
            if word.text not in stopwords:
                word = MORPH.parse(word.text)[0].normalized
                if not ('PREP' in word.tag or 'CONJ' in word.tag or 'PRCL' in word.tag or 'INTJ' in word.tag):
                    if word.word not in word_frequencies.keys():
                        word_frequencies[word.word] = 1
                    else:
                        word_frequencies[word.word] += 1

        maximum_frequency = max(word_frequencies.values())

        for word in word_frequencies.keys():
            word_frequencies[word] = (word_frequencies[word] / maximum_frequency)
        sentence_list = [sentence for sentence in docx.sents]

        sentence_scores = {}
        for sent in sentence_list:
            for word in sent:
                word = MORPH.parse(word.text)[0].normalized
                if not ('PREP' in word.tag or 'CONJ' in word.tag or 'PRCL' in word.tag or 'INTJ' in word.tag):
                    if word.word in word_frequencies.keys():
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word.word]
                        else:
                            sentence_scores[sent] += word_frequencies[word.word]

        return sentence_scores

    def spacy_summary(self):
        sentence_scores = self.spacy_sentence_scores()
        summary_sentences = nlargest(10, sentence_scores, key=sentence_scores.get)
        final_sentences = [w.text for w in summary_sentences]
        summary = re.sub('\n+', ' ', ' '.join(final_sentences))
        return summary

    def gensim_summary(self):
        return ' '.join(summarize(self.text, split=True))

    def own_summary(self):
        sentence_scores = self.sentence_scores()
        summary_sentences = nlargest(10, sentence_scores, key=sentence_scores.get)
        summary = re.sub('\n+', ' ', ' '.join(summary_sentences))
        return summary

    def keywords(self):
        return keywords(self.text, words=10, split=True)
