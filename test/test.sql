set hea on
set feedback on
set echo on

spool DP-11037-test.log
	select sysdate from dual;
	spool off
exit;
