# -*- coding: utf-8 -*-

import fnmatch
import string
import codecs
import random
import os
import re
import collections
import pickle


lastSequenceSymbols = ['?', '.', '!']


def preprocessStat(stat):
    for item1 in stat.items():
        count = 0.0
        for item2 in item1[1].items():
            count += item2[1]
        for item2 in item1[1].items():
            stat[item1[0]][item2[0]] = item2[1]/count


def randomWordFromDistribution(stat):
    value = random.random()
    sum = 0
    for item in stat.items():
        sum += item[1]
        if (sum > value):
            return item[0]
    return -1


def checkWordIsGood(word):
    if len(word) == 0:
        return False
    if word in lastSequenceSymbols:
        return True
    return word[0] in string.letters and word[-1] in string.letters


def escapeTrainingText(text):
    for chr in lastSequenceSymbols:
        text = text.replace(chr, u" {} ".format(chr))
    text = re.sub(u'[{}]'.format(
        #  “”’‘
        re.escape(u"\"#$%&()*+,-/:;<=>@[\]^_`{|}~")), ' ', text)
    text = u" ".join([w for w in text.split(u" ") if checkWordIsGood(w)])
    text = re.sub(u'\s{2,}', u' ', text)
    return text


def collectStatistics(text):
    allWords = sorted(set(escapedText.lower().split(" ")))
    word2id = {}
    id2word = {}
    for i in range(len(allWords)):
        word2id[allWords[i]] = i
        id2word[i] = allWords[i]

    lastSequenceSymbolsIds = [word2id[w] for w in lastSequenceSymbols]
    idsSequence = [word2id[w] for w in escapedText.lower().split(" ")]

    oneWordStat = {}
    twoWordsStat = {}
    for i in range(1, len(idsSequence) - 1):
        firstWord = idsSequence[i-1]
        secondWord = idsSequence[i]
        afterWord = idsSequence[i + 1]

        if firstWord not in twoWordsStat:
            twoWordsStat[firstWord] = {}
        if secondWord not in twoWordsStat[firstWord]:
            twoWordsStat[firstWord][secondWord] = collections.defaultdict(int)
        twoWordsStat[firstWord][secondWord][afterWord] += 1

        if secondWord not in oneWordStat:
            oneWordStat[secondWord] = collections.defaultdict(int)
        oneWordStat[secondWord][afterWord] += 1
    preprocessStat(oneWordStat)
    for item1 in twoWordsStat.items():
        preprocessStat(item1[1])
    return [allWords, word2id, id2word, oneWordStat, twoWordsStat]


def generateRandomText(allWords, word2id, id2word, oneWordStat,
                       twoWordsStat, minWordCount):
    result = u""
    prevSequenceLastWordId = word2id[u'.']
    wordCounter = 0
    while wordCounter < minWordCount:
        assert id2word[prevSequenceLastWordId] in lastSequenceSymbols
        nextAddingWordId = \
            randomWordFromDistribution(oneWordStat[prevSequenceLastWordId])
        if id2word[nextAddingWordId] in lastSequenceSymbols:
            continue

        result += id2word[nextAddingWordId].capitalize()
        wordCounter += 1
        prevAddedWordId, nextAddingWordId = \
            nextAddingWordId, \
            randomWordFromDistribution(oneWordStat[nextAddingWordId])
        if not id2word[nextAddingWordId] in lastSequenceSymbols:
            result += u" {}".format(id2word[nextAddingWordId])
            wordCounter += 1

            maxSentenseSize = 100000
            sentenseWordCount = 1
            while sentenseWordCount < maxSentenseSize:
                sentenseWordCount += 1
                prevAddedWordId, nextAddingWordId = \
                    nextAddingWordId, randomWordFromDistribution(
                        twoWordsStat[prevAddedWordId][nextAddingWordId])
                if id2word[nextAddingWordId] in lastSequenceSymbols:
                    break
                result += u" {}".format(id2word[nextAddingWordId])
                wordCounter += 1

        result += u'{} '.format(id2word[nextAddingWordId])
        wordCounter += 1
        prevSequenceLastWordId = nextAddingWordId
    return result


if __name__ == "__main__":
    minWordCount = 20000
    databasePath = 'corpus/'
    tempDirPath = 'temp/'
    resultFilePath = './result.txt'
    statFilePath = '{}/stat.dat'.format(tempDirPath)
    if not os.path.exists(tempDirPath):
        os.makedirs(tempDirPath)

    if not os.path.exists(statFilePath):
        print("reading data from files...")
        texts = []
        for root, dir, files in os.walk(databasePath):
                for item in fnmatch.filter(files, "*.txt"):
                    textPath = '{}/{}'.format(root, item)
                    with codecs.open(textPath, 'r', encoding='utf8') as f:
                        texts.append(f.read())

        print("escaping data...")
        escapedText = escapeTrainingText(' '.join(texts))

        print("collecting statistics...")
        [allWords, word2id, id2word, oneWordStat, twoWordsStat]\
            = collectStatistics(escapedText)
        with open(statFilePath, 'wb') as f:
            pickle.dump(
                [allWords, word2id, id2word, oneWordStat, twoWordsStat], f)

    print("initialize statistics...")
    with open(statFilePath, 'rb') as f:
        [allWords, word2id, id2word, oneWordStat, twoWordsStat]\
            = pickle.load(f)

    print("generating random text...")
    generatedText = generateRandomText(allWords, word2id, id2word,
                                       oneWordStat, twoWordsStat, minWordCount)
    with codecs.open(resultFilePath, encoding='utf8', mode='w') as f:
        f.write(generatedText)
