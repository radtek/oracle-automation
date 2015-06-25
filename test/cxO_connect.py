#!/usr/bin/python
# Test script to test connectivity.
import cx_Oracle

uid="shsrinivasan"
pwd="winter2014#"

def exec_query(sid,query):
    
    service=sid
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + service)
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    print "#-records:", cursor.rowcount
    print rows[0][0]
    cursor.close()


exec_query("PODB","create role test_role")
exec_query("PODB","grant test_role to shsrinivasan")

def does_schema_exist(sid,schema):
    service=sid
    db = cx_Oracle.connect(uid + "/" + pwd + "@" + service)
    cursor = db.cursor()
    cursor.execute("select account_status, default_tablespace, temporary_tablespace from dba_users where username ='"+schema+"'")
    rows = cursor.fetchall()
    print "#-records:", cursor.rowcount
    for i in range(0, 3):
        print rows[0][i]
    cursor.close()

#does_schema_exist("podb","shsrinivasan")

#does_schema_exist("cdb1","SIMPSON")
## generated "IndexError: list index out of range"
