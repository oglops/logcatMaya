# -*- coding: UTF-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2014-2015 Mack Stone
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# How to use it
# open script editor and run
#
# import cmdReporterHighlighter as crHighlighter
# crHighlighter.highlightCmdReporter()
#
# using userSetup.py
# added follow line to your userSetup.py
#
# from maya import utils
# import cmdReporterHighlighter as crHighlighter
# utils.executeDeferred(crHighlighter.launchFromCmdWndIcon)

import sys
import os
import re
import keyword

try:
    from maya import (cmds, mel)
    from maya import OpenMayaUI as omui
except:
    pass

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt4 import QtGui, QtCore
import re
import keyword


import utils
reload(utils)


def launchFromCmdWndIcon():
    '''launch from maya command line script editor icon.'''
    def cmdWnd(arg=None):
        cmds.ScriptEditor()
        highlightCmdReporter()

    # get command line formLayout
    gCommandLineForm = mel.eval('$tempVar = $gCommandLineForm')
    commandLineForm = cmds.formLayout(gCommandLineForm, q=1, ca=1)[0]
    # get cmdWndIcon button
    cmdWndIcon = cmds.formLayout(commandLineForm, q=1, ca=1)[-1]
    # change the command of the button
    cmds.symbolButton(cmdWndIcon, e=1, c=cmdWnd)

    # change the main manu item command
    #menuName = 'wmScriptEditor'
    #if cmds.menuItem(menuName, q=1, ex=1):
        #cmds.menuItem(menuName, e=1, c=cmdWnd)

def getMayaWindowWidget():
    '''get maya window widget for Qt'''
    mwin = None
    try:
        from shiboken import wrapInstance
        mwinPtr = omui.MQtUtil.mainWindow()
        mwin = wrapInstance(long(mwinPtr), QtGui.QMainWindow)
    except:
        mapp = QtGui.QApplication.instance()
        for widget in mapp.topLevelWidgets():
            if widget.objectName() == 'MayaWindow':
                mwin = widget
                break
    return mwin

def highlightCmdReporter():
    '''find cmdScrollFieldReporter and highlight it'''
    mwin = getMayaWindowWidget()
    cmdReporters = cmds.lsUI(type='cmdScrollFieldReporter')
    if not cmdReporters: return
    # only setup for the first one
    cmdReporter = mwin.findChild(QtGui.QTextEdit, cmdReporters[0])
    highlighter = Highlighter(parent=mwin)
    highlighter.setDocument(cmdReporter.document())



class Highlighter(QtGui.QSyntaxHighlighter):
    """syntax highlighter"""

    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        self.__rules = []

        # numeric color
        self._numericFormat = QtGui.QTextCharFormat()
        self._numericFormat.setForeground(QtGui.QColor('#9ACD32'))

        # mel command options started with -
        melOpsFormat = QtGui.QTextCharFormat()
        melOpsFormat.setForeground(QtGui.QColor('#B8860B'))
        self.__rules.append((re.compile('-[a-zA-Z]+\\b'), melOpsFormat))

        # keywords color
        self._keywordColor = QtGui.QColor(0, 128, 255)

        self._numeric()
        self._keywordFormat()
        self._cmdsFunctionFormat()

        # maya api format
        mapiFormat = QtGui.QTextCharFormat()
        mapiFormat.setForeground(self._keywordColor)
        self.__rules.append((re.compile('\\bM\\w+\\b'), mapiFormat))
        # Qt
        self.__rules.append((re.compile('\\bQ\\w+\\b'), mapiFormat))

        # quotation
        self._quotationFormat = QtGui.QTextCharFormat()
        self._quotationFormat.setForeground(QtCore.Qt.green)
        # self._quotationFormat.setForeground(QtGui.QColor('seagreen'))


        # quote: ""
        self.__rules.append((re.compile('"[^\"]*"'), self._quotationFormat))
        # single quotes for python: ''
        self.__rules.append((re.compile("'.*'"), self._quotationFormat))

        # sing line comment
        self._commentFormat = QtGui.QTextCharFormat()
        # orange red
        self._commentFormat.setForeground(QtGui.QColor(255, 128, 64))

        # // mel comment
        self.__rules.append((re.compile('//[^\n]*'), self._commentFormat))
        # # python comment
        self.__rules.append((re.compile('#[^\n]*'), self._commentFormat))

        # function and class format
        funcFormat = QtGui.QTextCharFormat()
        funcFormat.setFontWeight(QtGui.QFont.Bold)
        self.__rules.append((re.compile('\\b(\\w+)\(.*\):'), funcFormat))

        # mel warning
        warningFormat = QtGui.QTextCharFormat()
        warningFormat.setForeground(QtGui.QColor('#FF9ACD32'))
        warningFormat.setBackground(QtCore.Qt.yellow)
        warningFormat.setFontWeight(QtGui.QFont.Bold)
        self.__rules.append((re.compile('// Warning:[^\n]*//'), warningFormat))

        # mel error
        errorFormat = QtGui.QTextCharFormat()
        errorFormat.setForeground(QtGui.QColor('#FF9ACD32'))
        errorFormat.setBackground(QtCore.Qt.red)
        errorFormat.setFontWeight(QtGui.QFont.Bold)
        self.__rules.append((re.compile('// Error:[^\n]*//'), errorFormat))

        # Quotes
        self._singleQuotes = QtCore.QRegExp("'''")
        self._doubleQuotes = QtCore.QRegExp('"""')

        # mel multi-line comment: /*  */
        self._melMLComStart = re.compile('/\\*')
        self._melMLComEnd = re.compile('\\*/')

    def _numeric(self):
        '''set up numeric format'''
        num_01 = re.compile('\\b[+-]?[0-9]+[lL]?\\b')
        num_02 = re.compile('\\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\\b')
        num_03 = re.compile('\\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\\b')
        num_regs = (num_01, num_02, num_03)
        for nr in num_regs:
            self.__rules.append((nr, self._numericFormat))

    def _keywordFormat(self):
        '''set up keyword format'''
        # mel keyword
        melKeywords = ['false', 'float', 'int', 'matrix', 'off', 'on', 'string',
                       'true', 'vector', 'yes', 'alias', 'case', 'catch', 'break',
                       'case', 'continue', 'default', 'do', 'else', 'for', 'if', 'in',
                       'while', 'alias', 'case', 'catch', 'global', 'proc', 'return', 'source', 'switch']
        # python keyword
        pyKeywords = keyword.kwlist + ['False', 'True', 'None']

        keywords = {}.fromkeys(melKeywords)
        keywords.update({}.fromkeys(pyKeywords))
        # keyword format
        keywordFormat = QtGui.QTextCharFormat()
        keywordFormat.setForeground(self._keywordColor)
        keywordFormat.setFontWeight(QtGui.QFont.Bold)
        kwtext = '\\b(' + "|".join(keywords) + ')\\b'
        self.__rules.append((re.compile(kwtext), keywordFormat))

    def _cmdsFunctionFormat(self):
        '''set up maya.cmds functions'''
        # mayaBinDir = os.path.dirname(sys.executable)
        # cmdsList = os.path.join(mayaBinDir, 'commandList')

        functions = '\\b('
        # with open(cmdsList) as phile:
        #     for line in phile:
        #         functions += line.split(' ')[0] + '|'

        maya_ver=utils.get_maya_version()
        maya_commands = utils.get_commands(version=maya_ver)
        for c in maya_commands:
            functions += c + '|'




        # global MEL procedures
        try:
            melProcedures = cmds.melInfo()
            maxlen = 1400
            stop = len(melProcedures) / maxlen
            melProc = []
            melProc.append('\\b(' + '|'.join(melProcedures[:maxlen]) + ')\\b')
            for i in range(1, stop - 1):
                start = maxlen * i
                end = maxlen * (i + 1)
                melProc.append('\\b(' + '|'.join(melProcedures[start:end]) + ')\\b')
            melProc.append('\\b(' + '|'.join(melProcedures[maxlen*stop:]) + ')\\b')
        except:
            pass

        # TODO: should update it when a plug-in was load.
        try:
            # function from plug-ins
            plugins = cmds.pluginInfo(q=1, listPlugins=1)
            for plugin in plugins:
                funcFromPlugin = cmds.pluginInfo(plugin, q=1, command=1)
                if funcFromPlugin:
                    functions += '|'.join(funcFromPlugin)
        except:
            pass

        functions = functions[:-1] + ')\\b'

        # function format
        funcFormat = QtGui.QTextCharFormat()
        funcFormat.setForeground(self._keywordColor)
        self.__rules.append((re.compile(functions), funcFormat))
        try:
            for mp in melProc:
                self.__rules.append((re.compile(mp), funcFormat))
        except:
            pass

    def _melMLCommentFormat(self, text):
        '''set up mel multi-line comment: /*  */'''
        startIndex = 0
        commentLen = 0
        self.setCurrentBlockState(0)
        if self.previousBlockState() != 1:
            searchStart = self._melMLComStart.search(text)
            if searchStart:
                startIndex = searchStart.start()
                searchEnd = self._melMLComEnd.search(text)
                if searchEnd:
                    commentLen = searchEnd.end() - startIndex
                else:
                    self.setCurrentBlockState(1)
                    commentLen = len(text) - startIndex
        else:
            searchEnd = self._melMLComEnd.search(text)
            if searchEnd:
                commentLen = searchEnd.end()
            else:
                self.setCurrentBlockState(1)
                commentLen = len(text)
        if commentLen > 0:
            self.setFormat(startIndex, commentLen, self._commentFormat)

    def quotesFormat(self, text, regExp, state):
        '''set up single or double quotes strings format'''
        if self.previousBlockState() == state:
            startIndex = 0
            add = 0
        else:
            startIndex = regExp.indexIn(text)
            add = regExp.matchedLength()

        while startIndex >= 0:
            end = regExp.indexIn(text, startIndex + add)
            if end >= add:
                quotesLen = end - startIndex + regExp.matchedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(state)
                quotesLen = len(text) - startIndex + add
            self.setFormat(startIndex, quotesLen, self._quotationFormat)
            startIndex = regExp.indexIn(text, startIndex + quotesLen)

        if self.currentBlockState() == state:
            return True
        else:
            return False

    def highlightBlock(self, text):
        '''highlight text'''
        for regExp, tformat in self.__rules:
            match = regExp.search(text)
            while match:
                self.setFormat(match.start(), match.end() - match.start(), tformat)
                match = regExp.search(text, match.end())

        # blocks
        self._melMLCommentFormat(text)
        quotesState = self.quotesFormat(text, self._singleQuotes, 2)
        if not quotesState:
            self.quotesFormat(text, self._doubleQuotes, 3)


# syntax.py
# https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)

    # _format.setBackground(QColor(124,124,124))
    # _format.setBackground(QtCore.Qt.gray)

    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
# https://www.w3.org/TR/SVG/types.html#ColorKeywords
STYLES = {
    'keyword': format('lime'),
    'command': format('blue'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('yellow'),
    'string2': format('darkMagenta'),
    'comment': format('red', 'italic'),
    # 'self': format('black', 'italic'),
    'numbers': format('gainsboro'),
}


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b',
             0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = expression.cap(nth).length()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = text.length() - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class MelHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords from 2015
    keywords = ['false', 'exists', 'int', 'float', 'warning', 'in', 'yes', 'if', 'matrix', 'for', 'switch', 'source',
                'vector', 'proc', 'do', 'global', 'return', 'string', 'trace', 'else', 'break', 'catch', 'true', 'case',
                'on', 'off', 'objExists', 'default', 'attributeExists', 'alias', 'while', 'continue', 'error']

    # add maya commands as keywords
    maya_ver=utils.get_maya_version()
    maya_commands = utils.get_commands(version=maya_ver)

    pyKeywords = keyword.kwlist + ['False', 'True', 'None']
    # keywords+=maya_commands

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '\%',  # '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        # '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        # self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        # self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in MelHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in MelHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in MelHighlighter.braces]

        rules += [(r'%s' % b, 0, STYLES['keyword'])
                  for b in MelHighlighter.pyKeywords]

        rules += [(r'%s' % "|".join(MelHighlighter.pyKeywords), 0, STYLES['keyword'])
                   ]

        # All other rules
        rules += [
            # 'self'
            # (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),

            # Single-quoted string, possibly containing escape sequences
            # (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'proc' followed by an identifier
            # (r'\bproc\b\s*(\w+)', 1, STYLES['defclass']),
            # 'global proc' followed by an identifier
            # (r'\bglobal proc\b\s*(\w+)', 1, STYLES['defclass']),



            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b',
             0, STYLES['numbers']),


            # From '//' until a newline
            (r'//[^\n]*', 0, STYLES['comment']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]


        # Quotes
        self._singleQuotes = QtCore.QRegExp("'''")
        self._doubleQuotes = QtCore.QRegExp('"""')

        # mel multi-line comment: /*  */
        self._melMLComStart = re.compile('/\\*')
        self._melMLComEnd = re.compile('\\*/')

    def _melMLCommentFormat(self, text):
        '''set up mel multi-line comment: /*  */'''
        startIndex = 0
        commentLen = 0
        self.setCurrentBlockState(0)
        if self.previousBlockState() != 1:
            searchStart = self._melMLComStart.search(text)
            if searchStart:
                startIndex = searchStart.start()
                searchEnd = self._melMLComEnd.search(text)
                if searchEnd:
                    commentLen = searchEnd.end() - startIndex
                else:
                    self.setCurrentBlockState(1)
                    commentLen = len(text) - startIndex
        else:
            searchEnd = self._melMLComEnd.search(text)
            if searchEnd:
                commentLen = searchEnd.end()
            else:
                self.setCurrentBlockState(1)
                commentLen = len(text)
        if commentLen > 0:
            # self.setFormat(startIndex, commentLen, self._commentFormat)
            self.setFormat(startIndex, commentLen, STYLES['comment'])


    def quotesFormat(self, text, regExp, state):
        '''set up single or double quotes strings format'''
        if self.previousBlockState() == state:
            startIndex = 0
            add = 0
        else:
            startIndex = regExp.indexIn(text)
            add = regExp.matchedLength()

        while startIndex >= 0:
            end = regExp.indexIn(text, startIndex + add)
            if end >= add:
                quotesLen = end - startIndex + regExp.matchedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(state)
                quotesLen = len(text) - startIndex + add
            # self.setFormat(startIndex, quotesLen, self._quotationFormat)
            self.setFormat(startIndex, quotesLen, STYLES['comment'])

            startIndex = regExp.indexIn(text, startIndex + quotesLen)

        if self.currentBlockState() == state:
            return True
        else:
            return False

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = expression.cap(nth).length()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # # Do multi-line strings
        # in_multiline = self.match_multiline(text, *self.tri_single)
        # if not in_multiline:
        #     in_multiline = self.match_multiline(text, *self.tri_double)

        # blocks
        self._melMLCommentFormat(text)
        quotesState = self.quotesFormat(text, self._singleQuotes, 2)
        if not quotesState:
            self.quotesFormat(text, self._doubleQuotes, 3)



def main():
    # editor.py

    from PyQt4 import QtGui
    import syntax

    app = QtGui.QApplication([])
    editor = QtGui.QPlainTextEdit()

    # default text and bg color
    p = editor.palette()
    p.setColor(QtGui.QPalette.Base, QColor(42, 42, 42))
    # p.setColor(QtGui.QPalette.Text, QColor(255, 255, 255))
    p.setColor(QtGui.QPalette.Text, QColor('gainsboro'))
    editor.setPalette(p)

    # highlight = syntax.PythonHighlighter(editor.document())
    # highlight = syntax.MelHighlighter(editor.document())
    highlight = Highlighter(editor.document())
    editor.show()
    editor.resize(1200, 840)

    # Load syntax.py into the editor for demo purposes
    # infile = open('syntax.py', 'r')
    infile = open('/home/oglop/github/logcatMaya/addPassiveToNSystem.mel', 'r')
    editor.setPlainText(infile.read())

    app.exec_()


if __name__ == '__main__':
    main()
