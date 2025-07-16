from rq import Worker, Queue
from redis import Redis

listen = ['video']
redis_conn = Redis()

if __name__ == '__main__':
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(queues)
    worker.work()
