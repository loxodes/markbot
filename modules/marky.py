import re, pdb, random
nary = 1
maxwords = 20
logfile = 'fish_scraps'

aliases = ({'alias': 'user', 'stentor' : 'loxodes', 'kleinjt' : 'loxodes'});

users = {} 
def main():
    print __doc__.strip()

def mimic(phenny, input):
    buildusers()
    u = input.group(2).encode("utf8")
    a = finduser(u)
    if a in users:
        user = users[a]
        phenny.say(user.spit_line())
    if not a in users:
        phenny.say('sorry, ' + a + ' was not found')

mimic.commands = ['mimic'] 

def buildusers():
    f = open(logfile,'r')
    for line in f:
        if(linecheck(line)):
            s = line.split()
            a = finduser(s[2])
            if not a in users: 
                users[a] = User()
            
            w = s[3:]
            users[a].add_message(w)  
    
def finduser(author):
    author = author.rstrip('_')
    author = author.lstrip('@')
    author = author.lstrip('+')
    if author in aliases:
        author = aliases[author]
    return author

def linecheck(line):
    for c in ['-!-', ' * ', '-->', '.mimic', '<--']: 
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
    main()

