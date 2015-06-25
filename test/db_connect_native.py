from subprocess import Popen, PIPE

#function that takes the sqlCommand and connectString and retuns the output and #error string (if any)

connectString = 'shsrinivasan/winter2014#@podb'

def runSqlQuery(sqlCommand,connectString):
    session = Popen(['sqlplus', '-S', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    session.stdin.write(sqlCommand)
    return session.communicate()


#example 1: run a query that returns one record
sqlCommand = b'select sysdate from dual;'
queryResult, errorMessage = runSqlQuery(sqlCommand, connectString)
print queryResult

#example 2: run a query that returns a next value of sequence
sqlCommand = b'@test.sql'
queryResult, errorMessage = runSqlQuery(sqlCommand, connectString)
print queryResult.decode(encoding='UTF-8')
