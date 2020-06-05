import redis
import time
import random as r

names = []
class Worker:
    def __init__(self, conn):
        self._conn = conn

    def clearing_queue(self):
        connection = self._conn
        while True:
            if connection.lrange('message-queue', 0, -1) != []:
                time.sleep(r.uniform(0, 3))
                order = str(connection.lpop('message-queue'))
                message_obj = connection.hgetall(order)
                sender = message_obj.get('sender')
                recipient = message_obj.get('recipient')
                message = message_obj.get('message')
                connection.srem(f'in_queue:{sender}', message)
                rand = r.randint(0, 1000)
                if (rand % 2 == 0):
                    connection.zincrby('top-spam', float(1), sender)
                    connection.sadd(f'spammed:{sender}', message)
                    connection.publish('spam', order)
                else:
                    connection.zincrby('top-active', float(1), sender)
                    connection.sadd(f'recieved:{recipient}',message)
                    connection.sadd(f'sent:{sender}', message)
                    connection.publish('active', order)
