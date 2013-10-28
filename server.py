#!/usr/bin/python
import SocketServer, socket, string, time, threading, sys
import sppoker, enchant, BaseHTTPServer, sppweb, cgi
spellcheck = enchant.DictWithPWL("en_US","extrawords")
cards = sppoker.cards[:]
players = {}
users = []

class SppokerServerHandler(SocketServer.DatagramRequestHandler):
    def handle(self):
        global server, cards, players, users, spellcheck
        while 1:
            raw = self.rfile.read().strip()
            if raw == "":
                break
            split = raw.split(" ")
            if split[0] == "":
                self.wfile.write("WARN Blank message")
                break
            # Begin command handling
            if split[0] == "SEARCH":
                server.echo("Game search request from %s" % self.client_address[0])
                self.wfile.write("SEARCH %s %s %s %s" % ( \
                                    server.name, \
                                    str(len(players)), \
                                    str(server.bot_count), \
                                    str(server.webactive)  ))
                break
            if split[0] == "PING":
                self.checkIfReady(True)
                self.wfile.write("PONG")
                break
            elif split[0] == "JOIN":
                if len(players) == 6:
                    self.wfile.write("JOIN DENY Server is full.")
                else:
                    name = split[1]
                    name_in_use = True
                    while name_in_use:
                        name_in_use = False
                        for k,v in players.iteritems():
                            if v['name'] == name:
                                name_in_use = True
                        if name_in_use:
                            name = "%s1" % name
                            #self.wfile.write("JOIN DENY Name in use.")
                    else:
                        players[self.client_address] = {}
                        p = players[self.client_address]
                        p['name'] = name
                        p['hand'] = []
                        p['word'] = ""
                        p['call'] = ""
                        p['poker'] = []
                        p['score'] = 0
                        p['ready'] = False
                        self.wfile.write("JOIN ACCE %s" % name)
                break
            elif split[0] == "HELO":
                server.echo("Helo received from %s" % str(self.client_address))
                users.append(self.client_address)
                self.wfile.write("HELO Welcome!")
                break
            elif split[0] == "DEAL":
                # Faster deal for AI, etc.
                if players.has_key(self.client_address):
                    p = players[self.client_address]
                    while len(p['hand']) < 7:
                        card = sppoker.dealcard(cards)
                        if card != 0:
                            p['hand'].append(card)
                    tmp = map(str,p['hand'])
                    output = "DEAL %s" % string.join(tmp)
                    self.wfile.write(output)
                    break
                else:
                    self.wfile.write("WARN Can't deal to unknown player.")
                    break
            elif split[0] == "RESE":
                self.newgame()
                self.wfile.write(" ")
                break
            elif split[0] == "PLAY":
                # list of players
                playerlist = []
                for v in players.values():
                    playerlist.append( v['name'] )
                output = "PLAY %s" % string.join(playerlist)
                for i in users:
                    self.request[1].sendto(output,i)
                self.wfile.write(" ")
                break
            elif split[0] == "CALL":
                if players.has_key(self.client_address):
                    players[self.client_address]['call'] = split[1]
                    players[self.client_address]['word'] = ""
                    players[self.client_address]['poker'] = []
                    output = "CALL %s" % players[self.client_address]['name']
                    server.echo("Call from %s (%s)" % (players[self.client_address]['name'], split[1]))
                    for i in users:
                        self.request[1].sendto(output,i)
                    self.wfile.write(" ")
                    break
                else:
                    self.wfile.write("WARN Not a player.")
                    break
            elif split[0] == "DROP":
                try: del players[self.client_address]
                except: pass
                playerlist = []
                for v in players.values():
                    playerlist.append( v['name'] )
                output = "PLAY %s" % string.join(playerlist)
                for i in users:
                    self.request[1].sendto(output,i)
                self.wfile.write(" ")
                break
            elif split[0] == "KILL":
                who = None
                for k,v in players.iteritems():
                    if v['name'] == split[1]:
                        who = k
                try: del players[who]
                except: pass
                playerlist = []
                for v in players.values():
                    playerlist.append( v['name'] )
                output = "PLAY %s" % string.join(playerlist)
                for i in users:
                    self.request[1].sendto(output,i)
                self.wfile.write(" ")
                break
            elif split[0] == "WORD":
                if players.has_key(self.client_address):
                    players[self.client_address]['word'] = split[1]
                    word = split[1]
                    letters = ""
                    for card in players[self.client_address]['hand']:
                        letters += card.letter
                    fail = False
                    for i in word:
                        if not letters.find(i) == -1:
                            letters.replace(i,"",1)
                        else:
                            fail = True
                            break
                    if fail:
                        self.wfile.write("WORD FAIL")
                        server.echo("Word failed from %s" % players[self.client_address]['name'])
                        break
                    else:
                        if players[self.client_address]['call'] == "WORD":
                            players[self.client_address]['ready'] = True
                        self.wfile.write("WORD OK")
                        server.echo("Word ok from %s" % players[self.client_address]['name'])
                        self.checkIfReady()
                        break
                else:
                    self.wfile.write("WORD FAIL")
                    break
            elif split[0] == "HAND":
                if players.has_key(self.client_address):
                    players[self.client_address]['poker'] = split[1:]
                    chand = []
                    for i in players[self.client_address]['hand']:
                        chand.append(str(i))
                    tmphand = split[1:]
                    fail = False
                    for i in tmphand:
                        if not chand.count(i) < 1:
                            chand.remove(i)
                        else:
                            fail = True
                            break
                    if fail:
                        self.wfile.write("HAND FAIL")
                        break
                    else:
                        players[self.client_address]['ready'] = True
                        self.wfile.write("HAND OK")
                        server.echo("Hand ok from %s" % players[self.client_address]['name'])
                        self.checkIfReady()
                        break
                else:
                    self.wfile.write("HAND FAIL")
                    break
            elif split[0] == "CHAT":
                if players.has_key(self.client_address):
                    text = "%s: %s" % (players[self.client_address]['name'].replace("_"," ").strip(), string.join(split[1:]))
                else:
                    text = "%s: %s" % (self.client_address[0], string.join(split[1:]))
                server.chat_log.insert(0,text)
                output = "CHAT %s" % text
                for i in users:
                    self.request[1].sendto(output,i)
                self.wfile.write(" ")
                break
            elif split[0] == "REDO":
                server.echo("Requesting redo from all clients.")
                output = "REDO"
                for i in users:
                    self.request[1].sendto(output,i)
                self.wfile.write(" ")
                break
            else:
                self.wfile.write("WARN Unkown command: %s" % split[0])
                break
        return
    def newgame(self):
        global server, cards, players, users
        cards = sppoker.cards[:]
        for v in players.values():
            v['word'] = ""
            v['hand'] = []
            v['call'] = ""
            v['poker'] = []
            v['ready'] = False
        for i in users:
            self.request[1].sendto("RESE OK",i)
        server.processThread = SppokerServerProcessor(self.processGame)
    def processGame(self):
        global server, cards, players, users
        for i in users:
            self.request[1].sendto("READY",i)
        # Process the game.
        wordplayers = {}
        handplayers = {}
        doubleplayers = {}
        for k,v in players.iteritems():
            if v['call'] == "WORD" or v['call'] == "DOUBLE":
                wordplayers[k] = v['word']
            if v['call'] == "HAND" or v['call'] == "DOUBLE":
                tmphand = []
                for i in v['poker']:
                    tmphand.append(sppoker.CardFromText(i))
                handtype = sppoker.PokerHandRank(tmphand)
                handplayers[k] = handtype
            if v['call'] == "DOUBLE":
                doubleplayers[k] = 0
        winner = False
        bestword = ""
        bestwplayer = None
        besthand = "0"
        besthplayer = None
        NO_HAND_WINNER = False
        NO_WORD_WINNER = False
        while not winner:
            if len(wordplayers) < 1:
                bestwplayer = None
                NO_WORD_WINNER = True
            else:
                # find a winner...
                bestword = ""
                bestplayer = None
                for k,v in wordplayers.iteritems():
                    if not spellcheck.check(v):
                        continue
                    if v == "SPPOKER":
                        bestword = "SPPOKER"
                        bestplayer = k
                        break
                    if len(v) > len(bestword):
                        bestword = v + ""
                        bestwplayer = k
                    elif len(v) == len(bestword):
                        for i in range(0,len(v)):
                            if ord(v[i]) > ord(bestword[i]):
                                bestword = v
                                bestwplayer = k
                                break
                            elif ord(v[i]) < ord(bestword[i]):
                                break
            if len(handplayers) < 1:
                besthplayer = None
                NO_HAND_WINNER = True
                winner = True
            else:
                besthand = ("0",0)
                besthplayer = None
                for k,v in handplayers.iteritems():
                    if ord(v[0]) > ord(besthand[0]):
                        besthand = (v[0],v[1])
                        besthplayer = k
                    elif ord(v[0]) == ord(besthand[0]):
                        if v[1] > besthand[1]:
                            besthand = (v[0],v[1])
                            besthplayer = k
                if len(doubleplayers.values()) < 1:
                    winner = True
                else:
                    if doubleplayers.has_key(besthplayer):
                        if not bestwplayer == besthplayer:
                            if doubleplayers.has_key(bestwplayer):
                                try: del handplayers[bestwplayer]
                                except: pass
                                try: del wordplayers[bestwplayer]
                                except: pass
                                doubleplayers[bestwplayer] = 0
                            winner = False
                            try: del handplayers[besthplayer]
                            except: pass
                            try: del wordplayers[besthplayer]
                            except: pass
                            doubleplayers[besthplayer] = 0
                        else:
                            doubleplayers[besthplayer] = 1
                            winner = True
                    elif doubleplayers.has_key(bestwplayer):
                        winner = False
                        doubleplayers[bestwplayer] = 0
                        try: del handplayers[bestwplayer]
                        except: pass
                        try: del wordplayers[bestwplayer]
                        except: pass
                    else:
                        winner = True
        oldscores = {}
        if NO_WORD_WINNER:
            server.lastwinning_word = "&lt;i&gt;None&lt;/i&gt;"
            server.lastwinning_wplayer = "&lt;i&gt;No Winner&lt;/i&gt;"
            for i in users:
                self.request[1].sendto("WIN WORD NONE",i)
        if NO_HAND_WINNER:
            server.lastwinning_hand = "&lt;i&gt;None&lt;/i&gt;"
            server.lastwinning_handtype = "&lt;i&gt;Nothing&lt;/i&gt;"
            server.lastwinning_hplayer = "&lt;i&gt;No Winner&lt;/i&gt;"
            for i in users:
                self.request[1].sendto("WIN HAND NONE",i)
        for v in players.values():
            oldscores[v['name']] = v['score']
        if not bestwplayer == besthplayer:
            if bestwplayer:
                if not doubleplayers.has_key(bestwplayer):
                    players[bestwplayer]['score'] += 1
            if besthplayer:
                if not doubleplayers.has_key(besthplayer):
                    players[besthplayer]['score'] += 1
        for k,v in doubleplayers.iteritems():
            if v == 1:
                players[k]['score'] += 4
            else:
                players[k]['score'] -= 2
        if bestwplayer and len(wordplayers) > 0:
            server.lastwinning_word = bestword
            server.lastwinning_wplayer = players[bestwplayer]['name']
            for i in users:
                self.request[1].sendto("WIN WORD %s %s" % (players[bestwplayer]['name'], bestword),i)
        if besthplayer and len(handplayers) > 0:
            server.lastwinning_hand = sppoker.prettyHand(players[besthplayer]['poker'])
            server.lastwinning_handtype = sppoker.handType(besthand[0])
            server.lastwinning_hplayer = players[besthplayer]['name']
            for i in users:
                self.request[1].sendto("WIN HAND %s %s" % (players[besthplayer]['name'], besthand[0]),i)
        scorelist = []
        for k,v in players.iteritems():
            scorelist.append("%s:%s:%s:%s:%s" % (v['name'], str(v['score']), str(oldscores[v['name']]), v['word'], string.join(v['poker'],"_")))
        for i in users:
            self.request[1].sendto("SCORES %s" % string.join(scorelist),i)
        self.newgame()
    def checkIfReady(self,fromPing=False):
        global server, players, users
        if len(players.values()) < 1:
            return
        ready = True
        for i in players.values():
            ready = ready & i['ready']
        if ready:
            for k,v in players.iteritems():
                v['ready'] == False
            if server.processThread == None:
                server.processThread = SppokerServerProcessor(self.processGame)
            try:
                server.processThread.start()
            except:
                pass
class SppokerServerThread(threading.Thread):
    def run(self):
        try: self.udp.serve_forever()
        except: pass
        print "stopped server"
    def start(self,server):
        self.udp = server
        threading.Thread.start(self)
class SppokerServerProcessor(threading.Thread):
    def run(self):
        self.func()
    def __init__(self,func):
        self.func = func
        threading.Thread.__init__(self)
class SppokerServer():
    def __init__(self):
        try:
            self.udp = SocketServer.ThreadingUDPServer(("",2009),SppokerServerHandler)
            self.udp.allow_reuse_address = True
            self.reset()
            self.web = BaseHTTPServer.HTTPServer(("",2009),SppokerWebRequest)
        except:
            self.donotstart = True
    def echo(self,text):
        if self.console:
            self.console.echo("[server] %s" % (text),color=(15,15,255))
        else:
            print "\r[server] %s" % (text)
            sys.stdout.write(self.prompt)
            sys.stdout.flush()
    def start(self):
        self.thread = SppokerServerThread()
        self.thread.start(self.udp)
        self.wthread = None
        self.started = True
    def webiface(self):
        self.webactive = True
        self.wthread = SppokerServerThread()
        self.wthread.start(self.web)
    def reset(self):
        self.players = {}
        self.started = False
        self.console = None
        self.donotstart = False
        self.ready = False
        self.processThread = None
        self.prompt = ""
        self.name = "Sppoker_Game"
        self.webactive = False
        self.chat_log = []
        self.bot_count = 0
        self.lastwinning_hand = "&lt;i&gt;None&lt;/i&gt;"
        self.lastwinning_word = "&lt;i&gt;None&lt;/i&gt;"
        self.lastwinning_handtype = "&lt;i&gt;N/A&lt;/i&gt;"
        self.lastwinning_hplayer = "&lt;i&gt;No Winner&lt;/i&gt;"
        self.lastwinning_wplayer = "&lt;i&gt;No Winner&lt;/i&gt;"
        cards = sppoker.cards[:]
class SppokerWebRequest(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        global server, users
        try:
            self.server_version = "SppokerServer/0.1"
            if self.path == "/":
                self.send_response(200,'OK')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("""<html>
<head>
<title>Internet Sppoker - Web Panel</title>
<style type="text/css">
body {
 background-image:url(%s);
 background-color: #00DD00;
 color: #FFF;
 font-family: sans, Tahoma, Verdana;
 font-size: 18px;
}
input {
 border: 1px #FFF solid;
 background-color: #555;
 color: #FFF;
 width: 100%%;
}
.idiv {
 position: absolute;
 top: 40px;
 bottom: 10px;
 left: 10px;
 right: 10px;
 padding: 0px;
}
</style>
<script type="text/javascript">
var httpRequest, httpPush;
if (window.XMLHttpRequest) {
  httpRequest = new XMLHttpRequest();
  httpPush = new XMLHttpRequest();
} else if (window.ActiveXObject) {
  alert("You're using IE, bugger off.");
}
httpRequest.overrideMimeType('text/xml');
function q(xml,tag) {
    document.getElementById(tag).innerHTML = xml.getElementsByTagName(tag)[0].childNodes[0].nodeValue;
}
httpRequest.onreadystatechange = function(){
  if (httpRequest.readyState == 4) {
   if (httpRequest.status == "200") {
     var root = httpRequest.responseXML;
     q(root,"servername");
     q(root,"players");
     q(root,"chat");
     q(root,"last_word_winner");
     q(root,"last_word");
     q(root,"last_hand_winner");
     q(root,"last_hand");
     q(root,"last_hand_type");
   }
  } else {}
};
function doit() {
  httpRequest.open('GET','dat.xml',true);
  httpRequest.send(null);
  setTimeout("doit()",400);
}
function send() {
  var params = "input_box=" + document.chat_form.input_box.value;
  document.chat_form.reset();
  httpPush.open("POST","/chat",true);
  httpPush.setRequestHeader("Content-type","application/x-www-form-urlencoded");
  httpPush.setRequestHeader("Content-length", params.length);
  httpPush.setRequestHeader("Connection","close");
  httpPush.send(params);
  return false;
}
doit();

</script>
</head>
<body>
<span style="font-size: 24px;" id="servername">Loading...</span><br>
<table><tr><td style="vertical-align: top; width: 300px;"><span id="players">Loading...</span></td>
<td style="vertical-align: top;">
<b>Last Word</b>: <span id="last_word">(Nothing yet!)</span> by <span id="last_word_winner">(No one!)</span><br>
<b>Last Hand</b>: <span id="last_hand">(Nothing yet!)</span> (a <span id="last_hand_type">nothing</span>)
by <span id="last_hand_winner">(No one!)</span><br>
</td></tr></table>
<form action="/chat" method="post" name="chat_form" onsubmit="return send()">
<table><tr><td><input type="text" id="box" name="input_box" class="box"></td>
<td><input type="submit" class="sub" value="Send"></td></tr></table>
<script type="text/javascript">
box.focus();
</script>
</form>
<span id="chat">Message Buffer</span>
</body>
</html>""" % sppweb.background)
            elif self.path == "/dat.xml":
                self.send_response(200,'OK')
                self.send_header('Content-type', 'text/xml')
                self.end_headers()
                scorelist = []
                for k,v in players.iteritems():
                    scorelist.append("&lt;b&gt;%s&lt;/b&gt;: %s" % (v['name'].replace("_"," ").strip(), str(v['score'])))
                output = string.join(scorelist,"&lt;br&gt;")
                clog = string.join(server.chat_log[:10],"<br>\n").replace("<","&lt;").replace(">","&gt;")
                self.wfile.write("""<?xml version="1.0" ?>
<root>
  <servername>%s</servername>
  <players>%s</players>
  <chat>%s</chat>
  <last_word_winner>%s</last_word_winner>
  <last_word>%s</last_word>
  <last_hand_winner>%s</last_hand_winner>
  <last_hand>%s</last_hand>
  <last_hand_type>%s</last_hand_type>
</root>
""" % (server.name.replace("_"," "), output, clog, server.lastwinning_wplayer.replace("_"," ").strip(), server.lastwinning_word, server.lastwinning_hplayer.replace("_"," ").strip(), server.lastwinning_hand.encode('ascii', 'xmlcharrefreplace'), server.lastwinning_handtype))
            else:
                self.send_response(404,'File Not Found')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("<b>File Not Found</b>: " + self.path)
        except:
            return
    def do_POST(self):
        global server, users
        self.server_version = "SppokerServer/0.1"
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        self.send_response(200,'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        server.chat_log.insert(0,"[Web] %s: %s" % (self.client_address[0],form['input_box'].value))
        output = "CHAT [Web] %s: %s" % (self.client_address[0],form['input_box'].value)
        for i in users:
            server.udp.socket.sendto(output,i)
        self.wfile.write("<meta http-equiv=\"refresh\" content=\"0\" />")
    def log_request(self,code="-",size="-"):
        pass
server = SppokerServer()
def clearUsers():
    global users
    users = []
if __name__ == "__main__":
    server.start()
    cmd = ""
    server.prompt = ">"
    while not cmd == "exit":
        cmd = raw_input(">")
        c = cmd.split(" ")
        if c[0] == "exit":
            break
        elif c[0] == "ai":
            import ai, random
            ai_names = ai.ai_names[:]
            ai.SppokerAIThread().start()
            for i in range(0,int(c[1])):
                server.bot_count = int(c[1])
                i = random.randint(0,len(ai_names)-1)
                tmp = ai_names[i]
                del ai_names[i]
                ai.SppokerAIClient(tmp)
        elif c[0] == "boot":
            who = None
            for k,v in players.iteritems():
                if v['name'] == c[1]:
                    who = k
            try: del players[who]
            except: pass
            playerlist = []
            for v in players.values():
                playerlist.append( v['name'] )
            output = "PLAY %s" % string.join(playerlist)
            for i in users:
                server.udp.socket.sendto(output,i)
        elif c[0] == "send":
            server.chat_log.insert(0,"[server]: %s" % string.join(c[1:]))
            output = "CHAT [server]: %s" % string.join(c[1:])
            for i in users:
                server.udp.socket.sendto(output,i)
        elif c[0] == "name":
            server.name = c[1]
        elif c[0] == "web":
            server.webiface()
            server.echo("Web server started.")
    sys.exit(1)
