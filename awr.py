######################################################
import decimal

import os
import sys
import getopt
import cx_Oracle
#import paramiko
#import py2exe

import time,os

from subprocess import Popen, PIPE

from getpass import getpass




######################################################

base_dir='C:\Python27'
port = 1521
nbytes = 4096
Result=''
Message=''
str1=''
hostname = '192.168.56.101'
global start_time

new_array = [100]


#######################################################

def id_tablespace_obtain():
        global sid
        global tablespace
        sid = raw_input("Enter SID: ")
        print
        #empty_string = snap_id(sid)
        string123 = ''
        print
        #test_spool(sid,string123)
##########################################################################


def exec_script(sqlCommand,sid):
        os.environ['ORACLE_SID'] = sid
        session = Popen(['sqlplus', '-s', '/','as','sysdba'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        session.stdin.write(sqlCommand)
        return session.communicate()




###########################################################################







###########################################################################




###########################################################################

###########################################################################
def test_spool(sid,some_string,start_time,end_time):
        naming_convention = sid + '_' + some_string + '.html'
        print naming_convention
        start_date = '5-21-2015'
        #print "Please enter a start time for the awr snapshots: "
        #print "It should be in military time format for example hh:mm 12:00, or 24:00: "
        #target_time = raw_input()
        #print "Please enter an end time for the awr snapshots: "
        #print "It should be in military time format for example hh:mm 12:00, or 24:00: "
        #end_time = raw_input()
        test_spool_file = 'test1.html'
        Result, Message = exec_script('''
spool /home/oracle/python/{old}
set hea off
set feedback off
set linesize  1000
SELECT output FROM TABLE (dbms_workload_repository.awr_report_html((select dbid from v$database),(select instance_number from v$instance),(select SNAP_ID from dba_hist_snapshot where trunc(END_INTERVAL_TIME,'MI')=to_date('{olc} {olt}','MM-DD-YYYY HH24:MI')),(select snap_id from dba_hist_snapshot where trunc(END_INTERVAL_TIME,'MI')=to_date('{olc} {ole}','MM-DD-YYYY HH24:MI'))));
spool off'''.format(old=naming_convention,olc=some_string,olt=start_time,ole=end_time),sid)
        print Result
        print
        print '--------------'
        print "PRESS ENTER TO CONTINUE"
        print some_string
        raw_input()
###########################################################################


def snap_id(sid):
        db = cx_Oracle.connect(mode = cx_Oracle.SYSDBA)
        cursor = db.cursor()
        cursor.execute('''select  to_char(begin_interval_time, 'mm-dd-yyyy') begin from dba_hist_snapshot order by 1''')
        rows = cursor.fetchall()
        print "Please enter a start time for the awr snapshots: "
        target_time = raw_input()
        print "Please enter an end time for the awr snapshots: "
        end_time = raw_input()
        first_date = rows[0]
        first_date = str(first_date)
        first_date = trim_date(first_date)
        last_date = rows[cursor.rowcount-1]
        last_date = str(last_date)
        last_date = trim_date(last_date)
        #try:
        #       test_spool(sid,first_date)
        #except:
        #       e = sys.exec_info()[0]
        #       write_to_page( "<p>Error: %</p>" % e)
        foo = rows[0]
        pervious = None
        next = None
        for x, obj in enumerate(rows):
                if obj == foo:
                        try:
                                pervious = rows[x-1]
                                next = rows[x+1]
                        except IndexError:
                                print ''
                else:
                        try:
                                second_date = rows[x]
                                second_date = str(second_date)
                                second_date = trim_date(second_date)
                                print second_date
                                test_spool(sid,second_date,target_time,end_time)
                        except Exception:
                                pass
                                continue
                        finally:
                                foo = rows[x]
#####################################################


def trim_date(string):
        string = string[1:]
        string = string[1:]
        string = string[:-1]
        string = string[:-1]
        string = string[:-1]
        return string
########        ###########################
#
# MAIN

#

###################################





def main():

        #id_tablespace_obtain()
        snap_id('db11g')

main()
