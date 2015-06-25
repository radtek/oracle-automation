import oracle_utils as utils

sqlCommand="select sysdate from dual"

utils.exec_command("POLS",sqlCommand+";")
utils.cx_query("POLS",sqlCommand)
