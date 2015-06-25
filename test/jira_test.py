# This script shows how to connect to a JIRA instance with a
# username and password over HTTP BASIC authentication.

from jira.client import JIRA
import webbrowser
import urllib2

jira=JIRA(basic_auth=('shsrinivasan','Sh@nk@r1028'),options={'server': 'https://jira.k12.com','headers': {'X-Atlassian-Token': 'nocheck'}})
issue = jira.issue('DP-11037')
# This is how to access field values
print issue.key
#print issue.key+"---"+str(issue.fields.customfield_12720)+"---"+str(issue.fields.customfield_12721)

#webbrowser.open('https://jira.k12.com/browse/'+issue.key)
print ""

# Simple search for issues - all issues reported by the admin
#issues = jira.search_issues('assignee=admin')


#my_list = jira.search_issues('(project = DP OR project = ET OR project = Configuration) AND resolution = Unresolved AND (assignee = datacenter OR assignee = dba OR assignee = noc_change_manager) AND project = DP AND assignee = noc_change_manager ORDER BY priority DESC')

#for i in my_list:
#    issue=i
#    print issue.key+"---"+issue.fields.summary
    #webbrowser.open('https://jira.k12.com/browse/'+issue.key)
#comment="If successful, a logfile will be uploaded, and assignee will be set to SQA Dept, and comment will be posted"
#jira.add_comment(issue,comment)

#######################################
# Attachments

# set the filename in the spreadsheet 
print issue.fields.attachment
sqls=0
for i in issue.fields.attachment:
    print i
    print i.get()
    if str(i).endswith('.txt'):
        sqls+=1
if sqls==1:
    print "1 found"
else:
    print "Not 1 found"
###################3

jira.add_attachment(issue,"C:\\Users\\shsrinivasan\\Desktop\\Micore\\Python\\test\\testERR.sql")

#jira.assign_issue(issue,'noc_change_manager')
#print issue.fields.assignee



#noc_change_manager
#sqadepartment

# Pertinent data fields:
#   ticket number       i.key
#   description         i.fields.summary
#   assignee            i.fields.assignee
#   str(issue.fields.status)
#jira.add_comment(issue,'Deployed to production, please see attached .log file')
#jira.add_comment(issue,'Run with errors, please see attached .log file')
