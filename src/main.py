import math
import sys

import stanza
import re
import csv
from pandas.io import json

# -*- coding: utf-8 -*-
stanza.download('es')


def process(nlp, text):
    return nlp(text)


def load_adjectives():
    d = {}
    with open('newdata/adjective-grammar.csv', "r", encoding="ISO-8859-1") as infile:
        reader = csv.reader(infile, delimiter=';')
        for line in reader:
            d[line[0]] = line[1:]
    return d


def load_adverbs():
    d = {}
    with open('newdata/adverb-grammar.csv', "r", encoding="ISO-8859-1") as infile:
        reader = csv.reader(infile, delimiter=';')
        for line in reader:
            d[line[0]] = line[1:]
    return d


def load_nouns():
    d = {}
    with open('newdata/noun-grammar.csv', "r", encoding="ISO-8859-1") as infile:
        reader = csv.reader(infile, delimiter=';')
        for line in reader:
            d[line[0]] = line[1:]
    return d


def load_verbs():
    d = {}
    with open('newdata/verb-grammar.csv', "r", encoding="ISO-8859-1") as infile:
        reader = csv.reader(infile, delimiter=';')
        for line in reader:
            d[line[0]] = line[1:]
    return d


def load_negations():
    negators = ["no", "ni", "nunca", "jam" + chr(225) + "s", "nada", "nadie", "ninguno", "ningunos", "ninguna",
                "ningunas", "faltar", "falta", "sin"];
    return negators


def load_punt():
    punct = [".", ",", ";", "!", "?", ":", ")", "(", "\"", "'", "-", chr(161), chr(191)]
    return punct


def load_disjunctives():
    disj = ["o", "u"]
    return disj


def load_ontology():
    d = {}
    with open('newdata/ontology-spanish.csv', "r", encoding="ISO-8859-1") as infile:
        reader = csv.reader(infile, delimiter=';')
        for line in reader:
            d[line[0]] = line[1:]
    return d


def load_positives_hashtags():
    with open("newdata/hashtags.csv") as source:
        grammar = csv.reader(source, delimiter=";")
        corp = [row[0] for row in grammar if len(row) == 2 and row[1] == "positive"]
    return corp


def load_negatives_hashtags():
    with open("newdata/hashtags.csv") as source:
        grammar = csv.reader(source, delimiter=";")
        corp = [row[0] for row in grammar if len(row) == 2 and row[1] == "negative"]
    return corp


def doc(nlp, tweet):
    doc = process(nlp, tweet)
    return doc


adverbs = load_adverbs()
adjectives = load_adjectives()
nouns = load_nouns()
verbs = load_verbs()
disjunctives = load_disjunctives()
negations = load_negations()
ontology = load_ontology()
positive_hashtags = load_positives_hashtags()
negative_hashtags = load_negatives_hashtags()


def tv(pols):
    root = [p[0] for p in pols if p[1] == 0]
    value, vemotions, strength, negation, disjunction, conjunction, subordinate, qualified, element, json_element_list = tv_rec(
        root[0], pols)
    return value, vemotions, json_element_list


def tv_rec(head, pols):
    full = [p for p in pols if p[0] == head]
    element_full = full[0]
    head_full = element_full[1]
    current = [p[2] for p in pols if p[0] == head]
    element = current[0]
    strength = 0
    negation = 1
    verb_modifier = False
    if element in adjectives.keys():
        evalue = int(adjectives.get(element)[0])
    else:
        if element in nouns.keys():
            evalue = int(nouns.get(element)[0])
        else:
            if element in verbs.keys() and verbs.get(element)[1] == "INTENSIFICACION":
                evalue = 0
                verb_modifier = True
            else:
                if element in verbs.keys() and verbs.get(element)[1] == "DEBILITACION":
                    evalue = 0
                    verb_modifier = True
                else:
                    if element in verbs.keys():
                        evalue = int(verbs.get(element)[0])
                    else:
                        evalue = 0

    if element in positive_hashtags:
        evalue = 10

    if element in negative_hashtags:
        evalue = -10

    if element in negations:
        negation = -1

    if element in adverbs.keys() and adverbs.get(element)[1] == "INTENSIFICACION":
        strength = abs(int(adverbs.get(element)[0]))

    if element in adverbs.keys() and adverbs.get(element)[1] == "DEBILITACION":
        strength = -abs(int(adverbs.get(element)[0]))

    if element in verbs.keys() and verbs.get(element)[1] == "INTENSIFICACION":
        strength = abs(int(verbs.get(element)[0]))

    if element in verbs.keys() and verbs.get(element)[1] == "DEBILITACION":
        strength = -abs(int(verbs.get(element)[0]))

    parent_all = [p for p in pols if p[1] == head]
    disjunction = len([p for p in parent_all if p[2] in disjunctives]) > 0
    conjunction = len([p for p in parent_all if p[3] == 'CCONJ' and p[2] not in disjunctives]) > 0
    subordinate = len([p for p in parent_all if p[3] == 'SCONJ']) > 0
    qualified = len([p for p in parent_all if p[3] == 'ADJ']) > 0

    pemotions = 0
    pstrength = strength
    pnegation = negation
    pvalue = evalue
    pdisjunction = 0
    pconjunction = 0
    psubordinate = 0
    pqualified = 0
    number_disjunctions = 0
    pjson_element_list = []
    parent = [p[0] for p in pols if p[1] == head]
    for p in parent:
        pp = tv_rec(p, pols)
        if pp is not None:
            ppvalue, ppemotions, ppstrength, ppnegation, ppdisjunction, ppconjunction, ppsubordinate, ppqualified, ppelement, \
            ppjson_element = pp
            pjson_element_list = pjson_element_list + ppjson_element
            if ppdisjunction:
                pdisjunction = pdisjunction + ppvalue
                number_disjunctions = number_disjunctions + 1
            elif ppconjunction:
                pconjunction = pconjunction + ppvalue
            elif ppsubordinate:
                psubordinate = psubordinate + ppvalue
            elif ppqualified:
                pqualified = pqualified + ppvalue
            else:
                pvalue = pvalue + ppvalue
                pstrength = pstrength + ppstrength
                pnegation = pnegation * ppnegation
            pemotions = pemotions + ppemotions

    if verb_modifier:
        if pnegation == 1:
            pvalue = (psubordinate + pconjunction + pdisjunction + pvalue + pqualified) * (1 + (strength / 10))
        else:
            pvalue = -(psubordinate + pconjunction + pdisjunction + pvalue + pqualified) * (1 - (strength / 10))
    else:
        if pnegation == 1:
            pvalue = pvalue * (1 + (pstrength / 10))
        else:
            pvalue = -pvalue * (1 - (pstrength / 10))

        pvalue = pvalue * (1 - abs(psubordinate) / 10)
        pvalue = pvalue * (1 - abs(pqualified) / 10)

        if number_disjunctions > 0:
            pvalue = (pvalue + pdisjunction + pconjunction) / number_disjunctions
        else:
            pvalue = pvalue + pconjunction

    json_element = {}
    if head_full == 0:
        type = "Main_Emotion"
    else:
        type = "Emotion"

    if pvalue >= 0:
        interval = math.ceil((pvalue + 1) / 2) + 4
    else:
        interval = math.ceil((pvalue - 1) / 2) + 4

    if element in adjectives.keys() and not adjectives[element][1] == "":
        if interval > 7:
            json_element["Emotion_Polarity"] = "positive"
            json_element["word"] = element
            json_element["polarity"] = pvalue
            pemotions = pemotions + pvalue
            json_element[type] = ontology.get(adjectives[element][1])[7]

        else:
            if interval < 0:
                json_element["Emotion_Polarity"] = "negative"
                json_element["word"] = element
                json_element["polarity"] = pvalue
                pemotions = pemotions + pvalue
                json_element[type] = ontology.get(adjectives[element][1])[0]

            else:
                if interval >= 4:
                    json_element["Emotion_Polarity"] = "positive"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(adjectives[element][1])[interval]
                else:
                    json_element["Emotion_Polarity"] = "negative"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(adjectives[element][1])[interval]

    if element in nouns.keys() and not nouns[element][1] == "":
        if interval > 7:
            json_element["Emotion_Polarity"] = "positive"
            json_element["word"] = element
            json_element["polarity"] = pvalue
            pemotions = pemotions + pvalue
            json_element[type] = ontology.get(nouns[element][1])[7]

        else:
            if interval < 0:
                json_element["Emotion_Polarity"] = "negative"
                json_element["word"] = element
                json_element["polarity"] = pvalue
                pemotions = pemotions + pvalue
                json_element[type] = ontology.get(nouns[element][1])[0]

            else:
                if interval >= 4:
                    json_element["Emotion_Polarity"] = "positive"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(nouns[element][1])[interval]

                else:
                    json_element["Emotion_Polarity"] = "negative"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(nouns[element][1])[interval]

    if element in verbs.keys() and not verbs[element][2] == "":
        if interval > 7:
            json_element["Emotion_Polarity"] = "positive"
            json_element["word"] = element
            json_element["polarity"] = pvalue
            pemotions = pemotions + pvalue
            json_element[type] = ontology.get(verbs[element][2])[7]

        else:
            if interval < 0:
                json_element["Emotion_Polarity"] = "negative"
                json_element["word"] = element
                json_element["polarity"] = pvalue
                pemotions = pemotions + pvalue
                json_element[type] = ontology.get(verbs[element][2])[0]

            else:
                if interval >= 4:
                    json_element["Emotion_Polarity"] = "positive"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(verbs[element][2])[interval]
                else:
                    json_element["Emotion_Polarity"] = "negative"
                    json_element["word"] = element
                    json_element["polarity"] = pvalue
                    pemotions = pemotions + pvalue
                    json_element[type] = ontology.get(verbs[element][2])[interval]

    if len(json_element) > 0:
        pjson_element_list = [json_element] + pjson_element_list

    # print(element, pvalue, pstrength, pnegation,  disjunction, conjunction, subordinate, qualified,pjson_element_list)
    return pvalue, pemotions, pstrength, pnegation, disjunction, conjunction, subordinate, qualified, element, \
           pjson_element_list


def clean_tweet(tweet):
    import numpy as np
    import re
    if type(tweet) == np.float:
        return ""
    temp = tweet.lower()
    temp = re.sub("'", "", temp)
    temp = re.sub("@[A-Za-z0-9_]+", "", temp)
    temp = re.sub(r'http\S+', '', temp)
    temp = re.sub('[()!?]', ' ', temp)
    temp = re.sub('\[.*?\]', ' ', temp)
    temp = re.sub("[^a-z0-9]", " ", temp)
    temp = temp.split()
    temp = " ".join(word for word in temp)
    return temp


def remove_accents(old):
    new = old.lower()
    new = re.sub(r'[àáâãäå]', 'a', new)
    new = re.sub(r'[èéêë]', 'e', new)
    new = re.sub(r'[ìíîï]', 'i', new)
    new = re.sub(r'[òóôõö]', 'o', new)
    new = re.sub(r'[ùúûü]', 'u', new)
    return new


##################
# MAIN PROGRAM
##################





file = sys.argv[1]

import json
with open(file, 'r') as f:
  data = json.load(f)

stweet = [i['text'] for i in data['data']]


nlp = stanza.Pipeline(lang='es')
json_tree = {}
json_list = []
id = 0
for t in stweet:
    t = remove_accents(t)
    t = t.replace(",", " y ").replace(".", " y ").replace(";", " y ").replace(":", " y ").replace("(", " y "). \
        replace(")", " y ").replace("#", " ")
    document = doc(nlp, t)
    id = id + 1
    json_element = {}
    json_element["id"] = id
    json_element["tweet"] = t
    total_polarity = 0
    total_emotions = 0
    json_emotion = {}
    for sent in document.sentences:
        pols = [(word.id, word.head, word.lemma, word.upos) for word in sent.words]
        # print(pols)
        partial_polarity, partial_emotions, json_emotion = tv(pols)
        total_polarity = total_polarity + partial_polarity
        total_emotions = total_emotions + partial_emotions

    json_element['polarity_text'] = total_polarity
    json_element['polarity_emotions'] = total_emotions
    if max(abs(total_polarity), abs(total_emotions)) == abs(total_polarity):
        json_element['total_polarity'] = total_polarity
    else:
        json_element['total_polarity'] = total_emotions
    json_element['Emotions'] = json_emotion
    json_list.append(json_element)

json_tree = json.dumps(json_list)
print(json_tree)
open("out.json", "w").write(json_tree)
