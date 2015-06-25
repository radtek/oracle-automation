#!/usr/bin/python

# Namespace
######################################################
import decimal
import os,sys
import getopt
import cx_Oracle
import Queue,threading

import xlwt,xlrd
import time,os

from xlutils.copy import copy
from subprocess import Popen, PIPE
from getpass import getpass

######################################################

start_time = time.time()

#base_dir='C:\Users\\shsrinivasan\\Documents\\pyScrub\\'
base_dir='C:\dbscrub\\'
date=time.strftime("%m-%d-%Y_%H%M%S")

logfile=''

ols_hash=''
ecollege_hash=''
ols_db_name=''

uid=''
pwd=''
sid=''

exitFlag = 0
queueLock = threading.Lock()
workQueue = Queue.Queue()

def exec_script(sqlCommand,sid,uid,pwd):
    connectString=uid + "/" + pwd + "@" + sid
    session = Popen(['sqlplus', '-S', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    session.stdin.write(sqlCommand)
    return session.communicate()

def does_table_exist(sid,schema,table):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute("select status from dba_objects where owner ='"+schema.upper()+"' and object_name='"+table.upper()+"'")
    rows = cursor.fetchall()
    print("#-records:", cursor.rowcount)
    try:
        print(rows[0][0])
        cursor.close()
    except IndexError:
        cursor.close()
        return False
    return True


def does_schema_exist(sid,schema):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute("select account_status, default_tablespace, temporary_tablespace from dba_users where username ='"+schema.upper()+"'")
    rows = cursor.fetchall()
    try:
        for i in range(0, 3):
            print (rows[0][i])
        cursor.close()
    except IndexError:
        cursor.close()
        return False
    return True

def does_scrub_package_exist(sid):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute("select status from dba_objects where owner='DATAMASKER' and object_name ='DBSCRUB' and object_type='PACKAGE BODY'")
    rows = cursor.fetchall()
    try:
        package_status=rows[0][0]
    except IndexError:
        cursor.close()
        return False
    print "Scrub package Status: "+package_status
    if package_status=='VALID':
        cursor.close()
        return True
    else:
        cursor.close()
        return False

def is_wallet_open(sid):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute("select status from v$encryption_wallet")
    rows = cursor.fetchall()
    print
    wallet_status=rows[0][0]
    print "Wallet Status: "+wallet_status
    if wallet_status=='OPEN':
        cursor.close()
        return True
    else:
        cursor.close()
        return False

def dm_list_check(sid):
    if does_table_exist(sid,'datamasker','dm_list'):
        print
        print "DM_LIST already exists. Checking records against spreadsheet..."
        
    else:    
        print
        print "NO DM_LIST FOUND, CREATING..."
        result,error = exec_script('''
Prompt "Creating table datamasker.dm_list....."
CREATE TABLE "DATAMASKER"."DM_LIST"
   (  "ID" NUMBER NOT NULL ENABLE,
  "DATABASE" VARCHAR2(30) NOT NULL ENABLE,
  "SCHEMA" VARCHAR2(30) NOT NULL ENABLE,
  "TABLE_NAME" VARCHAR2(50) NOT NULL ENABLE,
  "COLUMN_NAME" VARCHAR2(50) NOT NULL ENABLE,
  "TYPE" VARCHAR2(20) NOT NULL ENABLE,
  "ACTIVE" VARCHAR2(1) NOT NULL ENABLE,
  "COMMENTS" VARCHAR2(250),
  "PRIMARY_KEY" VARCHAR2(50),
  "PACKAGE_FUCNTION_NAME" VARCHAR2(30),
  "COMPLETION_STATUS" VARCHAR2(10)
 );
''',sid,uid,pwd)
        print result,error
        load_dm_list(sid)
        


def db_links_validate(sid):
    db = cx_Oracle.connect('datamasker' + "/" + 'datamasker' + "@" + sid)
    cursor = db.cursor()
    try:
        cursor.execute("select 'GOING' FROM DUAL@OLS.K12.COM")
    except:
        return False
    rows = cursor.fetchall()
    result=rows[0][0]
    if result=='GOING':
        try:
            cursor.execute("select 'DEEPER' FROM DUAL@ECOLLEGE.K12.COM")
        except:
            return False
        rows = cursor.fetchall()
        result=rows[0][0]
        if result=='DEEPER':
            return True
        else:
            return False

def db_links_check(sid):
    global ols_hash
    global ecollege_hash
    global ols_db_name
    ols_db_name=sid.replace('ODB','OLS')
    print 'CHECKING DB_LINKS'
    print
    if db_links_validate(sid):
        print 'DB LINKS TO '+ols_db_name+' FOUND!'
        print
    else:
        print 'SCRUBBING ODB REQUIRES DB_LINKS CREATED TO '+ols_db_name+' DATABASE';
        links = raw_input("CREATE THEM NOW? ")
        if links.upper() == 'YES':
            db = cx_Oracle.connect(uid + "/" + pwd + "@" + ols_db_name)
            cursor = db.cursor()
            cursor.execute("select spare4 from sys.user$ where name='OLS'")
            rows = cursor.fetchall()
            ols_hash=rows[0][0]

            cursor.execute("select spare4 from sys.user$ where name='ECOLLEGE'")
            rows = cursor.fetchall()
            ecollege_hash=rows[0][0]

            cursor.close()
            result, error = exec_script('ALTER USER OLS IDENTIFIED BY datamasker;',ols_db_name,uid,pwd)
            print result,error
            result, error = exec_script('ALTER USER ECOLLEGE IDENTIFIED BY datamasker;',ols_db_name,uid,pwd)
            print result,error

            result, error = exec_script("""
DROP DATABASE LINK "OLS.K12.COM";
CREATE DATABASE LINK "OLS.K12.COM"
 CONNECT TO OLS
 IDENTIFIED BY datamasker
 USING '{ols}';
""".format(ols=ols_db_name),sid,'datamasker','datamasker')
            print error

            result, error = exec_script("""
DROP DATABASE LINK "ECOLLEGE.K12.COM";
CREATE DATABASE LINK "ECOLLEGE.K12.COM"
 CONNECT TO ECOLLEGE
 IDENTIFIED BY datamasker
 USING '{ols}';
""".format(ols=ols_db_name),sid,'datamasker','datamasker')
            print error

            if db_links_validate(sid):
                print
                print 'DB LINKS CREATED SUCCESSFULLY.'
            else:
                print
                print 'ERRORS CREATING DB_LINKS, PLEASE CREATE MANUALLY.'
        else:
            print "NO LINKS WERE CREATED, ABORTING..."
            exit
        
def dm_user_check(sid):
    print "SCRUBBING WILL BE PERFORMED WITH THE 'DATAMASKER' USER"
    print "NOW CHECKING IF USER EXISTS IN THE TARGET DATABASE"

    if does_schema_exist(sid,'datamasker'):
        print
        print 'DATAMASKER FOUND!'
        print
    else:
        print
        print 'NO DATAMASKER USER FOUND, CREATING...'
        exec_script('create user datamasker identified by datamasker default tablespace users temporary tablespace temp;',sid,uid,pwd)
        exec_script('grant dba to datamasker;',sid,uid,pwd)    


def prerequisite_checks(sid):

    dm_user_check(sid)
    
    if 'ODB' in sid:
        if is_wallet_open(sid):
            print "WALLET OPEN!!"
        else:
            print "WALLET CLOSED"
            open_wallet = raw_input("OPEN WALLET NOW? ")
            if open_wallet.upper() == 'YES':
                result, error = exec_script('ALTER SYSTEM SET WALLET OPEN IDENTIFIED BY "w1nt3r2010#";',sid,uid,pwd)
                print result
            else:
                print "WALLET MUST BE OPENED FOR ODB SCRUBBING, EXITING..."
                exit
        print
        db_links_check(sid)
    else:
        print "Wallet not needed."
    
    dm_list_check(sid)

def reset_ols_auth():

    print "RESETTING CREDENTIALS FOR OLS USERS..."
    print
    reset_ols = "ALTER USER OLS IDENTIFIED BY VALUES '"+ols_hash+"';"
    result, error = exec_script(reset_ols,ols_db_name,uid,pwd)
    print result,error

    reset_ecollege = "ALTER USER ECOLLEGE IDENTIFIED BY VALUES '"+ecollege_hash+"';"
    result, error = exec_script(reset_ecollege,ols_db_name,uid,pwd)
    print result,error

def authenticate():
    global uid
    global pwd
    uid = raw_input("Enter USERNAME: ")
    print
    print "DATABASE password"
    pwd=getpass()
    print


def load_dm_list(sid):
    print
    print "NOW LOADING THE DM_LIST..."
    dm_master=base_dir+'master_dm_list.xls'
    workbook = xlrd.open_workbook(dm_master)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)

    db = cx_Oracle.connect("datamasker" + "/" + "datamasker" + "@" + sid)
    cursor = db.cursor()
    
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0
    while curr_row < num_rows:
	curr_row += 1
        curr_id = int(worksheet.cell_value(curr_row,0))
	curr_database = worksheet.cell_value(curr_row,1)
        curr_schema = worksheet.cell_value(curr_row,2)
        curr_table = worksheet.cell_value(curr_row,3)
        curr_column = worksheet.cell_value(curr_row,4)
        curr_type = worksheet.cell_value(curr_row,5)
        curr_active = int(worksheet.cell_value(curr_row,6))
        curr_comments = worksheet.cell_value(curr_row,7)
        curr_pk = worksheet.cell_value(curr_row,8)
        curr_pkg_function = worksheet.cell_value(curr_row,9)
        curr_completion = worksheet.cell_value(curr_row,10)
        if curr_database in sid:
            cursor.execute("""
INSERT INTO DM_LIST (ID,DATABASE,SCHEMA,TABLE_NAME,COLUMN_NAME,TYPE,ACTIVE,COMMENTS,PRIMARY_KEY,PACKAGE_FUCNTION_NAME)
VALUES ({id},'{database}','{schema}','{table}','{column}','{typ}','{active}','{comments}','{pk}','{pkg_funct}')
""".format(id=curr_id,database=curr_database,schema=curr_schema,table=curr_table,column=curr_column,typ=curr_type,active=curr_active,comments=curr_comments,pk=curr_pk,pkg_funct=curr_pkg_function))
            cursor.execute("commit")

    cursor.close()        

def scrub_package_check(sid):
    if does_scrub_package_exist(sid):
        print
        print "SCRUB PACKAGE FOUND!"
    else:
        print
        print "NO SCRUB PACKAGE FOUND, CREATING..."
        result,error = exec_script("""
CREATE OR REPLACE PACKAGE dbscrub AS
  scrub_passtable_value varchar2(20);
  scrub_email_value    varchar2(100);
  Function scrub_bday(bday IN DATE) RETURN DATE;
  Function scrub_commafullname(full_name IN varchar2) RETURN varchar2;
  Function scrub_email RETURN varchar2;
  Function scrub_fullname(full_name IN varchar2) RETURN varchar2;
  Function scrub_lname(name IN varchar2) RETURN varchar2;
  Function scrub_passtable RETURN varchar2;
  Function scrub_phone(input_no IN varchar2) RETURN varchar2;
  Function scrub_ssn RETURN number;
     function encrypt(p_x in varchar2) return varchar2;
     function decrypt(p_x in varchar2) return varchar2; 
     capitals VARCHAR2(26) :=  'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
     lowercase VARCHAR2(26) := 'abcdefghijklmnopqrstuvwxyz';
     numerals VARCHAR2(10) := '1234567890';

     salt              NUMBER := 7;
     decryption_string VARCHAR2(62) := 	concat(substr(capitals,mod(salt,26),length(capitals)),substr(capitals,0,mod(salt,26)-1)) ||
			concat(substr(lowercase,mod(salt,26),length(lowercase)),substr(lowercase,0,mod(salt,26)-1))  ||
			concat(substr(numerals,mod(salt,10),length(numerals)),substr(numerals,0,mod(salt,10)-1));
     unencrypted VARCHAR2(62) := capitals||lowercase||numerals;
     
END dbscrub;
/

CREATE OR REPLACE PACKAGE BODY dbscrub AS

  function encrypt(p_x in VARCHAR2)
return VARCHAR2
as
    begin
         return ( translate(p_x,
            unencrypted,
            decryption_string));
    end encrypt;

function decrypt(p_x in varchar2)
return varchar2
as
    begin
         return( translate(p_x,
            decryption_string,
            unencrypted));
    end decrypt;
  
  Function scrub_bday(bday IN DATE) RETURN DATE IS
    new_bday DATE;
  BEGIN
    new_bday := bday - (2 * TO_CHAR(bday, 'MM')) + TO_CHAR(bday, 'DD');
    RETURN(new_bday);
  END;

  Function scrub_commafullname(full_name IN varchar2) RETURN varchar2 IS

  BEGIN
	return(encrypt(full_name));
  END;

  Function scrub_email RETURN varchar2 AS
  BEGIN
    RETURN(scrub_email_value);
  END;

  Function scrub_fullname(full_name IN varchar2) RETURN varchar2 IS
  BEGIN
	RETURN(encrypt(full_name));
  END;

  Function scrub_lname(name IN varchar2) RETURN varchar2 IS
  BEGIN
    RETURN(encrypt(name));
  END;

  Function scrub_passtable RETURN varchar2 AS
  BEGIN
    RETURN(scrub_passtable_value);
  END;

  Function scrub_phone(input_no IN varchar2) RETURN varchar2 IS
  BEGIN
	return(encrypt(input_no));
  END;

  Function scrub_ssn RETURN number AS
  BEGIN
    RETURN(substr(to_char(systimestamp, 'SSSSSFF') / 1000, 3));
  END;

END dbscrub;
/
""",sid,'datamasker','datamasker')
        print result
        print error


def execute_grants(sid):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()

    cursor.execute("""
select distinct 'GRANT ALL ON ' || dm_list.schema || '.' || dm_list.table_name || ' to datamasker'
from datamasker.dm_list, dba_tables
where dm_list.schema=dba_tables.owner
AND dm_list.table_name=dba_tables.table_name
""")
    rows = cursor.fetchall()
    for i in range(0, cursor.rowcount):
        cursor.execute(rows[i][0])
    print "GRANTS COMPLETE"
    print
    print "DISABLING TRIGGERS..."
    cursor.execute("""
select distinct 'ALTER TABLE ' || dm_list.schema || '.' || dm_list.table_name || ' DISABLE ALL TRIGGERS'
from datamasker.dm_list, dba_tables
where dm_list.schema=dba_tables.owner
AND dm_list.table_name=dba_tables.table_name
""")
    rows = cursor.fetchall()
    for i in range(0, cursor.rowcount):
        cursor.execute(rows[i][0])    
    print "TRIGGERS DISABLED"
    cursor.close()

def enable_triggers(sid):
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()    
    print "RE-ENABLING TRIGGERS..."
    cursor.execute("""
select distinct 'ALTER TABLE ' || dm_list.schema || '.' || dm_list.table_name || ' ENABLE ALL TRIGGERS'
from datamasker.dm_list, dba_tables
where dm_list.schema=dba_tables.owner
AND dm_list.table_name=dba_tables.table_name
""")
    rows = cursor.fetchall()
    for i in range(0, cursor.rowcount):
        cursor.execute(rows[i][0])    
    print "TRIGGERS ENABLED"
    cursor.close()

def execute_scrub(sid):
    print
    print "ALL CHECKS PASSED, READY TO PERFORM SCRUBBING"
    print "NOW GRANTING NECESSARY PERMISIONS..."
    print
    execute_grants(sid)
    print
    print "RETRIEVING LIST OF TABLES FOR SCRUBBING"
    print
    db = cx_Oracle.connect('datamasker' + "/" + 'datamasker' + "@" + sid)
    cursor = db.cursor()
    cursor.execute("""
select 'update /*+ parallel(a,8) */ ' || t1.schema ||'.'||t1.table_name || ' a set ' ||listagg(t1.column_name||'='||
case when PACKAGE_FUCNTION_NAME like 'dbscrub%' then PACKAGE_FUCNTION_NAME||'('||t1.column_name||')'
else ''''||PACKAGE_FUCNTION_NAME||'''' end,', ') within group(order by column_name) ||';'
from dm_list t1, all_tables t2
where t1.schema=t2.owner(+)
and   t1.table_name=t2.table_name
and   t1.active = 1
and   t1.type !='Null'
group by t1.schema,t1.table_name
order by t1.schema,t1.table_name
""")
    result = cursor.fetchall()
    table_list = []
    for i in range(0, cursor.rowcount):
        table_list.append(result[i][0])

    cursor.close()
    #for j in range(0,len(table_list)):
        #print table_list[j]
    print
    print "DO NOT CLOSE THIS WINDOW UNTIL THE MESSAGE 'Scrub Completed' DISPLAYS"
    print
    print '...'
    #threadList = ["Thread-1", "Thread-2", "Thread-3","Thread-4","Thread-5","Thread-6","Thread-7","Thread-8"]
    threadList = ["Thread-1", "Thread-2", "Thread-3","Thread-4","Thread-5","Thread-6","Thread-7"]
    threads = []
    threadID = 1

    global exitFlag
    global queueLock
    global workQueue
    
    # Create new threads
    for tName in threadList:
        thread = myThread(threadID, tName, workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1
    
    # Fill the queue
    queueLock.acquire()
    for table in table_list:
        workQueue.put(table)
    queueLock.release()

    # Wait for queue to empty
    while not workQueue.empty():
        pass

    # Notify threads it's time to exit
    exitFlag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print    
    print "Exiting Main Thread"


def scrub_database(sid):
    global logfile
    logfile=base_dir+"MiCORE_SCRUB_"+sid+"_"+date+".log"
    print "\nLOGS WILL BE WRITTEN TO: "+logfile
    authenticate()
    prerequisite_checks(sid)
    scrub_package_check(sid)
    execute_scrub(sid)
    ctas(sid)
    seq_update()
    enable_triggers(sid)

    if ols_hash!='':
        reset_ols_auth()

    seconds=(time.time() - start_time)    
    minutes = seconds // 60
    hours = minutes // 60    
    with open(logfile, 'a') as f:
        print >>f,"--- TOTAL RUNTIME: %02d:%02d:%02d ---" % (hours, minutes % 60, seconds % 60)

    print "--- Scrub Completed ---"    

def ctas(sid):
    ctas_array = []
    drop_array = []
    rename_array=[]
    print
    print "EXECUTING CTAS ON LARGE TABLES WHICH DRAIN UNDO TABLESPACE..."
    db = cx_Oracle.connect('datamasker' + "/" + 'datamasker' + "@" + sid)
    cursor = db.cursor()
    cursor.execute("""
select distinct t1.schema,t1.table_name
from dm_list t1, all_tables t2
where t1.schema=t2.owner(+)
and   t1.table_name=t2.table_name
and   t1.active = 2
and   t1.type !='Null'
group by t1.schema,t1.table_name
order by t1.schema,t1.table_name
""")
    ctas_list = cursor.fetchall()
    num_tables=cursor.rowcount
    for i in range(0, num_tables):
        curr_schema=ctas_list[i][0]
        curr_table=ctas_list[i][1]
        full_name=curr_schema+'.'+curr_table
        scrub_cols=[]
        drop_array.append("DROP TABLE "+full_name)
        #print curr_table
        cursor.execute("""
select column_name
from dm_list
where schema='{SCHEMA}'
and table_name='{TABLE}'
and   active = 2
and   type !='Null'
""".format(SCHEMA=curr_schema,TABLE=curr_table))
        result = cursor.fetchall()
        for r in range(0,cursor.rowcount):
            scrub_cols.append(result[r][0])
        cursor.execute("""
select COLUMN_NAME||',' from dba_tab_columns where OWNER='{SCHEMA}' and TABLE_NAME='{TABLE}'
""".format(SCHEMA=curr_schema,TABLE=curr_table))
        cols = cursor.fetchall()
        new_table=curr_schema+"."+curr_table+'_NEW'
        rename_array.append("ALTER TABLE "+new_table+" RENAME TO "+curr_table)
        ctas_statement="CREATE TABLE "+new_table+" AS SELECT "        
        
        for j in range(0, cursor.rowcount):
            current_column=cols[j][0]
            nocomma = current_column.rstrip(',')
            if nocomma not in scrub_cols:
                if j==cursor.rowcount-1:
                    ctas_statement=ctas_statement+nocomma
                else:
                    ctas_statement=ctas_statement+current_column
            else:              
                new_line="dbscrub.encrypt("+nocomma+") "+nocomma
        
                if j==cursor.rowcount-1:
                    ctas_statement=ctas_statement+new_line
                else:
                    ctas_statement=ctas_statement+new_line+','
        ctas_statement=ctas_statement+" from "+full_name
        print
        ctas_array.append(ctas_statement)
    
    for k in ctas_array:
        begin=time.time()
        with open(logfile, 'a') as f:
            print >>f,"Executing "+k
        cursor.execute(k)
        time_exec(begin,time.time())
    for l in drop_array:
        begin=time.time()
        with open(logfile, 'a') as f:
            print >>f,"Executing "+l        
        cursor.execute(l)
        time_exec(begin,time.time())
    for m in rename_array:
        begin=time.time()
        with open(logfile, 'a') as f:
            print >>f,"Executing "+m
        cursor.execute(m)
        time_exec(begin,time.time())
       
    cursor.close()
    
def time_exec(start,end):
    seconds=(time.time() - start_time)    
    minutes = seconds // 60
    hours = minutes // 60    
    with open(logfile, 'a') as f:
        print >>f,"Elapsed: %02d:%02d:%02d" % (hours, minutes % 60, seconds % 60)


def seq_update():
    print
    print "UPDATING WITH SEQUENCES FOR TABLES WHICH WERE CAUSING CONSTRAINT VIOLATIONS"
    db = cx_Oracle.connect('datamasker' + "/" + 'datamasker' + "@" + sid)
    cursor = db.cursor()
    cursor.execute("""
select distinct t1.schema,t1.table_name,t1.column_name
from dm_list t1, all_tables t2
where t1.schema=t2.owner(+)
and   t1.table_name=t2.table_name
and   t1.active = 3
and   t1.type !='Null'
group by t1.schema,t1.table_name,t1.column_name
order by t1.schema,t1.table_name,t1.column_name
""")
    seq_list = cursor.fetchall()
    num_cols=cursor.rowcount
    for i in range(0, num_cols):
        curr_schema=seq_list[i][0]
        curr_table=seq_list[i][1]
        curr_column=seq_list[i][2]
        print curr_schema+'.'+curr_table,curr_column
        result,error=exec_script("""
drop sequence phone_nums;
create sequence phone_nums start with 2021010001 increment by 1;
""",sid,'datamasker','datamasker')
        print result,error
        update_statement="update {schema}.{table} set {column}=phone_nums.nextval;".format(schema=curr_schema,table=curr_table,column=curr_column)
        full_statement="""set timing on
"""+update_statement+"""
commit;"""
        with open(logfile, 'a') as f:
            print >>f,"Executing "+update_statement
        result,error=exec_script(full_statement,sid,'datamasker','datamasker')
        with open(logfile, 'a') as f:
            print >>f,result,error
                

class myThread (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        with open(logfile, 'a') as f:
            print >>f,"Starting " + self.name+"\n"
        process_table(self.name, self.q)
        with open(logfile, 'a') as f:
            print >>f,"Exiting " + self.name+"\n"


def process_table(threadName, q):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            data = q.get()
            with open(logfile, 'a') as f:
                print >>f,"%s executing %s" % (threadName, data)+"\n"
            queueLock.release()
            data1="""set timing on
set echo on
set feedback on
"""+data+"""
commit;"""
            result,error = exec_script(data1,sid,'datamasker','datamasker')
            with open(logfile, 'a') as f:
                print >>f,"%s completed execution of %s" % (threadName,data)
                print >>f,result,error
        else:
            queueLock.release()
        time.sleep(1)



###################################
#
# MAIN
#
###################################

def main(argv):
    global sid
    try:
        opts, args = getopt.getopt(argv,"hd:",["sid="])
    except getopt.GetoptError:
        print ('dbscrub.py -d <database>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('dbscrub.py -d <drive>')
            sys.exit()
        elif opt in ("-d", "--database"):
            sid = arg
    if sid != '':
        scrub_database(sid)
    else:
        print ('dbscrub.py -d <database>')

if __name__ == "__main__":
    main(sys.argv[1:])
