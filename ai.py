#!/usr/bin/python
# Sppoker AI
import sppoker, asyncore, string, enchant, socket, threading, time, random, sys
ai_names = ["_Joe_", "_Bob_", "_Bill_", "_Adam_", "_Jerry_", "_Dan_", "_Anthony_", "_Jess_", "_Rachael_", "_Carie_", "_Tim_"]
ai_stuff = ["Good to go.", "Ready!", "All right guys.", "Let's go.", "Hurry up, you guys are slow.", "Good luck.", "Great hand!", "Haha.", "Alright.", "Phew."]
ai_cool = ["Yes!", "Yeaah boyee.", "Awesome!.", "Sweet!", "Take that!"]
ai_dang = ["Oh, dang.", "Darn it.", "Gah!", "So close...", "Arg!"]
if "--quick-dict" in sys.argv:
    d = enchant.Dict("en_US")
else:
    d = enchant.DictWithPWL("en_US","extrawords")
def unique(s):
    n = len(s)
    if n == 0:
        return []
    u = []
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u
    else:
        return u.keys()
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u

def examine_cards(c,hand):
    # Alright, first off, we'll check our words.
    tmp = ""
    for i in hand:
        tmp += i.letter
    words = unique(findwords(tmp.lower()))
    words.sort()
    BESTWORD = bestword(words).upper()
    (CARDHAND,BESTTYPE) = besthand(hand)
    # Do we double, call a word, or call a hand?
    w = len(BESTWORD)
    h = 0
    if BESTTYPE == "B":
        h = 11
    elif BESTTYPE == "A":
        h = 10
    else:
        h = int(BESTTYPE)
    if h > 6 and w > 3:
        c.call = "double"
        c.word = BESTWORD
        l = []
        for i in CARDHAND:
            l.append(str(i))
        c.callhand = string.join(l)
        c.send("CALL DOUBLE")
    elif (h > 1 and w < 4) or w == 0:
        c.call = "hand"
        l = []
        for i in CARDHAND:
            l.append(str(i))
        c.callhand = string.join(l)
        c.send("CALL HAND")
    else:
        c.call = "word"
        c.word = BESTWORD
        c.send("CALL WORD")
    c.send("CHAT %s" % ai_stuff[random.randint(0,len(ai_stuff)-1)])
def besthand(hand):
    best = "0"
    bhand = []
    for i in range(0,7):
        tmp = hand[:]
        del tmp[i]
        for j in range(0,6):
            tmpa = tmp[:]
            del tmpa[j]
            typ = sppoker.PokerHandRank(tmpa)[0]
            if ord(typ) > ord(best):
                best = typ
                bhand = tmpa
    return (bhand,best)
def bestword(lst):
    bestword = ""
    for i in lst:
        if i == "sppoker":
            bestword = "sppoker"
            break
        if len(i) > len(bestword):
            bestword = i + ""
        elif len(i) == len(bestword):
            for j in range(0,len(i)):
                if ord(i[j]) > ord(bestword[j]):
                    bestword = i
                    break
                elif ord(i[j]) < ord(bestword[j]):
                    break
    return bestword
def findwords(text,used=[]):
    if text in used:
        return []
    if len(text) > 2:
        s = wordsfrom(anagram(text))
        for i in unique(text[:]):
            s.extend(findwords(text.replace(i,'',1),s))
        return s
    else:
        return []
def wordsfrom(lst):
    global d
    p = []
    for i in unique(lst):
        if d.check(i):
            p.append(i)
    return p
def anagram(txt):
    if txt == "":
        return [txt]
    else:
        ans = []
        for an in unique(anagram(txt[1:])):
            for pos in range(len(an)+1):
                ans.append(an[:pos]+txt[0]+an[pos:])
        return ans

class SppokerAIClient(asyncore.dispatcher):
    def __init__(self,name):
        asyncore.dispatcher.__init__(self)
        self.olddata = ""
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = "localhost"
        self.buffer = "HELO"
        self.connect( (self.host, 2009) )
        self.hand = []
        self.phand = []
        self.call = "none"
        self.callhand = ""
        self.word = ""
        self.player_name = name # Select a random one
        self.lastPing = time.time()
        self.attached = True
        self.ka = SppokerAIClientKeepalive(self)
        self.ka.start()
    def handle_connect(self):
        pass
    def handle_close(self):
        self.attached = False
        try: self.send("DROP")
        except: pass
        self.close()
    def handle_read(self):
        data = self.recv(1024).strip()
        if data == "PONG":
            self.lastPing = time.time()
            return
        if data == self.olddata:
            return
        else:
            self.olddata = data
        if data == "":
            return
        raw = data.split(" ")
        if raw[0] == "":
            return
        # Begin command handling
        if raw[0] == "JOIN":
            if raw[1] == "ACCE":
                self.player_name = raw[2]
                self.send("PLAY")
                self.send("DEAL")
            elif raw[1] == "DENY":
                print "AI: Failed to join game room."
        elif raw[0] == "DEAL":
            # List of cards will follow
            temp_hand = raw[1:]
            if len(temp_hand) == 7:
                self.hand = []
                self.word = ""
                self.callhand = ""
                self.call = "none"
                for i in temp_hand:
                    card = sppoker.CardFromText(i)
                    if card != 0:
                        self.hand.append(card)
                # Time to handle these cards, eh?
                SppokerAIWorker(self,self.hand).start()
        elif raw[0] == "RESE":
            self.send("DEAL")
        elif raw[0] == "SCORES":
            sl = raw[1:]
            for i in sl:
                tmp = i.split(":")
                if tmp[0] == self.player_name:
                    dif = int(tmp[1]) - int(tmp[2])
                    if dif > 0:
                        self.send("CHAT %s" % ai_cool[random.randint(0,len(ai_cool)-1)])
                    elif dif < 0:
                        self.send("CHAT %s" % ai_dang[random.randint(0,len(ai_dang)-1)])
        elif raw[0] == "HELO":
            self.send("JOIN %s" % self.player_name)
        elif raw[0] == "CALL":
            if raw[1] == self.player_name:
                if self.call == "double":
                    self.send("WORD %s" % self.word)
                    self.send("HAND %s" % self.callhand)
                elif self.call == "word":
                    self.send("WORD %s" % self.word)
                elif self.call == "hand":
                    self.send("HAND %s" % self.callhand)
        elif raw[0] == "REDO":
            if self.call == "word" or self.call == "double":
                self.send("WORD %s" % self.word)
            if self.call == "double" or self.call == "hand":
                self.send("HAND %s" % self.callhand)
        else:
            pass
    def writable(self):
        return (len(self.buffer) > 0)
    def handle_write(self):
        try:
            sent = self.send(self.buffer)
            self.buffer = self.buffer[sent:]
        except:
            pass
class SppokerAIWorker(threading.Thread):
    def __init__(self,client,hand):
        self.client = client
        threading.Thread.__init__(self)
        self.hand = hand
    def run(self):
        try: examine_cards(self.client,self.hand)
        except: pass
class SppokerAIClientKeepalive(threading.Thread):
    def __init__(self,client):
        self.client = client
        threading.Thread.__init__(self)
    def run(self):
        while self.client.attached:
            time.sleep(2)
            if time.time() - self.client.lastPing > 10:
                print "AI",self.client.player_name,"probably timed out."
            try: self.client.send("PING")
            except: pass
class SppokerAIThread(threading.Thread):
    def run(self):
        while 1:
            asyncore.loop()
if __name__ == "__main__":
    # Run some tests.
    words = unique(findwords(raw_input("Letters: ").lower()))
    words.sort()
    print words
    BESTWORD = bestword(words)
    print BESTWORD
