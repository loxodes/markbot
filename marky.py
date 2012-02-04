# marky, the markov chain irc bot
# jon klein
# mit license
# kleinjt@ieee.org

from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
import random, time, shelve
import parsedatetime
import parsedatetime.parsedatetime as pdt 
import parsedatetime.parsedatetime_consts as pdc 

# cooldown before 
cooldown = 60 

# upper and lower bound before anti-flooding measures
minuses = 2
maxuses = 4

# max chain length
maxwords = 25

# markov chain max prefix length
nprefix = 3

# max-ary markov chain
maxary = 3 

# minimum choices before backing off to lower order markov chain
minchoices = 2


aliases = ({'stentor' : 'loxodes', 'kleinjt' : 'loxodes',
            'topmost' : 'tommost' , 'TBoneULS' : 'baty' ,
            'rthc' : 'chtr' , 'poppy_nogood' : 'chtr' , 'octavious' : 'joshc'})

server = 'irc.freenode.net'
channel = '#rhnoise'

# filename of weechat style irc log
logfile = 'fish_scraps'

# filename of shelved .delays
shelffile = 'bookshelf'

# parsedatetime constants
pdc_const = pdc.Constants()
pdc_cal = pdt.Calendar(pdc_const)

class MarkBotFactory(protocol.ClientFactory):
    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename 

    def buildProtocol(self, addr):
        p = MarkBot()
        p.factory = self
        p.reshelve()
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()
 
    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


class MarkBot(irc.IRCClient):
    nickname = 'markbot'
    lineRate = .75
    maxlength = 220

    abusers = {}

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)
    
    def delayBlast(self, t):
        payload = self.shelf[t]
        del self.shelf[t]
        self.msg(channel, payload)
        self.shelf.sync()

    def decayAbuse(self, user):
       self.abusers[user] -= 1 

    def privmsg(self, user, channel, msg):
        if msg.startswith('.mimic'):
            author = self.findUser(msg.split()[1])
            
            # deter flooding..
            if not user in self.abusers:
                self.abusers[user] = 0
            self.abusers[user] += 1
            reactor.callLater(cooldown, self.decayAbuse, user)
            if self.abusers[user] > random.randint(minuses, maxuses):
                self.msg(channel, '.slap ' + user.split('!')[0])
                return
            
            # attempt to build markov chain for target user, spew sentence fragment 
            target = self.buildUser(author)
            if target.empty:
                self.msg(channel, 'sorry, ' + author + ' was not found')
            else:
                quote = target.spit_line()
                self.msg(channel, '< ' + author + '> ' + quote)                
        
        if msg.startswith('.delay'):
            delay = time.mktime(pdc_cal.parse(msg.split(';')[0].lstrip('.delay '))[0]) - time.mktime(time.gmtime())
            if delay < 0:
                return
            t = str(delay)
            self.shelf[t] = (msg.split(';')[-1].lstrip(' '))
            reactor.callLater(delay, self.delayBlast, t)
        
        # insecure, but entertaining
        #if msg.startswith('.eval'):
        #    try:
        #        self.msg(channel, str(eval(' '.join(msg.split(' ')[1:]))), length=self.maxlength)
        #    except Exception as err:
        #        nick = user.split("!")[0]
        #        self.msg(nick, "Error: " + str(err))

    def buildUser(self, author):
        f = open(logfile,'r')
        u = User()
        for line in f:
            if(self.lineCheck(line)):
                s = line.split()
                a = self.findUser(s[2])
                if not a == author:
                    continue
                w = s[3:]
                u.add_message(w)
        return u
    
    def reshelve(self):
        self.shelf = shelve.open(shelffile, writeback=True)
        for t in self.shelf.keys():
            if float(t) < time.time():
                del self.shelf[t]
            else:
                reactor.callLater(float(t) - time.time(), self.delayBlast, t)
        self.shelf.sync()

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
        return 1


class User:
    def __init__(self):
        self.pre = {}
        self.ribbons = [{} for i in range(maxary)]
        self.empty = True

    def add_pre(self, w):
        words = ' '.join(w) 
        if not words in self.pre:
            self.pre[words] = 0
        self.pre[words] += + 1

    def add_message(self, words):
        self.empty = False
        self.add_pre(words[0:nprefix])
        words.append('EOL')
        for j in range(1,maxary+1): 
            for i in range(nprefix, len(words)):
                prefix = intern(' '.join(words[i-j:i]))
                if not prefix in self.ribbons[j-1]:
                    self.ribbons[j-1][prefix] = {}
                if not words[i] in self.ribbons[j-1][prefix]:
                    self.ribbons[j-1][prefix][intern(words[i])] = 0
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
