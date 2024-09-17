import concurrent.futures
import requests
import threading
import time
import os

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

def function_file_5(message, seconds, file="/tmp/file"):
    print ("START %s" % message)
    with open(file, "a+", 1) as f: # third argument to force line-buffered
        time.sleep(seconds)
        for i in range(10):
            for j in range(10):
                for k in range(10):
                    f.write("%s,%s,%s,%s\n"%(threading.current_thread(), i,j,k))
    print ("END %s" % message)

def function_file_6(message, seconds, file="/tmp/file"):
    import pandas as pd
    from StringIO import StringIO

    print ("START %s" % message)
    with open(file, 'r') as f:
        time.sleep(seconds)
        str_cont = f.read()
    DATA = StringIO(str_cont.replace(',','\t'))
    df = pd.read_csv(DATA)
    print ("END %s" % message)

if __name__ == "__main__":
    reportes = [
        ["function_1", 3],
        ["function_2", 2],
        ["function_3", 0],
        ["function_4", 1],
        # files
        ["function_file_5", 1],
        ["function_file_5", 1],
        ["function_file_5", 1],
        ["function_file_5", 1],
        ["function_file_5", 1],
        # pandas
        ["function_file_6", 10],
        ["function_file_6", 10],
    ]

    print("Setting file test")
    file = open("/tmp/file", "w")
    file.write("")
    file.close()

    threads = []
    start_time = time.time()
    for i,r in enumerate(reportes):
        func = locals()[r[0]]
        t = threading.Thread(target=func, args=(r[0], r[1]))
        t.start()
        threads.append(t)
    x = len([t.join() for t in threads])
    duration = time.time() - start_time
    print("END %s seconds, functions executed: %s" % (duration, x))
