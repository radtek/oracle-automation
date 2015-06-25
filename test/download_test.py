import urllib
import urllib2
import requests
import webbrowser


baseurl = "https://jira.k12.com/browse/DP-10958/"

url='https://jira.k12.com/secure/attachment/221709/'
filename='attach-test.txt'

#webbrowser.open_new_tab(url)


print "Downloading with urllib"
##urllib.urlretrieve(baseurl+"DP-10958-enable-schooltool-dropbox.sql", "DOWN1.sql")
urllib.urlretrieve(url+filename, filename)


print "downloading with urllib2"
f = urllib2.urlopen(url)
data = f.read()
with open("DOWN2.sql", "wb") as code:
    code.write(data)
 
print "downloading with requests"
r = requests.get(url)
with open("DOWN3.sql", "wb") as code:
    code.write(r.content)

#soup = BeautifulSoup(urllib2.urlopen(baseurl))
#links=soup.findAll("a")

#for link in links[5:]:
#    print link.text
#    urllib.urlretrieve(baseurl+link.text, link.text)
