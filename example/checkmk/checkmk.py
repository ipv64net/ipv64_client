import statsCollector
from os import getenv, name as osname, path, makedirs
__REALAPPPATH__ = path.dirname(path.dirname(path.dirname(path.realpath(__file__))))
                            
import sys
import time
import threading
from socketserver import TCPServer,StreamRequestHandler
import sqlite3

nodeColor = False # Default Disable
if str(getenv('Node64Color')).lower() == "true":
    nodeColor=True

if len(sys.argv) == 2:
    nodeSecret = sys.argv[1]
elif getenv('Node64Secret'):
    nodeSecret = getenv('Node64Secret')
else:
    print(f"{sys.argv[0]} <your node secret>")
    sys.exit(1)


StopServer = False

def runserver():
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        time.sleep(10)
        print("Hello from Server")
    print("Server Stop")

class checkmk_checker(object):

    def do_checks(self,**kwargs):
        _lines = ["<<<check_mk>>>"]
        _lines.append("AgentOS: node64")
        _lines.append("Version: xy")
        _lines.append("Hostname: node64")

        con = sqlite3.connect(f"{__REALAPPPATH__}/stats/stats.db")
        fields = con.execute("SELECT field from tasks GROUP by field ORDER BY field ASC")
        overallruntime = 0.0
        overallcount = 0
        _lines.append("<<<local:sep(0)>>>")
        for field in fields:
            sql = f"SELECT count(*) as count, SUM(runtime) as runtime from tasks WHERE field = '{field[0]}'"
            #print(sql)
            results = con.execute(sql)
            data = results.fetchone()
            count = data[0]
            runtime = data[1] 
            overallcount += count
            overallruntime += runtime
            _lines.append(f'0 "Task {field[0]}" count={count}|runtime={round(runtime,0)} {count} {field[0]} Tasks with a {round(runtime,0)}s runtime')
        _lines.append(f'0 "node64 Tasks" count={overallcount}|runtime={round(overallruntime,0)} {overallcount} Tasks with a {round(overallruntime,0)}s runtime')

        fields = con.execute("SELECT field from tasks GROUP by field ORDER BY field ASC")
        todayruntime = 0.0
        todaycount = 0
        for field in fields:
            sql = f"SELECT count(*) as count, SUM(runtime) as runtime from tasks WHERE field = '{field[0]}' and date(dt) = date('now')"
            #print(sql)
            results = con.execute(sql)
            data = results.fetchone()
            count = data[0]
            runtime = data[1] 
            todaycount += count
            todayruntime += runtime
            _lines.append(f'0 "Task {field[0]} Today" count={count}|runtime={round(runtime,0)} {count} {field[0]} Tasks with a {round(runtime,0)}s runtime')
        _lines.append(f'0 "node64 Tasks Today" count={todaycount}|runtime={round(todayruntime,0)} {todaycount} Tasks with a {round(todayruntime,0)}s runtime')


        con.close()
        return "\n".join(_lines).encode("utf-8")

class checkmkHandler(StreamRequestHandler):
    def handle(self):
        try:
            _msg = checkmk_checker.do_checks(self)
        except Exception as e:
            raise
            _msg = str(e).encode("utf-8")
        try:
            self.wfile.write(_msg)
        except:
            pass

def runserver():
    
    aServer = TCPServer(('', 6556), checkmkHandler)
    aServer.serve_forever()

if __name__ == "__main__":
    if osname != 'nt':
        from os import geteuid
        if geteuid() != 0:
            exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
    
    isExist = path.exists(f"{__REALAPPPATH__}/stats")
    if not isExist:
        makedirs(f"{__REALAPPPATH__}/stats")

    threadserver = threading.Thread(target=runserver)
    threadserver.start()
    client = statsCollector.statsCollector(nodeSecret,nodeColor)
    if getenv('Node64MaxWait'):
        client.MaxWait = int(getenv('Node64MaxWait'))
    client.run()
    threadserver.do_run = False
    #runserver()


