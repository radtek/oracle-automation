import time, os

#Set the filename and open the file
working_dir='C:\\Users\\User\\Desktop\\Python\\Oracle utils\\'
alert_log = 'test.txt'

def mon_alert_log(filename):
    file = open(filename,'r')
    #Find the size of the file and move to the end
    st_results = os.stat(filename)
    st_size = st_results[6]
    file.seek(st_size)

    while 1:
        where = file.tell()
        line = file.readline()
        if not line:
            time.sleep(1)
            file.seek(where)
        else:
            print line,
            if "ORA-" in line:
                os.system('cls')
                print time.strftime("%m-%d-%Y %H:%M:%S : ORA- ERRORS DETECTED IN LOG!!!")



mon_alert_log(working_dir+alert_log)
