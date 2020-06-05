import redis
import time
import subprocess as sp

class View:
    def __init__(self, conn, username=""):
        self._conn = conn
        self._username = username
        self._pubsub = conn.pubsub()
        self._online = set([])
        self._offline = set([])
        self._journal = []
        #self._pubsub.subscribe(['online', 'offline', 'spam'])

    def adminUI(self):
        self.adminMenu()
        self._pubsub.psubscribe(**{'o*':self.custom_handler, 'active':self.custom_handler, 'spam':self.custom_handler})
        self.thread = self._pubsub.run_in_thread(sleep_time=0.001)
        while True:
            print()
            print('\033[94m=>\033[0m', end = '')
            n = input()
            if (n == '1'):
                print('--------------JOURNAL--------------')
                self.showJournal()
            elif (n == '2'):
                self.showOnline()
            elif (n == '3'):
                N = int(input('Enter the amount of spammers to show \n\033[94m=>\033[0m'))
                self.showSpamers(N)
            elif (n == '4'):
                N = int(input('Enter the amount of active senders to show \n\033[94m=>\033[0m'))
                self.showActive(N)
            elif (n == '5'):
                self.thread.stop()
                break

    def getConnection(self):
        return self._conn

    def setUsername(self, username):
        self._username = username

    def userMenu(self):
        print("Entered as user")
        print('''\033[1mChoose among options\033[0m
        1 - write a message
        2 - show all my message groups
        3 - go back to login ''')

    def adminMenu(self):
        print("Entered as admin")
        print('''\033[1mChoose among options\033[0m
        1 - show activity journal
        2 - show people online
        3 - show top N spamers
        4 - show top N active senders
        5 - go back to login ''')

    def createNewMessage(self, sender, recipient, message):
        mes_id = str(self._conn.incr('message:'))
        self._conn.hmset('message:' + mes_id, {
            'sender': sender,
            'recipient': recipient,
            'message': message
        })
        now = time.time()
        self._conn.rpush('message-queue', 'message:' + mes_id)
        print('create ' + mes_id)
        self._conn.sadd('in_queue:' + sender, message)

    def showOnline(self):
        self._online -= self._offline
        self._offline.clear()
        count = 0
        for item in self._online:
            print(item)
            count += 1
        print(f'\033[93mTotal count of people online:\033[0m \033[1m{count}\033[0m\n\033[94m=>\033[0m', end='')

    def showSpamers(self, spamers):
        for spamer in self._conn.zrevrange('top-spam', 0, spamers - 1, withscores=True):
            print(spamer)

    def showActive(self, active):
        for one in self._conn.zrevrange('top-active', 0, active - 1, withscores=True):
            print(one)

    def customHandler(self, mes):
        # sp.call('cls', shell=True)
        if (mes['type'] == 'pmessage'):
            data = mes['data']
            ch = mes['channel']
            if (ch == 'online' or ch == 'offline'):
                self._journal.append(f"{data} went {ch}")
            elif (ch == 'online'):
                self._online.add(data)
            elif (ch == 'offline'):
                self._offline.add(data)
            elif (ch == 'active' or ch == 'spam'):
                message_obj = self._conn.hgetall(data)
                self._journal.append(f"{message_obj.get('sender')} wrote \033[1m{ch if ch == 'spam' else 'regular'}\033[0m message to {message_obj.get('recipient')}: {message_obj.get('message')}")
            print('\033[93mHandler called!\033[0m')

    def showJournal(self):
        for i in self._journal:
            print(i)

    def userUI(self):
        self.userMenu()
        while True:
            print()
            amount = self._conn.scard('recieved:' + self._username)
            if (amount > 0):
                print(f'\033[92mYou have {amount} new message(s)!\033[0m')
            print('\033[94m=>\033[0m', end = '')
            n = input()
            if (n == '1'):
                mes = input("Come up with a message: ")
                recipient = input("Who`s a recipient: ")
                self.createNewMessage(self._username, recipient, mes)
                print("Message is created and put in queue...")
            elif (n == '2'):
                c = self._conn
                usr = self._username
                i = 1
                groups = ['recieved:', 'in_queue:', 'check_for_spam:', 'spammed:', 'sent:', 'read:']
                for group in groups:
                    if c.scard(group + usr) > 0:
                        print(f'Messages {group}')
                        for mes in c.smembers(group + usr):
                            print(str(i) + ') ' + mes)
                            i += 1
                        print()
                        i = 1
                        if (group == 'recieved:'):
                            while c.scard(group + usr) > 0:
                                c.sadd('read:' + usr, c.spop('recieved:' + usr))
            elif(n == '3'):
                break
