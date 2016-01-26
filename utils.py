
import constants


def get_commands(web=False, version=2015):
    if web:

        import requests

        from bs4 import BeautifulSoup

        url = 'http://help.autodesk.com/cloudhelp/2015/ENU/Maya-Tech-Docs/CommandsPython/index_all.html'
        r = requests.get(url)

        soup = BeautifulSoup(r.text, 'html.parser')
        commands = []
        for a in soup.select("td a"):
            commands.append(a.text)

    else:
        commands = constants.maya_commands[version]

    return commands


def get_maya_version():
    version = 2015
    try:
        import maya.cmds as mc
        version = int(mc.about(v=1))
    except:
        pass
    return version

def highlight_script_editor_output():
	import syntax
	syntax.highlightCmdReporter()