

import requests

from bs4 import BeautifulSoup


url = 'http://help.autodesk.com/cloudhelp/2015/ENU/Maya-Tech-Docs/CommandsPython/index_all.html'

def get_commands():
	r = requests.get(url)

	soup = BeautifulSoup(r.text, 'html.parser')
	commands=[]
	for a in soup.select("td a"):
		commands.append(a.text)

	return commands


print get_commands()