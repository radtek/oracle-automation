import fileinput
import cx_Oracle

from sys import stdout

# These functions are destructive.  Make a copy of your file
#       and point this program to the copy.
#       Changes cannot be undone.

target_file="DP-10953-update-classroom-teacher.sql"
#######################################


def grep_destructive(target,search):
    for line in fileinput.FileInput(target,inplace=1):
        if search in line:
            print line,


def add_char_to_end(target,line_end):
    for line in fileinput.FileInput(target,inplace=1):
            print line.rstrip(),
            print line_end



def get_grants(target):
    grep_destructive(target,"GRANT")
    grep_destructive(target,"TO")
    add_char_to_end(target,";")
    

def replace_text(search, replace):
    for line in fileinput.FileInput(target_file,inplace=1):
        if search in line:
            line=line.replace(search,replace)
        print line,


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


def trim_empty_lines_newfile(target):
    with open(target+".txt", 'w') as f:
        for line in open(target):
            line = line.rstrip()
            if line!='':
                f.write(line+'\n')


def trim_empty_lines(target):
    for line in fileinput.FileInput(target,inplace=1):
        if line.rstrip():
            print line,


def add_line_to_beginning(target,new_line):
    count=0
    for line in fileinput.FileInput(target,inplace=1):
        if count == 0:
            print new_line
        print line,
        count+=1
   
replace_text('&1',"HELLO WORLD")
