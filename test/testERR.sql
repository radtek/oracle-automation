set hea on
set feedback on
set echo on

spool DP-11037-test.log
	select name, open_mode, DUMMY_COLUMN from v$database;
	spool off
exit;
