from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
import random, pdb

maxwords = 25
nprefix = 3
maxary = 3 
minchoices = 2

aliases = ({'alias': 'user', 'stentor' : 'loxodes', 'kleinjt' : 'loxodes',
            'topmost' : 'tommost' , 'TBoneULS' : 'baty' ,
            'rthc' : 'chtr' , 'poppy_nogood' : 'chtr' , 'octavious' : 'joshc'});

server = 'irc.freenode.net'
channel = '#rhtest'
logfile = 'fish_scraps'


class MarkBotFactory(protocol.ClientFactory):
    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename 

    def buildProtocol(self, addr):
        p = MarkBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()
 
    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


class MarkBot(irc.IRCClient):
    nickname = 'markbot'

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.users = {}
        self.buildUsers()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def privmsg(self, user, channel, msg):
        if msg.startswith('.mimic'):
            author = self.findUser(msg.split()[1])
            if author is self.nickname:
                self.msg(channel, '.slap ' + user.split('!', 1)[0])
            elif author in self.users:
                quote = self.users[author].spit_line()
                self.msg(channel, '< ' + author + '> ' + quote)                
            elif not author in self.users:
                self.msg(channel, 'sorry, ' + author + ' was not found')

    def buildUsers(self):
        f = open(logfile,'r')
        for line in f:
            if(self.lineCheck(line)):
                s = line.split()
                a = self.findUser(s[2])
                if not a in self.users: 
                    self.users[a] = User()
                w = s[3:]
                self.users[a].add_message(w)
 
    def findUser(self, author):
        author = author.lstrip(' ')
        author = author.rstrip(' ')
        author = author.lstrip('@')
        author = author.lstrip('+')
        author = author.rstrip('_')
        
        if author in aliases:
            author = aliases[author]
        return author


    def lineCheck(self, line):
        for c in ['-!-', ' * ', '-->', '.mimic', '<--', 'http']: 
            if c in line:
                return 0
        for c in ['-', ':']:
            if not c in line:
                return 0
        return 1;

class User:
    def __init__(self):
        self.pre = {}
        self.ribbons = [{} for i in range(maxary)]

    def add_pre(self, w):
        words = ' '.join(w) 
        if not words in self.pre:
            self.pre[words] = 0
        self.pre[words] += + 1

    def add_message(self, words):
        self.add_pre(words[0:nprefix])
        words.append('EOL')
        for j in range(1,maxary+1): 
            for i in range(nprefix, len(words)):
                prefix = ' '.join(words[i-j:i])
                if not prefix in self.ribbons[j-1]:
                    self.ribbons[j-1][prefix] = {}
                if not words[i] in self.ribbons[j-1][prefix]:
                    self.ribbons[j-1][prefix][words[i]] = 0;
                self.ribbons[j-1][prefix][words[i]] += 1
        
    def spit_word(self, prefix):
        for i in range(maxary,0,-1):
            words = []
            try: nxt = self.ribbons[i-1][' '.join(prefix[-i:])]
            except KeyError: continue
            for n, c in nxt.iteritems():
                for j in range(c):
                    words.append(n)
            if(len(words) >= minchoices):
                break
        return random.choice(words)

    def spit_pre(self):
        pres = []
        for p, c in self.pre.iteritems():
            for i in range(c):
                pres.append(p)
        return random.choice(pres).split()

    def spit_line(self):
        line = self.spit_pre()
        if(len(line) == maxary):
            for i in range(maxwords):
                line.append(self.spit_word(line[-maxary:]))
                if(line[-1] == 'EOL'):
                    line = line[0:-1]
                    break 
        return ' '.join(line)

if __name__ == "__main__":
    f = MarkBotFactory(channel, logfile)
    reactor.connectTCP(server, 6667, f)
    reactor.run()
