import concurrent.futures
import requests
import threading
import time

thread_local = threading.local()

def timmer(message, seconds):
    print ("START %s" % message)
    time.sleep(seconds)
    print ("END %s" % message)    

def function_1(message, seconds):
    timmer(message, seconds)
def function_2(message, seconds):
    timmer(message, seconds)
def function_3(message, seconds):
    timmer(message, seconds)
def function_4(message, seconds):
    timmer(message, seconds)
    #raise Exception("Error X")

if __name__ == "__main__":
    reportes = [
        ["function_1", 4],
        ["function_2", 3],
        ["function_3", 1],
        ["function_4", 2],
    ]

    threads = []
    start_time = time.time()
    for r in reportes:
        func = locals()[r[0]]
        t = threading.Thread(target=func, args=(r[0], r[1]))
        t.start()
        threads.append(t)
    x = len([t.join() for t in threads])
    duration = time.time() - start_time
    print("END %s seconds, functions executed: %s" % (duration, x))
