#!/usr/bin/python
#
# Shankar Srinivasan 11/15/2014

import cx_Oracle
import xlwt,xlrd
import time,os,webbrowser
import fileinput

from subprocess import Popen, PIPE
from xlutils.copy import copy

from jira.client import JIRA
from getpass import getpass

######################################################

base_dir='C:\Users\\shsrinivasan\\Desktop\\Python\\'
working_dir=base_dir+time.strftime("%m-%d-%Y-deployment")

logname=time.strftime("deploy_%m-%d-%Y.xls")

uid = raw_input("Enter USERNAME: ")
print
print "DATABASE password"
pwd=getpass()
print
print "JIRA password"
jpwd=getpass()
print

ready2go=0   
completed=0


def file_contains(target,search):
    count=0
    for line in fileinput.FileInput(target):
        if search in line:
            count+=1
    return count


def file_contains_ci(target,search):
    count=0
    for line in fileinput.FileInput(target):
        if search.upper() in line.upper():
            count+=1
    return count


def trim_empty_lines(target):
    for line in fileinput.FileInput(target,inplace=1):
        if line.rstrip():
            print line,


def replace_text(target,search,replace):
    for line in fileinput.FileInput(target,inplace=1):
        if search in line:
            line=line.replace(search,replace)
        print line,


def add_line_to_beginning(target,new_line):
    count=0
    for line in fileinput.FileInput(target,inplace=1):
        if count == 0:
            print new_line
        print line,
        count+=1


def create_book():
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet1")

    sheet1.write(0, 0, "Ticket_ID")
    sheet1.write(0, 1, "Target_DB")
    sheet1.write(0, 2, "Target_Schema")
    sheet1.write(0, 3, "Script_Name")
    sheet1.write(0, 4, "Spoolfile")
    sheet1.write(0, 5, "Status")
    sheet1.write(0, 6, "Log")

    book.save(logname)
    


def jira_fetch():

    try:
        jira=JIRA(basic_auth=(uid,jpwd),options={'server': 'https://jira.client.com','headers': {'X-Atlassian-Token': 'nocheck'}})
    except:
        print "Bad JIRA Password, exiting."
        exit()
    create_book()
    my_list = jira.search_issues('(project = DP OR project = ET OR project = Configuration) AND resolution = Unresolved AND (assignee = datacenter OR assignee = dba OR assignee = noc_change_manager) AND project = DP AND assignee = noc_change_manager AND "NOC Personnel Involved" = dba ORDER BY key ASC')
    
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)
    seq_counter=0
    for i in my_list:
        seq_counter+=1
        issue=i
        print issue.key+"---"+issue.fields.summary
        w_sheet.write(seq_counter,0,issue.key)
        if issue.fields.customfield_12720!=None:
            w_sheet.write(seq_counter,1,str(issue.fields.customfield_12720))
        if issue.fields.customfield_12721!=None:
            w_sheet.write(seq_counter,2,str(issue.fields.customfield_12721))
	webbrowser.open_new_tab('https://jira.client.com/browse/'+issue.key)
        
        if not os.path.exists(issue.key):
            os.mkdir(issue.key)

    os.chdir(working_dir)
    wb.save(logname)


def jira_dl():
    jira=JIRA(basic_auth=(uid,jpwd),options={'server': 'https://jira.client.com','headers': {'X-Atlassian-Token': 'nocheck'}})

    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)

    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0
    while curr_row < num_rows:
        curr_row+=1
        ticket_no=worksheet.cell_value(curr_row, 0)
        schema=worksheet.cell_value(curr_row, 0)

        issue = jira.issue(ticket_no)
        os.chdir(working_dir+'\\'+ticket_no)
        sqls=0
        foundsql=""
        for i in issue.fields.attachment:
            if str(i).endswith('.dml') or str(i).endswith('.sql'):
                sqls+=1
                foundsql=str(i)
                if ticket_no in foundsql or ticket_no.replace('-','') in foundsql:
                    write_name=foundsql
                else:
                    write_name=ticket_no+'-'+foundsql
                with open(write_name, 'w') as f:
                    f.write(str(i.get()))

                # Cleanup DLed files and verify coding standards
                trim_empty_lines(write_name)
                spoolname=os.path.splitext(write_name)[0]+'.log'
                replace_text(write_name,'&1',spoolname)

        if sqls==1:
            w_sheet.write(curr_row,3,write_name)
        elif sqls==0:
            w_sheet.write(curr_row,6,"No .sql attachment found, please see ticket in browser.")
        else:
            w_sheet.write(curr_row,6,"Multiple sql scripts found, please see ticket in browser.")
    os.chdir(working_dir)
    wb.save(logname)

def post_to_jira():

    jira=JIRA(basic_auth=(uid,jpwd),options={'server': 'https://jira.client.com','headers': {'X-Atlassian-Token': 'nocheck'}})
    
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)

    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0
    while curr_row < num_rows:
        curr_row+=1
        issue=jira.issue(worksheet.cell_value(curr_row, 0))
        curr_status = worksheet.cell_value(curr_row, 5)
        comment = worksheet.cell_value(curr_row, 6)
        spoolfile= working_dir+"\\"+worksheet.cell_value(curr_row,0)+"\\"+worksheet.cell_value(curr_row,4)
        # print spoolfile
        if curr_status=="DEPLOYED":
            jira.add_comment(issue,comment)            
            jira.add_attachment(issue,spoolfile)
            jira.assign_issue(issue,'sqadepartment')
            w_sheet.write(curr_row,5,"COMPLETED")
            webbrowser.open_new_tab('https://jira.client.com/browse/'+issue.key)
            
    wb.save(logname)


def check_spreadsheet():
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)
    try:
        wb.save(logname)
    except IOError:
        print "CLOSE THE SPREADSHEET BEFORE CONTINUING"
        exit()

    
def exec_script(sqlCommand,sid):
    connectString=uid + "/" + pwd + "@" + sid
    session = Popen(['sqlplus', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    session.stdin.write(sqlCommand)
    return session.communicate()


def does_schema_exist(sid,schema):

    db = cx_Oracle.connect(uid + "/" + pwd + "@" + sid)
    cursor = db.cursor()
    cursor.execute("select account_status, default_tablespace, temporary_tablespace from dba_users where username ='"+schema.upper()+"'")
    rows = cursor.fetchall()
    print("#-records:", cursor.rowcount)
    try:
        for i in range(0, 3):
            print(rows[0][i])
        cursor.close()
    except IndexError:
        return False
    return True


def prereq_checks():
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)
    
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    global ready2go
    global completed
    curr_row = 0
    while curr_row < num_rows:
	curr_row += 1

	file_ext = worksheet.cell_value(curr_row, 3)
	if worksheet.cell_type(curr_row, 4) == 0:
            w_sheet.write(curr_row,4,os.path.splitext(file_ext)[0]+".log")

        # Check whether schema exists in db, and whether db exists
        curr_db = worksheet.cell_value(curr_row, 1)
        curr_schema = worksheet.cell_value(curr_row, 2)
        curr_status = worksheet.cell_value(curr_row, 5)
        if curr_status!="DEPLOYED" and curr_status!="COMPLETED" and curr_status!="ATTEMPTED":
            try:
                result=does_schema_exist(curr_db,curr_schema)
                if result:
                    w_sheet.write(curr_row,5,"OK")
                    w_sheet.write(curr_row,6,"Cleared for deployment")
                    ready2go+=1
                else:
                    w_sheet.write(curr_row,5,"ERROR")
                    w_sheet.write(curr_row,6,"Schema does not exist in target DB")

            except cx_Oracle.DatabaseError:
                w_sheet.write(curr_row,5,"ERROR")
                w_sheet.write(curr_row,6,"SID DOES NOT EXIST or bad user/pass combo")
            wb.save(logname)
        elif curr_status=="DEPLOYED":
            completed+=1


def spool_checks():
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)
    
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0
    while curr_row < num_rows:
	curr_row += 1
	curr_ticket_no=worksheet.cell_value(curr_row, 0)
        curr_status = worksheet.cell_value(curr_row, 5)
        curr_target_db = worksheet.cell_value(curr_row, 1)
        schema=worksheet.cell_value(curr_row, 2)
        curr_script = worksheet.cell_value(curr_row, 3)
        curr_logfile = worksheet.cell_value(curr_row, 4)
        os.chdir(working_dir+'\\'+curr_ticket_no)
        if file_contains_ci(curr_script,"ALTER SESSION SET CURRENT_SCHEMA"):
            print curr_script+" CONTAINS THE CURRENT_SCHEMA statement"
        else:
            add_line_to_beginning(curr_script,'ALTER SESSION SET CURRENT_SCHEMA='+schema+';')

        if not file_contains_ci(curr_script,'SPOOL'):
            add_line_to_beginning(curr_script,'SPOOL '+curr_logfile)
        else:
            print curr_script+" CONTAINS SPOOL statement"

        os.chdir(working_dir)
    
    wb.save(logname)
        

def run_deploy():
    workbook = xlrd.open_workbook(logname)
    worksheet = workbook.sheet_by_index(0)
    wb = copy(workbook)
    w_sheet = wb.get_sheet(0)
    
    num_rows = worksheet.nrows - 1
    num_cells = worksheet.ncols - 1
    curr_row = 0
    while curr_row < num_rows:
	curr_row += 1
	curr_ticket_no=worksheet.cell_value(curr_row, 0)
        curr_status = worksheet.cell_value(curr_row, 5)
        curr_target_db = worksheet.cell_value(curr_row, 1)
        curr_script = worksheet.cell_value(curr_row, 3)
        curr_logfile = worksheet.cell_value(curr_row, 4)
        if curr_status=="OK":
            print "Deploying Ticket "+curr_ticket_no
            os.chdir(working_dir+'\\'+curr_ticket_no)
            sqlCommand = '@'+curr_script.decode(encoding='UTF-8')
            queryResult, errorMessage = exec_script(sqlCommand,curr_target_db)
            print queryResult.decode(encoding='UTF-8')
            print errorMessage.decode(encoding='UTF-8')
            os.chdir(working_dir+'\\'+worksheet.cell_value(curr_row, 0))            
            # Grep the spoolfile for errors, and do not post to Jira yet
            if file_contains(curr_logfile,"ORA-"):
                w_sheet.write(curr_row,5,"DEPLOYED")
                log=curr_script+" "+time.strftime("Attempted at: %Y-%m-%d %H:%M:%S. ERRORS DETECTED IN SPOOL")
                w_sheet.write(curr_row,6,log)
            else:
                w_sheet.write(curr_row,5,"DEPLOYED")
                msg=curr_script+time.strftime(" Deployed without errors at: %Y-%m-%d %H:%M:%S. See log.")
                w_sheet.write(curr_row,6,msg)
            os.chdir(working_dir)
    
        wb.save(logname)


def main():
    global ready2go
    global completed
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    os.chdir(working_dir)

    if not os.path.exists(logname):
        jira_fetch()
        jira_dl()
        exit()

    check_spreadsheet()    
    response="CONTINUE"
    while response == "CONTINUE":

        prereq_checks()

        spool = raw_input("Enter SPOOL to check .sql files: ")
        if spool == "SPOOL":
            spool_checks()
        os.system('cls')

        print "============================================================="
        print 
        print
        print "  Ready for deployment on "+str(ready2go)+" cleared tickets."
        print "     ("+str(completed)+" already deployed)"
        print
        print "     see spreadsheet for any errors."
        print "     if you do open it, close the spreadsheet before proceeding"
        print " "
        proceed = raw_input("Enter DEPLOY to proceed: ")
        if proceed == "DEPLOY":
            run_deploy()
            print 
            print
            jirapost = raw_input("Enter POST to post successful tickets to Jira: ")
            if jirapost == "POST":
                post_to_jira()
            else:
                print 
                print "Nothing posted to Jira."
        else:
            print 
            print "Deployment aborted"
            print "No changes made."

        print " "
        response = raw_input("Enter CONTINUE to re-run checks: ")
        ready2go=0
        completed=0
            


############################
# End function definition
# Begin execution
############################

main()
