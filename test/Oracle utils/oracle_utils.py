import cx_Oracle
from getpass import getpass
from subprocess import Popen, PIPE

uid=""
pwd=""
sqlCommand="Select 'HELLO', sysdate,'WORLD' from dual"


def authenticate():
    global uid,pwd
    uid = raw_input("Enter USERNAME: ")
    print
    print "DATABASE password"
    pwd=getpass()


def exec_command(sid,sqlCommand):
    connectString=uid + "/" + pwd + "@" + sid
    session = Popen(['sqlplus', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
#    session = Popen(['sqlplus', '-S', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    session.stdin.write(sqlCommand)
    queryResult, errorMessage = session.communicate()
    print queryResult.decode(encoding='UTF-8')
    print errorMessage.decode(encoding='UTF-8')
	
	
def cx_query(sid,query):

    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    print "Count:", cursor.rowcount
    if cursor.rowcount==0:
        print "No rows returned"
    else:
        for i in range(0,cursor.rowcount):
            for j in range(0,len(rows[i])):
                if j < len(rows[i]) and j!=0:
                    print "-----",
                print rows[i][j],
                
    cursor.close()
    	

authenticate()

#After importing and authenticating, the script can be used as below:
#exec_command("POLS",sqlCommand)
#cx_query("POLS",sqlCommand)
