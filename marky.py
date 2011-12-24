from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
import random, pdb

nprefix = 2
nary = 2 
maxwords = 20

aliases = ({'alias': 'user', 'stentor' : 'loxodes', 'kleinjt' : 'loxodes',
            'topmost' : 'tommost' , 'TBoneULS' : 'baty' ,
            'rthc' : 'chtr' , 'poppy_nogood' : 'chtr' , 'octavious' : 'joshc'});

server = 'irc.freenode.net'
channel = "#rhnoise"
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
        self.users = buildusers()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def privmsg(self, user, channel, msg):
        if msg.startswith('.mimic'):
            author = finduser(msg.split()[1])
            if author is self.nickname:
                self.msg(channel, '.slap ' + user.split('!', 1)[0])
            elif author in self.users:
                quote = self.users[author].spit_line()
                self.msg(channel, '< ' + author + '> ' + quote)                
            elif not author in self.users:
                self.msg(channel, 'sorry, ' + author + ' was not found')

def buildusers():
    users = {}

    f = open(logfile,'r')
    for line in f:
        if(linecheck(line)):
            s = line.split()
            a = finduser(s[2])
            if not a in users: 
                users[a] = User()
            w = s[3:]
            users[a].add_message(w)
    return users
    
def finduser(author):
    author = author.lstrip(' ')
    author = author.rstrip(' ')
    author = author.lstrip('@')
    author = author.lstrip('+')
    author = author.rstrip('_')
    
    if author in aliases:
        author = aliases[author]
    return author

def linecheck(line):
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
        self.ribbons = {}

    def add_pre(self, w):
        words = ' '.join(w) 
        if not words in self.pre:
            self.pre[words] = 0
        self.pre[words] = self.pre[words] + 1

    def add_message(self, words):
        self.add_pre(words[0:nary])
        words.append('EOL')
        for i in range(nary, len(words)):
            prefix = ' '.join(words[i-nary:i])
            if not prefix in self.ribbons:
                self.ribbons[prefix] = {}
            if not words[i] in self.ribbons[prefix]:
                self.ribbons[prefix][words[i]] = 0;
            self.ribbons[prefix][words[i]] = self.ribbons[prefix][words[i]] + 1
    
    def spit_word(self, prefix):
        words = []
        nxt = self.ribbons[' '.join(prefix)]
        for n, c in nxt.iteritems():
            for i in range(c):
                words.append(n)

        return random.choice(words)

    def spit_pre(self):
        pres = []
        for p, c in self.pre.iteritems():
            for i in range(c):
                pres.append(p)
        return random.choice(pres).split()

    def spit_line(self):
        line = self.spit_pre()
        if(len(line) == nary):
            for i in range(maxwords):
                line.append(self.spit_word(line[-nary:]))
                if(line[-1] == 'EOL'):
                    line = line[0:-1]
                    break 
        return ' '.join(line)

if __name__ == "__main__":
    f = MarkBotFactory(channel, logfile)
    reactor.connectTCP(server, 6667, f)
    reactor.run()
