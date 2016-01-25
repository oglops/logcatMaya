import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import maya.OpenMaya as mo

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QObject, pyqtSignal

import logging

sys.path.insert(0,'/home/oglop/github/logcatMaya')
# import syntax

__VERSION__ = '0.01'


# https://john.nachtimwald.com/2009/08/19/better-qplaintextedit-with-line-numbers/

'''
Text widget with support for line numbers
'''

from PyQt4.Qt import QFrame
from PyQt4.Qt import QHBoxLayout
from PyQt4.Qt import QPainter
from PyQt4.Qt import QPlainTextEdit
from PyQt4.Qt import QRect
from PyQt4.Qt import QTextEdit
from PyQt4.Qt import QTextFormat
from PyQt4.Qt import QVariant
from PyQt4.Qt import QWidget
from PyQt4.Qt import Qt


f=open('/tmp/logcat.log','a')

class LNTextEdit(QFrame):

    class NumberBar(QWidget):

        def __init__(self, edit):
            QWidget.__init__(self, edit)

            self.edit = edit
            self.adjustWidth(9999)

        def paintEvent(self, event):
            self.edit.numberbarPaint(self, event)
            QWidget.paintEvent(self, event)

        def adjustWidth(self, count):
            width = self.fontMetrics().width(unicode(count))
            if self.width() != width:
                self.setFixedWidth(width)

        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                # It would be nice to do
                # self.update(0, rect.y(), self.width(), rect.height())
                # But we can't because it will not remove the bold on the
                # current line if word wrap is enabled and a new block is
                # selected.
                self.update()

    class PlainTextEdit(QTextEdit):
        zoomed = pyqtSignal(int)
        def __init__(self, *args):
            QPlainTextEdit.__init__(self, *args)

            # self.setFrameStyle(QFrame.NoFrame)

            self.setFrameStyle(QFrame.NoFrame)
            self.highlight()
            # self.setLineWrapMode(QPlainTextEdit.NoWrap)

            self.cursorPositionChanged.connect(self.highlight)
            self._zoom = 0

        def highlight(self):
            hi_selection = QTextEdit.ExtraSelection()

            hi_selection.format.setBackground(self.palette().alternateBase())
            hi_selection.format.setProperty(
                QTextFormat.FullWidthSelection, QVariant(True))
            hi_selection.cursor = self.textCursor()
            hi_selection.cursor.clearSelection()

            self.setExtraSelections([hi_selection])

        def zoom(self, delta):
            # if it has not been zoomed before, set it to any zoom or text will become tiny
            # is this a bug?
            if self._zoom == 0:
                self.zoomIn(10)

            if delta < 0:
                self._zoom = 1
                self.zoomOut(2)
                self.zoomed.emit(-2)
            elif delta > 0:
                self._zoom = 1
                # self.setFontPointSize(62)
                self.zoomIn(2)

                # line numbers
                self.zoomed.emit(2)

        def wheelEvent(self, event):
            if (event.modifiers() & QtCore.Qt.ControlModifier):
                self.zoom(event.delta())
                self.ensureCursorVisible()
                return
            else:
                QtGui.QTextEdit.wheelEvent(self, event)

        def firstVisibleBlock(self):
            for i in range(self.document().blockCount()):
                block = self.document().findBlockByNumber(i)
                if block.isVisible():
                    return block
                    break

        def blockBoundingGeometry(self, block):
            rect = QtCore.QRect()
            if block.isValid():
                rect = block.layout().boundingRect().translated(
                    block.layout().position())
            return rect

        def contentOffset(self):

            x = self.horizontalScrollBar().value()
            y = self.verticalScrollBar().value()
            point = QtCore.QPointF(-x, -y)
            # print x,y
            # f.write('in contentOffset %s %s \n'%(x,y))
            # f.flush()
            return point

        def numberbarPaint(self, number_bar, event):
            font_metrics = self.fontMetrics()
            # edit_font = self.font()
            current_line = self.document().findBlock(
                self.textCursor().position()).blockNumber() + 1

            block = self.firstVisibleBlock()
            # block = self.document().findBlock(2)
            # block = self.document().firstBlock()
            line_count = block.blockNumber()
            painter = QPainter(number_bar)

            # baseBrush=self.palette().light()
            # baseBrush.setColor(Qt.darkGray)
            painter.fillRect(event.rect(), self.palette().light())

            # Iterate over all visible text blocks in the document.
            while block.isValid():
                line_count += 1
                block_bounding_rect = self.blockBoundingGeometry(
                    block).translated(self.contentOffset())

                block_top= block_bounding_rect.top()
                # block_top_middle=block_top + font_metrics.height()/2

                
                # f.write('line_count: %s , %s' % (line_count,block_top))
                # Check if the position of the block is out side of the visible
                # area.
                if not block.isVisible() or block_top >= event.rect().bottom():
                    break
                    # pass


                # We want the line number for the selected line to be bold.
                if line_count == current_line:
                    font = painter.font()
                    font.setBold(True)
                    # font.setPointSize(font.pointSize() * 2)
                    # painter.setFont(font)
                else:
                    font = painter.font()
                    font.setBold(False)
                    # font.setPointSize(font.pointSize() * 2)

                # print 'painter font size',font.pointSize(), '--->',font.pointSize()*2
                edit_font_size=self.font().pointSize()
                if edit_font_size>0:
                    font.setPointSize(edit_font_size)

                painter.setFont(font)


                # font.setPointSize(20)

                # Draw the line number right justified at the position of the
                # line.
                paint_rect = QRect(
                    0, block_top, number_bar.width(),  font_metrics.height()) #  edit_font.pixelSize())
                painter.drawText(
                    paint_rect, Qt.AlignRight, unicode(line_count))

                block = block.next()

            painter.end()

    def __init__(self, *args):
        QFrame.__init__(self, *args)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

        self.edit = self.PlainTextEdit()
        self.number_bar = self.NumberBar(self.edit)

        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        # self.edit.blockCountChanged.connect(self.number_bar.adjustWidth)
        # self.edit.updateRequest.connect(self.number_bar.updateContents)

        # self.edit.textChanged.connect(self.number_bar.updateContents)
        self.edit.zoomed.connect(self.update_numbar_zoom)

    def update_numbar_zoom(self,zoom):
        new_zoom = self.number_bar.font().pointSize() + zoom
        # print 'number bar font size',self.number_bar.font().pointSize(), '--->', new_zoom
        if new_zoom>0:
            self.number_bar.font().setPointSize(new_zoom) 
        # self.number_bar.font().setPixelSize(10)
        # print 'number bar font size',self.number_bar.font().pixelSize(), '--->'
        self.number_bar.update()


    def write(self, text):
        self.edit.insertPlainText(text)
        self.update()
        self.edit.ensureCursorVisible()

    def getText(self):
        return unicode(self.edit.toPlainText())

    def setText(self, text):
        self.edit.setPlainText(text)

    def isModified(self):
        return self.edit.document().isModified()

    def setModified(self, modified):
        self.edit.document().setModified(modified)

    def setLineWrapMode(self, mode):
        self.edit.setLineWrapMode(mode)


class LogTextBrowser(QTextBrowser):

    def __init__(self, parent=None):
        super(LogTextBrowser, self).__init__(parent)

    def write(self, text):
        self.insertPlainText(text)
        self.ensureCursorVisible()


class LogCat(QDialog):

    def __init__(self, parent=None):
        super(LogCat, self).__init__(parent)

        self.layout = QVBoxLayout(self)
        self.lineedit = QLineEdit(self)
        self.textedit = LNTextEdit(self)

        self.textedit.edit.setReadOnly(True)

        self.layout.addWidget(self.lineedit)
        self.layout.addWidget(self.textedit)

        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(2)
        self.resize(600, 300)
        self.setWindowTitle('LogCat v%s - Uncle Han' % __VERSION__)
        # self.setupUI()
        self.setLayout(self.layout)

        sys.stdout = self.textedit
        self.id = mo.MCommandMessage.addCommandOutputCallback(
            self.callback, None)

        # self.highlight=syntax.MelHighlighter(self.textedit.edit.document())

    def callback(self, nativeMsg, messageType, data):
        # print nativeMsg, messageType, data
        # print( 'nativeMsg: %s' % nativeMsg )
        # print( 'messageType:  %s' %  messageType)
        # print( 'data: %s' % data)
        # print nativeMsg
        # if messageType==5:
        #     nativeMsg = '// Result: %s //' % nativeMsg
        nativeMsg = nativeMsg.strip()
        if nativeMsg:
            print nativeMsg

    def closeEvent(self, event):
        try:
            mo.MCommandMessage.removeCallback(self.id)
        except:
            pass


def main():
    global win
    try:
        win.close()
    except:
        pass
    win = LogCat()
    win.show()

if __name__ == "__main__":
    main()
