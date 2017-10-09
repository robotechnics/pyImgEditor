"""
This File is part of bLUe software.

Copyright (C) 2017  Bernard Virot <bernard.virot@libertysurf.fr>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Lesser Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


from PySide2.QtCore import Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QGraphicsView, QSizePolicy, QVBoxLayout, QSlider, QLabel, QHBoxLayout

from graphicsTemp import sRGBWP
from utils import optionsWidget


class histForm (QGraphicsView):
    @classmethod
    def getNewWindow(cls, targetImage=None, size=500, layer=None, parent=None, mainForm=None):
        wdgt = histForm(targetImage=targetImage, size=size, layer=layer, parent=parent, mainForm=mainForm)
        wdgt.setWindowTitle(layer.name)
        return wdgt

    def __init__(self, targetImage=None, size=200, layer=None, parent=None, mainForm=None):
        super(histForm, self).__init__(parent=parent)
        self.targetImage = targetImage
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(size, 100)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.img = targetImage
        self.layer = layer
        l = QVBoxLayout()
        l.setAlignment(Qt.AlignBottom)
        l.setSpacing(0)
        self.Label_Hist = QLabel()
        l.addWidget(self.Label_Hist)

        # options
        options1 = ['Original Image']
        self.listWidget1 = optionsWidget(options=options1, exclusive=False)
        self.listWidget1.setStyleSheet("background-color: gray; selection-background-color: gray; border: 0px; font-size: 9px")
        #self.listWidget1.select(self.listWidget1.items['Original Image'])
        self.listWidget1.setMaximumSize(self.listWidget1.sizeHintForColumn(0) + 5, self.listWidget1.sizeHintForRow(0) * len(options1))

        options2 = ['Color Chans']
        self.listWidget2 = optionsWidget(options=options2, exclusive=False)
        self.listWidget2.setStyleSheet("background-color: gray; selection-background-color: gray; border: 0px; font-size: 9px")
        #self.listWidget2.select(self.listWidget2.items['Color Chans'])
        self.listWidget2.setMaximumSize(self.listWidget2.sizeHintForColumn(0) + 5, self.listWidget2.sizeHintForRow(0) * len(options2))

        self.options = { option : True for option in options1 + options2}
        def onSelect1(item):
            self.options[options1[0]] = item.checkState() is Qt.Checked #item is self.listWidget1.items['Original Image']
            self.targetImage.onImageChanged()
            self.Label_Hist.update()

        def onSelect2(item):
            self.options[options2[0]] = item.checkState() is Qt.Checked #item is self.listWidget1.items['Original Image']
            self.targetImage.onImageChanged()
            self.Label_Hist.update()

        self.listWidget1.onSelect = onSelect1
        self.listWidget2.onSelect = onSelect2

        h = QHBoxLayout()
        h.addWidget(self.listWidget1)
        h.addWidget(self.listWidget2)
        l.addLayout(h)
        l.addStretch(1)

        l.setContentsMargins(0, 0, 0, 0)  # left, top, right, bottom
        self.setLayout(l)



