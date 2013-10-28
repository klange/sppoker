#!/usr/bin/python2
# -*- coding: utf-8 -*-
# SPPoker is a registered trademark of Sppoker, LLC.
# All game play operations are the sole property of Sppoker, LLC
import pygame, sppoker
import pscreen, math
import asyncore, socket, threading, sys, time, string
import os, server, ai, random
import encodings.utf_8

# Load textures and fonts {
pscreen.SpriteLoad("card-front.png","front")
pscreen.SpriteLoad("card-back.png","back")
pscreen.SpriteLoad("card-clear.png","clear")
pscreen.SpriteLoad("card-glow.png","glow")
pscreen.SpriteLoad("prompt.png","prompt")
pscreen.SpriteLoad("edit-clear.png","reset")
pscreen.SpriteLoad("send-word.png","send-word")
pscreen.SpriteLoad("call-word.png","call-word")
pscreen.SpriteLoad("call-hand.png","call-hand")
pscreen.SpriteLoad("call-double.png","call-double")
pscreen.SpriteLoad("call-highlight.png","call-highlight")
pscreen.SpriteLoad("felt.png","felt")
pscreen.SpriteLoad("sppoker.png","sppoker")
pscreen.SpriteLoad("game-list.png","game-list")
pscreen.SpriteLoad("game-list-hl.png","game-list-hl")
pscreen.FontSelectDirect(fontName="DejaVuSans.ttf",fontSize=40)
pscreen.FontSelectDirect(fontName="DejaVuSans.ttf",fontSize=20,name="small")
pscreen.FontSelectDirect(fontName="DejaVuSansMono-Bold.ttf",fontSize=12,name="console")
# }

# Full screen? Disable text anti-aliasing? {
if "--fullscreen" in sys.argv:
    pscreen.LoadScreen(title="Internet Sppoker",resolution=(1024,600),fullscreen=True)
else:
    pscreen.LoadScreen(title="Internet Sppoker",resolution=(1024,600))
if "--disable-aa" in sys.argv:
    pscreen.textaa = False
# }

# Pump events? (Win32 requires this) {
pump_event_stream = False
if "--pump-events" in sys.argv:
    pump_event_steram = True
if sys.platform == "win32":
    pump_event_stream = True
# }

# Console background is pre-generated {
consoleback = pygame.Surface((1024,275),pygame.SRCALPHA,16)
consoleback.fill((0,0,0,160))
# }

# Settings {
default_options = { 'name':"Player",
                    'servername':"Sppoker_Game",
                    'bots':"2"
                  }
try:
    f = open("settings",'r')
    for line in f.readlines():
        tmp = line.strip().split(':')
        default_options[tmp[0]] = tmp[1]
    f.close()
except:
    pass
# }

# Some various client globals {
word = ""
highlight = -1
cardHighlighted = False
exit = False
kill = False
objects = []
handler = None
scores = {}
scorepluses = {}
playerwords = {}
playerhands = {}
displayBalloons = True
promptWait = False
ai_list = []
mouse = [0,0]
awaiting = "call"
dd = False
game_in_progress = False
# }

# Tiling felt background is pre-generated {
background = pygame.Surface((1024,600),0,16).convert()
for h in range(0,7):
    for v in range(0,4):
        background.blit(pscreen.sprite["felt"],(h * 160, v * 160))
# }

# Simple card-related items {
class DrawingCard():
    def __init__(self, position=[0,0], rotation=0):
        self.position = position
        self.rotation = rotation
    def render(self):
        pscreen.SpriteRender(self.position[0],self.position[1], \
            "back",self.rotation)
def RenderCardText(x,y,card):
    if card.suit == "D" or card.suit == "H":
        color = (220,0,0)
    else:
        color = (0,0,0)
    p = card.poker + ""
    if p == "0":
        p = "10"
    if p == "*":
        p = u"★"
    pscreen.FontWrite(x-50,y-80,p,color)
    pscreen.FontWrite(x-55,y-40,sppoker.suits[card.suit],color)
    pscreen.FontWrite(x+18,y+40,card.letter,(100,0,220))   
def inCard(coords,x,y):
    if coords[0] > x - 60 and coords[0] < x + 60:
        if coords[1] > y - 90 and coords[1] < y + 90:
            return True
    return False

playera = DrawingCard(position=[24,240],rotation=-90)
playerb = DrawingCard(position=[1000,240],rotation=90)
playerc = DrawingCard(position=[150,24],rotation=180)
playerd = DrawingCard(position=[510,24],rotation=180)
playere = DrawingCard(position=[870,24],rotation=180)
# }

# Called to call shots {
def showButtons():
    def tmp(call):
        global awaiting, dd, displayBalloons
        console.echo("WORD")
        client.send("CALL WORD")
        client.call = "word"
        try: del objects[:]
        except: pass
        def clearword(self):
            global word, client
            word = ""
            for i in client.hand:
                i.used = False
        def sendword(self):
            global word, client, awaiting
            client.send("WORD %s" % word)
            client.word = word
            word = ""
            awaiting = "none"
            for i in client.hand:
                i.used = True
            try: del objects[:]
            except: pass
        objects.append(SppokerUIButton('reset',(48,48),(694,364),clearword))
        objects.append(SppokerUIButton('send-word',(48,48),(740,364),sendword))
        awaiting = "word"
        dd = False
        displayBalloons = False
    def tmpb(call):
        global awaiting, dd, displayBalloons
        console.echo("HAND")
        client.send("CALL HAND")
        client.call = "hand"
        try: del objects[:]
        except: pass
        def clearhand(self):
            global client
            try: del client.phand[:]
            except: pass
            for i in client.hand:
                i.used = False
        def sendhand(self):
            global client, awaiting, console
            tmp = map(str,client.phand)
            console.echo(string.join(tmp))
            client.send("HAND %s" % string.join(tmp))
            awaiting = "none"
            for i in client.hand:
                i.used = True
            try: del objects[:]
            except: pass
        objects.append(SppokerUIButton('reset',(48,48),(694,364),clearhand))
        objects.append(SppokerUIButton('send-word',(48,48),(740,364),sendhand))
        awaiting = "hand"
        dd = False
        displayBalloons = False
    def tmpc(call):
        global awaiting, dd, displayBalloons
        console.echo("DOUBLE DOWN")
        client.send("CALL DOUBLE")
        try: del objects[:]
        except: pass
        def clearword(self):
            global word, client
            word = ""
            for i in client.hand:
                i.used = False
        def sendword(self):
            global word, client, awaiting
            client.send("WORD %s" % word)
            client.word = word
            word = ""
            awaiting = "hand"
            for i in client.hand:
                i.used = False
            try: del objects[:]
            except: pass
            def clearhand(self):
                global client
                try: del client.phand[:]
                except: pass
                for i in client.hand:
                    i.used = False
            def sendhand(self):
                global client, awaiting, console
                tmp = map(str,client.phand)
                console.echo(string.join(tmp))
                client.send("HAND %s" % string.join(tmp))
                awaiting = "none"
                for i in client.hand:
                    i.used = True
                try: del objects[:]
                except: pass
            objects.append(SppokerUIButton('reset',(48,48),(694,364),clearhand))
            objects.append(SppokerUIButton('send-word',(48,48),(740,364),sendhand))
        objects.append(SppokerUIButton('reset',(48,48),(694,364),clearword))
        objects.append(SppokerUIButton('send-word',(48,48),(740,364),sendword))
        client.call = "double"
        awaiting = "word"
        dd = True
        displayBalloons = False
    objects.append(SppokerUIButton("call-word",(200,80),(308,375),tmp,"call-highlight"))
    objects.append(SppokerUIButton("call-hand",(200,80),(716,375),tmpb,"call-highlight"))
    objects.append(SppokerUIButton("call-double",(200,80),(512,375),tmpc,"call-highlight"))
# }

# Bail out! (Or go to the menu) {
def HandleExit(soft=False):
    global client, thread, keepal, renderer, eventh, exit, promptWait, console
    try: client.send("DROP")
    except: pass
    if soft:
        try: console.visible = False
        except: pass
        exit = True
        return
    try: server.server.stop()
    except: pass
    client.close()
    asyncore.close_all()
    exit = True
    kill = True
    pscreen.UnloadScreen()
    pygame.quit()
    promptWait = False
    print "EXITING"
    os._exit(1)
# }

# Sppoker Client Class Definitions {
class SppokerClient(asyncore.dispatcher):
    def __init__(self,host):
        asyncore.dispatcher.__init__(self)
        self.olddata = ""
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.buffer = ""
        # SPPoker variables
        self.hand = []
        self.phand = []
        self.word = ""
        self.player_name = ""
        self.console = None
        self.chat = None
        self.call = "none"
        self.players = []
    def doconnect(self,host="NONE"):
        if host == "NONE":
            host = self.host + ""
        self.host = host + ""
        try:
            self.connect( (self.host,2009) )
            self.send("HELO")
        except:
            return False
        return True
    def attach_console(self,console):
        self.console = console
    def handle_connect(self):
        pass
    def handle_close(self):
        try: self.send("DROP") # We try this quite a bit.
        except: pass
        self.close()
    def echo(self,text,color=(255,255,255)):
        if self.console:
            self.console.echo(text,color)
    def handle_read(self):
        global objects, awaiting, scores, scorepluses, displayBalloons, exit, word, dd
        if exit:
            return
        data = self.recv(1024).strip()
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
                self.echo("Joined game room.")
                self.player_name = raw[2]
                self.echo("Requesting deal...")
                self.send("DEAL")
                self.send("PLAY")
            elif raw[1] == "DENY":
                self.echo("Could not join game room. Reason: %s" % string.join(raw[2:]))
                self.players = []
                HandleExit(True)
        elif raw[0] == "DEAL":
            # List of cards will follow
            temp_hand = raw[1:]
            self.hand = []
            self.phand = []
            self.word = ""
            awaiting = "call"
            for i in temp_hand:
                card = sppoker.CardFromText(i)
                if card != 0:
                    self.hand.append(card)
            if len(self.hand) == 7 and len(objects) < 3:
                showButtons()
        elif raw[0] == "CHAT":
            if self.chat:
                self.chat.append(string.join(raw[1:]))
        elif raw[0] == "HELO":
            self.echo("Handshake received. Message from server: %s" % string.join(raw[1:]))
            while self.player_name == "":
                self.player_name = Prompt("Name:",default_options['name'])
                self.player_name = self.player_name.replace(" ","_")
            self.send("JOIN %s" % self.player_name)
        elif raw[0] == "RESE":
            self.echo("Dealer shuffled the deck.")
            self.send("DEAL")
        elif raw[0] == "PLAY":
            if game_in_progress:
                self.players = raw[1:]
                self.echo("Players: %s" % string.join(raw[1:]))
        elif raw[0] == "CALL":
            if raw[1] == self.player_name:
                self.echo("Call accepted.")
        elif raw[0] == "WORD":
            if raw[1] == "FAIL":
                awaiting = "word"
                self.echo("Word failed.")
                for i in self.hand:
                    i.used = False
            elif raw[1] == "OK":
                self.echo("Word accepted.")
        elif raw[0] == "HAND":
            if raw[1] == "FAIL":
                awaiting = "hand"
                self.echo("Hand failed.")
            elif raw[1] == "OK":
                self.echo("Hand accepted.")
        elif raw[0] == "READY":
            self.echo("All players are ready. Waiting for the server...")
        elif raw[0] == "WIN":
            if raw[2] == "NONE":
                if raw[1] == "WORD":
                    self.echo("No word winner.")
                elif raw[1] == "HAND":
                    self.echo("No hand winner.")
            else:
                if raw[1] == "WORD":
                    self.echo("%s won with the word '%s'" % (raw[2],raw[3]))
                elif raw[1] == "HAND":
                    self.echo("%s won with a %s" % (raw[2],sppoker.handType(raw[3])))
        elif raw[0] == "SCORES":
            sl = raw[1:]
            for i in sl:
                tmp = i.split(":")
                dif = int(tmp[1]) - int(tmp[2])
                if dif > -1:
                    dif = "+%s" % str(dif)
                else:
                    dif = str(dif)
                playerwords[tmp[0]] = tmp[3]
                playerhands[tmp[0]] = tmp[4].split("_")
                self.echo("%s has %s point(s). (%s)" % (tmp[0],tmp[1],dif))
                scores[tmp[0]] = tmp[1]
                scorepluses[tmp[0]] = dif
                displayBalloons = True
        elif raw[0] == "REDO":
            if self.call == "word" or self.call == "double":
                self.send("WORD %s" % self.word)
            if self.call == "double" or self.call == "hand":
                tmp = map(str,self.phand)
                self.send("HAND %s" % string.join(tmp))
        elif raw[0] == "PONG":
            pass
        elif raw[0] == "WARN":
            self.echo("[ WARNING: %s ]" % string.join(raw[1:]),(250,120,0))
        else:
            self.echo("[ Unkown response: %s ]" % raw[0])
    def writable(self):
        return (len(self.buffer) > 0)
    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]
class SppokerClientThread(threading.Thread):
    def run(self):
        global client
        while not kill:
            try: asyncore.loop()
            except: pass
        sys.exit(1)
class SppokerClientKeepalive(threading.Thread):
    def run(self):
        global client, exit, awaiting, objects
        while not exit:
            time.sleep(5)
            try:
                client.send("PING")
                if len(client.hand) == 7 and awaiting == "call":
                    if len(objects) < 3:
                        showButtons()
            except:
                pass
        sys.exit(1)
class SppokerConsole():
    def __init__(self,client):
        self.client = client
        self.client.attach_console(self)
        self.screen = []
        self.colors = []
        self.input = ""
        self.print_events = False
        self.visible = False
    def echo(self,text,color=(255,255,255)):
        self.screen.append(text)
        self.colors.append(color)
        if len(self.screen) > 20:
            try: del self.screen[0]
            except: pass
            try: del self.colors[0]
            except: pass
    def clear(self):
        self.screen = []
        self.colors = []
    def handle(self,key):
        global game_in_progress
        if key == u'\x1b':
            HandleExit(game_in_progress)
        elif key == u'\x08':
            self.backspace()
        elif key == u'\r':
            self.send()
        elif len(key) > 0:
            self.input += key
    def backspace(self):
        if len(self.input) > 0:
            self.input = self.input[:-1]
    def send(self):
        # Process command
        if len(self.input) < 1:
            return
        if self.input[0] == "/":
            self.client.send(self.input[1:])
        else:
            command = self.input.strip().split()
            if command[0] == "clear":
                self.clear()
            elif command[0] == "events":
                if len(command) < 2:
                    self.echo("missing arguments for 'events'",(250,0,0))
                else:
                    if command[1] == "on":
                        self.echo("Event echoing on.")
                        self.print_events = True
                    elif command[1] == "off":
                        self.echo("Event echoing off.")
                        self.print_events = False
            elif command[0] == "server":
                if len(command) < 2:
                    self.echo("missing arguments for 'server'",(250,0,0))
                else:
                    if command[1] == "start":
                        if server.server.started:
                            self.echo("Server is already up.",(0,0,250))
                        else:
                            self.echo("Starting server...")
                            server.server.start()
                            server.server.console = self
                    elif command[1] == "reconnect":
                        print self.client.doconnect()
            elif command[0] == "connect":
                self.client.doconnect(command[1])
            elif command[0] == "cheat":
                tmp = ai.besthand(self.client.hand)
                self.echo("%s %s" % (string.join(map(str,tmp[0])),tmp[1]),(255,255,15))
                tmp = string.join([x.letter for x in self.client.hand],"")
                self.echo(str(ai.bestword(ai.unique(ai.findwords(tmp)))),(255,255,15))
            elif command[0] == "web":
                if server.server.started:
                    server.server.webiface()
                    self.echo("Web interface started.",(0,0,250))
                else:
                    self.echo("Can not start web interface: Server is not running.",(250,0,0))
            else:
                self.echo("Unknown command: %s" % command[0],(255,15,15))
        self.input = ""
    def width(self):
        width = 0
        for i in self.screen:
            if len(i) > width:
                width = len(i)
        if len(self.input) + 1 > width:
            width = len(self.input) + 1
        return width
    def render(self):
        global consoleback
        if self.visible:
            pscreen.screenbuffer.blit(consoleback,(0,0))
            j = 0
            for i in self.screen:
                pscreen.FontWrite(2,2 + j * 13,i,font="console",color=self.colors[j])
                j += 1
            pscreen.FontWrite(2,262,">%s" % self.input,font="console")
class SppokerRenderer(threading.Thread):
    def run(self):
        global playera, playerb, playerc, objects, word, awaiting
        global client, mouse, highlight, console, cardHighlighted
        global displayBalloons, background, exit, kill, game_in_progress
        while not kill:
            try:
                pscreen.screenbuffer.blit(background,(0,0))
                if len(client.player_name) > 0:
                    chat.render()
                if len(client.players) > 0:
                    oplayers = client.players[:]
                    try: oplayers.remove(client.player_name)
                    except: pass
                    text = []
                    lbl = []
                    lbla = []
                    for i in range(0,len(oplayers)):
                        if not scores.has_key(oplayers[i]):
                            scores[oplayers[i]] = 0
                            scorepluses[oplayers[i]] = ""
                            playerwords[oplayers[i]] = ""
                            playerhands[oplayers[i]] = []
                        if len(text) < i + 1:
                            text.append("")
                            lbl.append("")
                            lbla.append("")
                        text[i] = "%s: %s" % (oplayers[i].replace("_"," ").strip(), str(scores[oplayers[i]]))
                        w = playerwords[oplayers[i]]
                        h = playerhands[oplayers[i]]
                        if len(h) == 1:
                            if h[0] == '':
                                del h[0]
                        lbla[i] = scorepluses[oplayers[i]]
                        if not (w == "" and len(h) < 1):
                            lbl[i] = ""
                            if len(h) > 0:
                                lbl[i] = sppoker.prettyHand(h)
                            elif len(w) > 0:
                                lbl[i] = "\"%s\"" % w
                            if len(w) > 0 and len(h) > 0:
                                lbla[i] += " \"%s\"" % w
                    # Put these in layout lists for better
                    if len(oplayers) > 0:
                        pscreen.FontWrite(50,220 - pscreen.FontWidth(text[0],font="small")[0] / 2,text[0],(255,255,255),angle=-90,font="small")
                        playera.render()
                        if displayBalloons:
                            if not scorepluses[oplayers[0]] == "":
                                SppokerUILabel(lbla[0],lbl[0],(220,305)).render()
                    if len(oplayers) > 1:
                        pscreen.FontWrite(942,220 - pscreen.FontWidth(text[1],font="small")[0] / 2,text[1],(255,255,255),angle=90,font="small")
                        playerb.render()
                        if displayBalloons:
                            if not scorepluses[oplayers[1]] == "":
                                SppokerUILabel(lbla[1],lbl[1],(800,305)).render()
                    if len(oplayers) > 2:
                        pscreen.FontWrite(512 - 360 - pscreen.FontWidth(text[2],font="small")[0] / 2,60,text[2],(255,255,255),font="small")
                        playerc.render()
                        if displayBalloons:
                            if not scorepluses[oplayers[2]] == "":
                                SppokerUILabel(lbla[2],lbl[2],(512 - 360,27)).render()
                    if len(oplayers) > 3:
                        pscreen.FontWrite(512 - pscreen.FontWidth(text[3],font="small")[0] / 2,60,text[3],(255,255,255),font="small")
                        playerd.render()
                        if displayBalloons:
                            if not scorepluses[oplayers[3]] == "":
                                SppokerUILabel(lbla[3],lbl[3],(512,27)).render()
                    if len(oplayers) > 4:
                        pscreen.FontWrite(512 + 360 - pscreen.FontWidth(text[4],font="small")[0] / 2,60,text[4],(255,255,255),font="small")
                        playere.render()
                        if displayBalloons:
                            if not scorepluses[oplayers[4]] == "":
                                SppokerUILabel(lbla[4],lbl[4],(512 + 360,27)).render()
                if cardHighlighted:
                    pscreen.SpriteRender(130 + highlight * 125,500,"glow",0)
                for i in range(0,7):
                    if i < len(client.hand):
                        try:
                            if client.hand[i].used:
                                pscreen.SpriteRender(130 + i * 125,500,"clear",0)
                            else:
                                pscreen.SpriteRender(130 + i * 125,500,"front",0)
                            RenderCardText(130 + i * 125,500,client.hand[i])
                        except:
                            pass
                if client.player_name != "":
                    if not scores.has_key(client.player_name):
                        scores[client.player_name] = 0
                        scorepluses[client.player_name] = ""
                    s = scorepluses[client.player_name]
                    if displayBalloons:
                        if not s == "":
                            msg = ""
                            if s == "-2":
                                msg = "Too bad!"
                            elif s == "+0":
                                msg = "Nothing."
                            elif s == "+1":
                                msg = "Good job!"
                            elif s == "+4":
                                msg = "Amazing!"
                            SppokerUILabel(s,msg,(512,305)).render()
                    pscreen.FontWrite(80,360,client.player_name,(255,255,255),"small")
                    pscreen.FontWrite(80,382,"Points: %s" % str(scores[client.player_name]),(255,255,255),"small")
                if awaiting == "word":
                    pscreen.SpriteRender(512,362,"prompt",scaleFactor=0.6)
                    pscreen.FontWrite(512 - pscreen.FontWidth(word)[0] / 2,340,word,(255,255,255))
                if awaiting == "hand":
                    pscreen.SpriteRender(512,295,"prompt",scaleFactor=0.6)
                    pscreen.SpriteRender(512,362,"prompt",scaleFactor=0.6)
                    j = 0
                    for card in client.phand:
                        if card.suit == "D" or card.suit == "H":
                            color = (220,0,0)
                        else:
                            color = (255,255,255)
                        w = pscreen.FontWidth(card.poker)[0]
                        p = card.poker + ""
                        if p == "0":
                            p = "10"
                        if p == "*":
                            p = u"★"
                        pscreen.FontWrite(400 + j * 55 - w / 2,270,p,color)
                        pscreen.FontWrite(383 + j * 55,340,sppoker.suits[card.suit],color)
                        j += 1
                console.render()
                for i in objects:
                    i.render()
                    try:
                        for k in i.attached:
                            k.render()
                    except: pass
                pscreen.UpdateScreen()
            except:
                pass
        sys.exit(1)
class SppokerEventHandler(threading.Thread):
    def run(self):
        global exit, console, highlight, cardHighlighted, client, word, handler
        global objects, awaiting, dd, displayBalloons, chat
        global game_in_progress, kill
        while not kill:
            event = pygame.event.wait()
            if console.print_events:
                console.echo(str(event))
            if event.type == 4:
                x = event.dict['pos'][0] 
                y = event.dict['pos'][1]
                for i in objects:
                    i.mousein(x,y)
                    try:
                        for k in i.attached:
                            k.mousein(x,y)
                    except: pass
                if y > 300:
                    ht = False
                    hi = -1
                    for i in range(0,7):
                        if i < len(client.hand):
                            if inCard((x,y),130 + i * 125, 500):
                                ht = True
                                hi = i
                    if ht:
                        cardHighlighted = True
                        highlight = hi
                    else:
                        cardHighlighted = False
                        highlight = -1
            elif event.type == 12:
                HandleExit(game_in_progress )
            elif event.type == 6:
                for i in objects:
                    try:
                        i.mouseup()
                    except: pass
                    try:
                        for k in i.attached:
                            k.mouseup()
                    except: pass
            elif event.type == 5:
                # Check for it...
                if event.dict['button'] == 1:
                    x = event.dict['pos'][0] 
                    y = event.dict['pos'][1]
                    for i in objects:
                        if i.mousein(x,y):
                            i.click()
                            try:
                                for k in i.attached:
                                    if k.mousein(x,y):
                                        k.click()
                            except: pass
                    if cardHighlighted:
                        if awaiting == "word":
                            if not client.hand[highlight].used:
                                word += client.hand[highlight].letter
                                client.hand[highlight].used = True
                        elif awaiting == "hand":
                            if not client.hand[highlight].used:
                                if len(client.phand) < 5:
                                    client.hand[highlight].used = True
                                    client.phand.append(client.hand[highlight])
            if event.type == 2:
                key = event.dict['unicode']
                if key == u'\x1b':
                    HandleExit(game_in_progress)
                if handler:
                    handler.event_callback(key)
                else:
                    if key == u'`':
                        console.visible = not console.visible
                        continue
                    elif console.visible:
                        console.handle(key)
                    else:
                        chat.handle(key)
        sys.exit(1)
class SppokerUIPrompt():
    def __init__(self, prompt,init):
        self.prompt = prompt
        self.input = init
        self.response = ""
        self.hidden = False
        self.iwidth = pscreen.FontWidth(self.input)[0]
        self.pwidth = pscreen.FontWidth(self.prompt)[0]
    def event_callback(self,key):
        global console, game_in_progress
        if key == u'\x1b':
            HandleExit(game_in_progress)
        elif key == u'\x08':
            if len(self.input) > 0:
                self.input = self.input[:-1]
                self.iwidth = pscreen.FontWidth(self.input)[0]
        elif key == u'\r':
            self.finish()
        elif len(key) > 0:
            self.input += key
            self.iwidth = pscreen.FontWidth(self.input)[0]
    def finish(self):
        global promptWait
        self.response = self.input
        promptWait = False
    def setInput(self,text):
        self.input = text
        self.iwidth = pscreen.FontWidth(self.input)[0]
    def mousein(self,x,y):
        return False
    def click(self):
        pass
    def render(self):
        if not self.hidden:
            pscreen.SpriteRender(512,180,"prompt")
            pscreen.FontWrite(512 - self.pwidth / 2,130,self.prompt,(255,255,255))
            pscreen.FontWrite(512 - self.iwidth / 2,180,self.input,(255,255,255))
def Prompt(text,txt="",hide=False):
    global objects, promptWait, handler
    while promptWait:
        if pump_event_stream:
            try: pygame.event.pump()
            except: pass
    prompt = SppokerUIPrompt(text,txt)
    prompt.hidden = hide
    objects.append(prompt)
    promptWait = True
    handler = prompt
    while promptWait:
        if pump_event_stream:
            try: pygame.event.pump()
            except: pass
    handler = None
    try: objects.remove(prompt)
    except: pass
    return prompt.response
class SppokerUIButton():
    def __init__(self,image,size,pos,action,overimage="",overontop=False):
        self.image = image
        self.action = action
        self.pos = pos
        self.size = size
        self.overimage = overimage
        self.over = False
        self.overontop = overontop
    def render(self):
        if self.over and (not self.overimage == "") and (not self.overontop):
            pscreen.SpriteRender(self.pos[0],self.pos[1],self.overimage)
        pscreen.SpriteRender(self.pos[0],self.pos[1],self.image)
        if self.over and (not self.overimage == "") and self.overontop:
            pscreen.SpriteRender(self.pos[0],self.pos[1],self.overimage)
    def mousein(self,x,y):
        if x < self.pos[0] + self.size[0] / 2:
            if x > self.pos[0] - self.size[0] / 2:
                if y < self.pos[1] + self.size[1] / 2:
                    if y > self.pos[1] - self.size[1] / 2:
                        self.over = True
                        return True
        self.over = False
        return False
    def click(self):
        self.action(self)
class SppokerUILabel():
    def __init__(self,text,textb,pos,click=None,back=True):
        self.text = text
        self.textb = textb
        self.pos = pos
        self.over = False
        self.clickFunc = click
        self.back = back
        self.twidth = [pscreen.FontWidth(self.text,font="small")[0] / 2, \
            pscreen.FontWidth(self.textb,font="small")[0] / 2]
    def mousein(self,x,y):
        if x < self.pos[0] + 240 / 2:
            if x > self.pos[0] - 240 / 2:
                if y < self.pos[1] + 60 / 2:
                    if y > self.pos[1] - 60 / 2:
                        self.over = True
                        return True
        self.over = False
        return False
    def setText(self,a=None,b=None):
        if a:
            self.text = a
        if b:
            self.textb = b
        self.twidth = [pscreen.FontWidth(self.text,font="small")[0] / 2, \
            pscreen.FontWidth(self.textb,font="small")[0] / 2]
    def click(self):
        if self.clickFunc:
            self.clickFunc(self)
    def render(self):
        pos = self.pos
        if self.back:
            pscreen.SpriteRender(pos[0],pos[1],"prompt",scaleFactor=0.5)
        c = (255,255,255)
        if self.over:
            c = (80,220,40)
        pscreen.FontWrite(pos[0] - self.twidth[0],pos[1]-25,self.text,c,font="small")
        pscreen.FontWrite(pos[0] - self.twidth[1],pos[1],self.textb,c,font="small")
class SppokerUIUserList():
    def __init__(self):
        global objects
        self.pos = [20,20]
        self.size = [984,520]
        self.over = False
        self.mouse = (0,0)
        self.games = []
        self.scroll = 0
        self.highlight = -1
        self.scrollbar = SppokerUIScrollBar((self.pos[0]+self.size[0]-24,self.pos[1]),self.size[1])
        self.attached = []
        self.attached.append(self.scrollbar)
        self.scrollbar.max = 0.2
    def mousein(self,x,y):
        if x > self.pos[0] and x < self.pos[0] + self.size[0]:
         if y > self.pos[1] and y < self.pos[1] + self.size[1]:
          self.mouse = (x,y)
          if y > self.pos[1] + 40 and y < self.pos[1] + self.size[1] - 8 \
            and x < self.pos[0] + self.size[0] - 24:
            a = y - (self.pos[0] + 40)
            self.highlight = int(a / 25)
          else:
            self.highlight = -1
          return True
        self.highlight = -1
        return False
    def mouseup(self):
        self.scrollbar.mouseup()
    def addgame(self,game):
        self.games.append(game)
        if len(self.games) < 20:
            self.scrollbar.max = 0.2
        else:
            self.scrollbar.max = float(len(self.games) - 19)
        self.scrollbar.bound()
    def click(self):
        if self.highlight > -1:
            if self.highlight < len(self.games):
                start = int(self.scrollbar.value + 0.5)
                selected =  self.games[self.highlight + start]
                if selected.has_key('clickf'):
                    selected['clickf'](selected)
    def render(self):
        pscreen.SpriteRender(self.pos[0] + self.size[0] / 2, \
                             self.pos[1] + self.size[1] / 2, \
                             "game-list")
        if self.highlight > -1:
            if self.highlight < len(self.games):
                pscreen.SpriteRender(self.pos[0] + self.size[0] / 2, \
                                     self.pos[1] + 53 + 25 * self.highlight, \
                                     "game-list-hl")
        hc = (200,200,200)
        pscreen.FontWrite(self.pos[0] + 80,10 + self.pos[1], \
                          "Server Name",hc,font="small")
        pscreen.FontWrite(self.pos[0] + 590,10 + self.pos[1], \
                          "IP",hc,font="small")
        pscreen.FontWrite(self.pos[0] + 800,10 + self.pos[1], \
                          "Players",hc,font="small")
        pscreen.FontWrite(self.pos[0] + 900,10 + self.pos[1], \
                          "Bots",hc,font="small")
        r = 0
        start = int(self.scrollbar.value + 0.5)
        for j in range(start,start+19):
            try:
                i = self.games[j]
            except:
                break
            c = (255,255,255)
            if self.highlight == r:
                c = (80,220,40)
            # [*] | Server Name |    IP    | Players | Bots
            pscreen.FontWrite(self.pos[0] + 80,40 + self.pos[1] + 25 * r, \
                              i['title'],c,font="small")
            pscreen.FontWrite(self.pos[0] + 590,40 + self.pos[1] + 25 * r, \
                              i['ip'],c,font="small")
            pscreen.FontWrite(self.pos[0] + 800,40 + self.pos[1] + 25 * r, \
                              i['players'],c,font="small")
            pscreen.FontWrite(self.pos[0] + 900,40 + self.pos[1] + 25 * r, \
                              str(i['bots']),c,font="small")
            r += 1
class SppokerUIChat():
    def __init__(self):
        self.buffer = []
        self.input = ""
    def append(self,message):
        self.buffer.append(message)
        if len(self.buffer) > 5:
            try: del self.buffer[0]
            except: pass
    def backspace(self):
        if len(self.input) > 0:
            self.input = string.join(self.input[:-1],"")
    def convert(self,text):
        text = text.replace("/clubs",u"♣")
        text = text.replace("/spades",u"♠")
        text = text.replace("/diamonds",u"♦")
        text = text.replace("/hearts",u"♥")
        text = text.replace("/smile",u"☺")
        text = text.replace("/star",u"★")
        return text
    def handle(self,key):
        if key == u'\x1b':
            pass
        elif key == u'\x08':
            self.backspace()
        elif key == u'\r':
            self.send()
        elif len(key) > 0:
            self.input += key
    def send(self):
        global client
        client.send("CHAT %s" % self.input)
        self.input = ""
    def render(self):
        j = 0
        pscreen.SpriteRender(512,170,"prompt",scaleFactor=1.4)
        for i in self.buffer:
            pscreen.FontWrite(212,105 + j * 22,self.convert(i),font="small")
            j += 1
        pscreen.FontWrite(212,215,"Chat: %s" % self.convert(self.input),font="small")
class SppokerUIScrollBar():
    def __init__(self,pos,height):
        self.pos = pos
        self.height = height
        self.value = 0.0
        self.max = 100.0
        self.initmouse = (0,0)
        self.mouse = (0,0)
        self.grabbed = False
        self.initvalue = 0.0
        self.step = 1.0
        self.grabheight = 24
    def update(self):
        dy = (self.mouse[1] - self.initmouse[1]) / (float(self.height) - 48 - self.grabheight) * self.max
        self.value = self.initvalue + dy
        self.bound()
    def bound(self):
        self.grabheight = int((8 / (8 + self.max)) * self.height)
        if self.grabheight < 24:
            self.grabheight = 24
        elif self.grabheight > self.height - 48:
            self.grabheight = self.height - 48
        if self.value > self.max:
            self.value = self.max
        elif self.value < 0.0:
            self.value = 0.0
    def mousein(self,x,y):
        self.mouse = (x,y)
        if self.grabbed:
            self.update()
        if x > self.pos[0] and x < self.pos[0] + 24:
            if y > self.pos[1] and y < self.pos[1] + self.height:
                return True
        return False
    def click(self):
        if self.mouse[1] > self.pos[1] + 24 + (self.value / self.max) * (self.height - 48 - self.grabheight) and \
            self.mouse[1] < self.pos[1] + 24 + self.grabheight + (self.value / self.max) * (self.height - 48 - self.grabheight):
                self.initmouse = (self.mouse[0],self.mouse[1])
                self.initvalue = self.value + 0.0
                self.grabbed = True
        elif self.mouse[1] < self.pos[1] + 24:
            self.value -= self.step
            self.bound()
        elif self.mouse[1] > self.pos[1] + self.height - self.grabheight:
            self.value += self.step
            self.bound()
        else:
            pass
    def mouseup(self):
        if self.grabbed:
            self.grabbed = False
            self.update()
    def render(self):
        tmp = pygame.Surface((24,self.height),depth=16)
        tmp.fill((0,0,0,255))
        tmpa = pygame.Surface((24,self.grabheight),depth=16)
        tmpa.fill((0,0,255))
        tmp.blit(tmpa,(0,24 + (self.value / self.max) * (self.height - 48 - self.grabheight)))
        pscreen.screenbuffer.blit(tmp,self.pos)
# }

# Global game processors and threads {
client = SppokerClient("127.0.0.1") # Aka no one
thread = SppokerClientThread()
thread.start()
console = SppokerConsole(client)
chat = SppokerUIChat()
client.chat = chat
renderer = SppokerRenderer()
renderer.start()
eventh = SppokerEventHandler()
eventh.start()
# }

while 1:
    exit = False
    objects.append(SppokerUIButton("sppoker",(0,0),(512,70),None))
    
    # Main menu function {
    def show_menu(self):
     for i in objects:
      if isinstance(i,SppokerUIPrompt):
       if i.prompt == "MENU":
        i.setInput(self.text)
        i.finish()
        del objects[:]
    # }

    # Menu Options {
    objects.append(SppokerUILabel("New Game","Start a local game",(512,200),click=show_menu))
    objects.append(SppokerUILabel("Join Game","Join a network game",(512,270),click=show_menu))
    objects.append(SppokerUILabel("Options","Change settings",(512,340),click=show_menu))
    objects.append(SppokerUILabel("Quit","Leave SPPoker",(512,410),click=show_menu))
    # }

    # Wait for Menu selection {
    menu = Prompt("MENU","",True)
    # }
    if menu == "Quit":
        HandleExit()
    elif menu == "":
        del objects[:]
        continue
    elif menu == "Options":
        while 1:
            del objects[:]
            objects.append(SppokerUILabel("Player Name",default_options['name'],(512,200),click=show_menu))
            objects.append(SppokerUILabel("Default Bots",default_options['bots'],(512,270),click=show_menu))
            objects.append(SppokerUILabel("Server Name",default_options['servername'],(512,340),click=show_menu))
            objects.append(SppokerUILabel("Back","Return to Menu",(512,410),click=show_menu))
            menu = Prompt("MENU","",True)
            if menu == "Back":
                break
            elif menu == "Player Name":
                default_options['name'] = Prompt("Default Player Name:",default_options['name'])
            elif menu == "Default Bots":
                default_options['bots'] = Prompt("Default Bot Count:",default_options['bots'])
            elif menu == "Server Name":
                default_options['servername'] = Prompt("Default Server Name:",default_options['servername'])
            try:
                f = open("settings",'w')
                for k,v in default_options.iteritems():
                    f.write("%s:%s\n" % (k,v))
                f.close()
            except:
                pass
            continue
        continue
    elif menu == "New Game":
        aicount = 0
        serverip = "localhost"
        server.server.start()
        server.server.console = console
        server.clearUsers()
        server.server.name = Prompt("Server Name:",default_options['servername'])
        try: aicount = int(Prompt("Add Bots?",default_options['bots']))
        except: aicount = 0
        if aicount > 0:
            ai_names = ai.ai_names[:]
            del ai_list[:]
            for i in range(0,aicount):
                server.server.ai_count = aicount
                i = random.randint(0,len(ai_names)-1)
                tmp = ai_names[i]
                del ai_names[i]
                ai_list.append(ai.SppokerAIClient(tmp))
    elif menu == "Join Game":
        gamelist = SppokerUIUserList()
        def nullclick(self):
            print self['ip']
        def clickb(self):
         global objects
         for i in objects:
          if isinstance(i,SppokerUIPrompt):
           i.setInput(self['ip'])
           i.finish()
           del objects[:]
           break
        """for i in range(27):
            gamelist.addgame({  'title':"TEST %s" % str(i+1), \
                                'ip':"192.168.1.%s" % str(i), \
                                'players':"%s/6" % str(i % 6 + 1), \
                                'bots':str(i % 3), \
                                'web':"True", \
                                'clickf':nullclick })"""
        server_count = 0
        # Game Finders (LAN and Internet) {
        def append_game(tmp,address):
            global gamelist, clickb
            gamename = tmp[1].replace("_"," ")
            if len(tmp) > 2:
                p_count = "%s/6" % tmp[2]
                b_count = tmp[3]
                web = bool(tmp[4])
            else:
                p_count = "?/6"
                b_count = "?"
                web = False
            gamelist.addgame({  'title':"%s" % gamename, \
                                'ip':address, \
                                'players':p_count, \
                                'bots':b_count, \
                                'web':web, \
                                'clickf':clickb })
        class SppokerLANGameFinder(threading.Thread):
            def run(self):
                global objects, server_count, gamelist
                # Search for local servers on this subnet (ie, 192.168.2.*)
                s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                try:
                    s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
                    s.sendto("SEARCH",("<broadcast>",2009))
                    s.settimeout(0.1)
                except:
                    return
                searchtimeout = time.time() + 2
                k = 0
                while searchtimeout > time.time():
                    try:
                        (buf, address) = s.recvfrom(1024)
                        tmp = buf.strip().split()
                        append_game(tmp,address[0])
                        server_count += 1
                    except:
                        pass
                s.close()
                sys.exit(1)
        class SppokerWebGameFinder(threading.Thread):
            def run(self):
                global objects, server_count, gamelist
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                d = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("ogunderground.com",80))
                s.send("GET %s HTTP/1.0\r\nHost: %s\r\n\r\n" % ("/sppoker_games","ogunderground.com"))
                searchtimeout = time.time() + 3
                gamedata = ""
                while searchtimeout > time.time():
                    text = s.recv(2048)
                    if not text:
                        break
                    gamedata += text
                s.close()
                pullList = False
                for line in gamedata.split("\n"):
                    if line.find("<GAMELIST>") > -1:
                        pullList = True
                        continue
                    if pullList:
                        if line.count(" ") == 1:
                            (servername,address) = line.strip().split(" ")
                            d.sendto("SEARCH",(address,2009))
                            d.settimeout(0.1)
                            try:
                                (buf, address) = d.recvfrom(1024)
                                tmp = buf.strip().split()
                                append_game(tmp,address[0])
                                server_count += 1
                            except:
                                pass
                sys.exit(1)
        # }
        # Show the game list
        objects.append(gamelist)
        
        game_finder_done = False
        # Look for games {
        SppokerLANGameFinder().start()
        SppokerWebGameFinder().start()
        # }
        
        def test(self):
         for i in objects:
          if isinstance(i,SppokerUIPrompt):
           i.setInput("BACK")
           i.finish()
        objects.append(SppokerUILabel("Back","Return to Menu",(512,570),click=test))
        
        # Wait for a game to be found and selected {
        serverip = ""
        while serverip == "":
            serverip = Prompt("Choose a Game","",True)
        # }
        del objects[:]
        if serverip == "BACK":
            continue
    else:
        # Loose else (keeps random typing on menu from breaking)
        del objects[:]
        continue
    game_in_progress = True
    client.doconnect(serverip)
    keepal = SppokerClientKeepalive()
    keepal.start()
    while not exit:
        if pump_event_stream:
            try: pygame.event.pump()
            except: pass
        if exit:
            break
    HandleExit(True)
    game_in_progress = False
    del objects[:]
    client.hand = []
    client.phand = []
    client.players = []
    client.player_name = ""
    for i in ai_list:
        i.handle_close()
    try:
        server.server.reset()
    except: pass
    awaiting = "call"
    continue
HandleExit()
