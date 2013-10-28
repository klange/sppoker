#!/usr/bin/python
# -*- coding: utf-8 -*-
# Internet SPPoker
# SPPoker is a combination of Scrabble and Poker, played with
# special cards, each both a regular playing card value and suit
# and a SPPoker letter. Players are each dealt 7 cards and must
# determine either their best 5-card poker hand or their best
# word to spell with their letters.

import random, string
import encodings.utf_8
rand = random.Random()
deck = {}
deck['P']="A234567890JQKKQJ098765432AA234567890JQKKQJ098765432A****"
deck['L']="GSROPONMLKEIHOPQRSTUVWAYINTFEDCBAZYXWVUBCDEFGHIJKLMAAEIO"
deck['S']="HHHHHHHHHHHHHCCCCCCCCCCCCCDDDDDDDDDDDDDSSSSSSSSSSSSS****"

suits = {}
suits['D'] = u"♦"
suits['H'] = u"♥"
suits['S'] = u"♠"
suits['C'] = u"♣"
suits['*'] = ""

class Card():
    def __init__(self, deck, index):
        self.poker  = deck['P'][index]
        if self.poker == "0":
            self.poker == "10"
        self.letter = deck['L'][index]
        self.suit   = deck['S'][index]
        self.used = False
    def compare_poker(self, other):
        if self.poker == "*" or other.poker == "*":
            print "ERROR: Attempted to compare a wildcard!"
            return 0
        if str(ord(self.poker)) == self.poker:
            if str(ord(other.poker)) == other.poker:
                if int(other.poker) < int(self.poker):
                    return 1
                elif int(other.poker) > int(self.poker):
                    return -1
                else:
                    return 0
            else:
                return -1
        else:
            if str(ord(other.poker)) == other.poker:
                return 1
            else:
                if other.poker == self.poker:
                    return 0
                elif other.poker == "K":
                    return -1
                elif self.poker == "K":
                    return 1
                elif other.poker == "Q":
                    if self.poker == "J":
                        return -1
                    else:
                        return 1
                elif self.poker == "Q":
                    if other.poker == "J":
                        return 1
                    else:
                        return -1
    def compare_letter(self,other):
        if ord(self.letter) > ord(other.letter):
            return 1;
        elif ord(self.letter) < ord(other.letter):
            return -1;
        else:
            return 0;
    def set_wild(self,value,suit):
        if self.poker != "*":
            print "ERROR: Tried to set wild value for non-wild card."
            return 0
        if value == "10":
            value = "0"
        self.poker = upper(value)
        self.suit = upper(suit)
        return 1
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return self.poker + self.letter + self.suit
def dealcard(cards):
    global rand
    if len(cards) == 0:
        print "Out of cards"
        return 0
    return cards.pop(rand.randint(0,len(cards)-1))
def CardFromText(text):
    global deck
    tmp = Card(deck,0)
    try:
        tmp.poker = text[0]
        tmp.letter = text[1]
        tmp.suit = text[2]
    except:
        return 0
    return tmp
def cardValue(name,acehigh=False):
    if name == "K":
        return 13
    if name == "Q":
        return 12
    if name == "J":
        return 11
    if name == "0":
        return 10
    if name == "A":
        if acehigh:
            return 14
        return 1
    if name == "*":
        return -1
    return int(name)
def cardName(name):
    if name == 13:
        return "K"
    if name == 12:
        return "Q"
    if name == 11:
        return "J"
    if name == 10:
        return "0"
    if name == 14 or name == 1:
        return "A"
    return str(name)
def prettyHand(hand):
    tmp = []
    if len(hand) > 0:
        for j in hand:
            c = CardFromText(j)
            p = c.poker
            if p == "*":
                p = u"★"
            tmp.append(p + suits[c.suit])
    return string.join(tmp)
def handType(num):
    if num == "B":
        return "Five of a Kind"
    elif num == "A":
        return "Royal Flush"
    elif num == "9":
        return "Straight Flush"
    elif num == "8":
        return "Four of a Kind"
    elif num == "7":
        return "Full House"
    elif num == "6":
        return "Flush"
    elif num == "5":
        return "Straight"
    elif num == "4":
        return "Three of a Kind"
    elif num == "3":
        return "Two Pair"
    elif num == "2":
        return "Pair"
    elif num == "1":
        return "High Card"
def handToString(hand):
    out = ""
    for card in hand:
        out += card.poker
    return out
def suitToString(hand):
    out = ""
    for card in hand:
        out += card.suit
    return out
def valuesToList(hand):
    out = []
    for card in hand:
        out.append(cardValue(card.poker))
    return out
def bow(hand,card):
    if hand.find(card) != -1:
        return hand.replace(card,"",1)
    elif hand.find("*") != -1:
        return hand.replace("*","",1)
def highcard(hand,ignoreWild=False):
    highest_card = "1"
    highest_value = -2
    for card in hand:
        if card.suit == "*":
            continue
        if cardValue(card.poker,True) > highest_value:
            highest_card = card.poker
            highest_value = cardValue(card.poker)
    return highest_card
def PokerHandRank(hand):
    hs = handToString(hand)
    ss = suitToString(hand)
    vl = valuesToList(hand)
    finalhand = hs[:]
    hcard = 0
    if len(hand) == 5:
        # Five of a Kind
        hsa = hs.replace("*","")
        if len(hsa.replace(hsa[0],"")) == 0:
            if len(hsa) > 0:
                return ("B",cardValue(hsa[0],True))
            else:
                return ("B",14)
    # Royal Flush
    isStraight = False
    isFlush = False
    if hs.find("A") != -1 or hs.find("*") != -1:
        if hs.find("A") == -1:
            finalhand = finalhand.replace("*","A")
        hsb = bow(hs,"A")
        if hsb.find("K") != -1 or hsb.find("*") != -1:
            if hsb.find("K") == -1:
                finalhand = finalhand.replace("*","K")
            hsb = bow(hsb,"K")
            if hsb.find("Q") != -1 or hsb.find("*") != -1:
                if hsb.find("Q") == -1:
                    finalhand = finalhand.replace("*","Q")
                hsb = bow(hsb,"Q")
                if hsb.find("J") != -1 or hsb.find("*") != -1:
                    if hsb.find("J") == -1:
                        finalhand = finalhand.replace("*","J")
                    hsb = bow(hsb,"J")
                    if hsb.find("0") != -1 or hsb.find("*") != -1:
                        if hsb.find("0") == -1:
                            finalhand = finalhand.replace("*","0")
                        ssb = ss.replace("*","")
                        if len(ssb.replace(ssb[0],"")) == 0:
                            return ("A",14) # + finalhand
                        else:
                            isStraight = True
                            hcard = 14
    finalhand = hs[:]
    # Straight Flush, (four of a kind), Flush, Straight
    ssc = ss.replace("*","")
    if len(hand) == 5:
        if len(ssc.replace(ssc[0],"")) == 0:
            isFlush = True
    wasStraight = isStraight
    if len(hand) == 5:
        vlb = vl[:]
        vlb.sort()
        hsd = hs.replace("","")
        while vlb[0] == -1:
            vlb.remove(-1)
        i = 0
        precondition = True
        hcardb = -1
        for j in range(0,4):
            if len(vlb) > i + 1:
                if vlb[i+1] == vlb[i] + 1 or hsd.find("*") != -1:
                    if vlb[i+1] != vlb[i] + 1:
                        hsd = hsd.replace("*","",1)
                        vlb[i] += 1
                        hcardb = vlb[i]
                    else:
                        hcardb = vlb[i+1]
                        i += 1
                else:
                    precondition = False
                    break
            else:
                if hsd.find("*") != -1:
                    hcardb = vlb[i] + 1
                    hsd = hsd.replace("*","",1)
                else:
                    precondition = False
                    break
        isStraight = precondition and True
        if isStraight:
            hcard = hcardb
    if wasStraight:
        isStraight = True
    if isStraight and isFlush:
        return ("9",hcard)
    if len(hand) == 5:
        wc = hs.count("*")
        hsa = hs.replace("*","")
        hsf = hsa.replace(hsa[0],"")
        if len(hsf) == 1:
            if cardValue(hsa[0],True) > cardValue(hsf[0],True):
                return ("8",cardValue(hsa[0],True))
            else:
                return ("8",cardValue(hsf[0],True))
        else:
            for i in range(0,len(hsa)):
                if wc + hs.count(hsa[i]) == 4:
                    if hs.count(hsa[i]) > 0:
                        return ("8",cardValue(hsa[i],True))
                    return ("8",14)
    elif len(hand) == 4:
        hsa = hs.replace("*","")
        if len(hsa.replace(hsa[0],"")) == 0:
            return ("8",hsa[0])
    if len(hand) == 5:
        # Full house...
        hsf = hs.replace("*","")
        carda = hsf[0]
        cardb = "_"
        for i in hsf[1:]:
            if i != carda:
                if cardb != "_":
                    cardb = "_"
                    break
                cardb = i
                break
        if cardb != "_":
            wc = hs.count("*")
            if hs.count(carda) == 3 or wc - (3 - hs.count(carda)) > -1:
                wc -= (3 - hs.count(carda))
                if hs.count(cardb) == 2 or wc - (2 - hs.count(cardb)) == 0:
                    if hs.count("*") == 1 and cardValue(cardb,True) > cardValue(carda):
                        return ("7",cardValue(cardb,True) * 100 + cardValue(carda,True))
                    else:
                        return ("7",cardValue(carda,True) * 100 + cardValue(cardb,True))
    if isFlush:
        if hs.count("*") > 0:
            return ("6",14)
        else:
            return ("6",cardValue(highcard(hand),True))
    if isStraight:
        return ("5",hcard)
    if len(hand) == 5:
        wc = hs.count("*")
        hsa = hs.replace("*","")
        if wc == 2:
            return ("4",cardValue(highcard(hand,True),True))
        if len(hsa.replace(hsa[0],"")) == 2:
            return ("4",cardValue(hsa[0],True))
        else:
            for i in range(0,len(hsa)):
                if wc + hs.count(hsa[i]) >= 3:
                    return ("4",cardValue(hsa[i],True))
    elif len(hand) == 3:
        hsa = hs.replace("*","")
        if len(hsa.replace(hsa[0],"")) == 0:
            return ("4",cardValue(hsa[0],True))
    if len(hand) == 5 or len(hand) == 4 or len(hand) == 2:
        hsa = hs.replace("*","")
        hsb = hsa[:]
        pairs = []
        for i in hsa:
            if hsb.count(i) > 1:
                pairs.append(i)
                hsb = hsb.replace(i,"")
        if len(pairs) == 2:
            if cardValue(pairs[0],True) > cardValue(pairs[1],True):
                return ("3",cardValue(pairs[0],True) * 100 + cardValue(pairs[1],True))
            else:
                return ("3",cardValue(pairs[1],True) * 100 + cardValue(pairs[0],True))
        elif len(pairs) == 1:
            return ("2",cardValue(pairs[0],True))
        elif len(pairs) == 0:
            if hs.count("*") == 1:
                return ("2",cardValue(highcard(hand,True),True))
    return ("1",cardValue(highcard(hand),True))
cards = []
for i in range(0,56):
    cards.append(Card(deck,i))
if __name__ == "__main__":
    for i in range(0,1000):
        tmpcards = cards[:]
        for j in range(0,11):
            hand = []
            for k in range(0,5):
                hand.append(dealcard(tmpcards))
            tmp = PokerHandRank(hand)
            if tmp[1] > 100:
                l = int(tmp[1]/100)
                p = tmp[1] - l * 100
                print hand, handType(tmp[0]), cardName(l), cardName(p)
            else:
                print hand, handType(tmp[0]), cardName(tmp[1])
