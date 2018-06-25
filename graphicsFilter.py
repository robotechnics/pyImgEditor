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
from PySide2 import QtCore

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QSizePolicy, QVBoxLayout, QSlider, QLabel, QHBoxLayout, QWidget
from PySide2.QtGui import QFontMetrics

from kernel import filterIndex, getKernel
from utils import optionsWidget


class filterForm (QWidget): # (QGraphicsView): TODO modified 25/06/18 validate
    dataChanged = QtCore.Signal()
    @classmethod
    def getNewWindow(cls, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        wdgt = filterForm(targetImage=targetImage, axeSize=axeSize, layer=layer, parent=parent, mainForm=mainForm)
        wdgt.setWindowTitle(layer.name)
        return wdgt

    def __init__(self, targetImage=None, axeSize=500, layer=None, parent=None, mainForm=None):
        super().__init__(parent=parent)
        defaultRadius = 10
        defaultTone = 100.0
        defaultAmount = 50.0
        self.radius = defaultRadius
        self.tone = defaultTone
        self.amount = defaultAmount
        self.targetImage = targetImage
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(axeSize, axeSize)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.img = targetImage
        self.layer = layer
        self.mainForm = mainForm
        self.kernelCategory = filterIndex.UNSHARP
        self.kernel = getKernel(self.kernelCategory)

        l = QVBoxLayout()
        l.setAlignment(Qt.AlignBottom)

        # options
        optionList = ['Unsharp Mask', 'Sharpen', 'Gaussian Blur', 'Surface Blur']
        filters = [ filterIndex.UNSHARP, filterIndex.SHARPEN, filterIndex.BLUR1, filterIndex.SURFACEBLUR]
        filterDict = dict(zip(optionList, filters))

        self.listWidget1 = optionsWidget(options=optionList, exclusive=True, changed=self.dataChanged)
        # set initial selection to unsharp mask
        item = self.listWidget1.checkOption(optionList[0])

        # sliders
        self.sliderRadius = QSlider(Qt.Horizontal)
        self.sliderRadius.setTickPosition(QSlider.TicksBelow)
        self.sliderRadius.setRange(1, 50)
        self.sliderRadius.setSingleStep(1)
        radiusLabel = QLabel()
        radiusLabel.setMaximumSize(150, 30)
        radiusLabel.setText("Radius")

        self.radiusValue = QLabel()
        font = self.radiusValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("1000 ")
        h = metrics.height()
        self.radiusValue.setMinimumSize(w, h)
        self.radiusValue.setMaximumSize(w, h)
        #self.radiusValue.setStyleSheet("QLabel {background-color: gray;}")

        self.sliderAmount = QSlider(Qt.Horizontal)
        self.sliderAmount.setTickPosition(QSlider.TicksBelow)
        self.sliderAmount.setRange(0, 100)
        self.sliderAmount.setSingleStep(1)
        amountLabel = QLabel()
        amountLabel.setMaximumSize(150, 30)
        amountLabel.setText("Amount")
        self.amountValue = QLabel()
        font = self.radiusValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("1000 ")
        h = metrics.height()
        self.amountValue.setMinimumSize(w, h)
        self.amountValue.setMaximumSize(w, h)
        #self.amountValue.setStyleSheet("QLabel {background-color: gray;}")

        self.toneValue = QLabel()
        toneLabel = QLabel()
        toneLabel.setMaximumSize(150, 30)
        toneLabel.setText("Tone")
        self.sliderTone = QSlider(Qt.Horizontal)
        self.sliderTone.setTickPosition(QSlider.TicksBelow)
        self.sliderTone.setRange(0, 100)
        self.sliderTone.setSingleStep(1)
        font = self.radiusValue.font()
        metrics = QFontMetrics(font)
        w = metrics.width("1000 ")
        h = metrics.height()
        self.toneValue.setMinimumSize(w, h)
        self.toneValue.setMaximumSize(w, h)
        #self.toneValue.setStyleSheet("QLabel {background-color: white;}")

        l.addWidget(self.listWidget1)
        hl = QHBoxLayout()
        hl.addWidget(radiusLabel)
        hl.addWidget(self.radiusValue)
        hl.addWidget(self.sliderRadius)
        l.addLayout(hl)

        hl = QHBoxLayout()
        hl.addWidget(amountLabel)
        hl.addWidget(self.amountValue)
        hl.addWidget(self.sliderAmount)
        l.addLayout(hl)

        hl = QHBoxLayout()
        hl.addWidget(toneLabel)
        hl.addWidget(self.toneValue)
        hl.addWidget(self.sliderTone)
        l.addLayout(hl)

        l.setContentsMargins(20, 0, 20, 25)  # left, top, right, bottom

        self.setLayout(l)

        # value changed event handler
        def sliderUpdate():
            self.radiusValue.setText(str('%d ' % self.sliderRadius.value()))
            self.amountValue.setText(str('%d ' % self.sliderAmount.value()))
            self.toneValue.setText(str('%d ' % self.sliderTone.value()))
        # value done event handler
        def formUpdate():
            sR, sA, sT = self.sliderRadius.isEnabled(), self.sliderAmount.isEnabled(), self.sliderTone.isEnabled()
            self.sliderRadius.setEnabled(False)
            self.sliderAmount.setEnabled(False)
            self.sliderTone.setEnabled(False)
            self.kernel = getKernel(self.kernelCategory, self.sliderRadius.value(), self.sliderAmount.value())
            self.tone = self.sliderTone.value()
            self.radius = self.sliderRadius.value()
            self.amount = self.sliderAmount.value()
            sliderUpdate()
            # self.onUpdateFilter(self.kernelCategory, self.sliderRadius.value(), self.sliderAmount.value())
            self.dataChanged.emit()
            self.sliderRadius.setEnabled(sR)
            self.sliderAmount.setEnabled(sA)
            self.sliderTone.setEnabled(sT)

        self.sliderRadius.valueChanged.connect(sliderUpdate)
        self.sliderRadius.sliderReleased.connect(formUpdate)
        self.sliderAmount.valueChanged.connect(sliderUpdate)
        self.sliderAmount.sliderReleased.connect(formUpdate)
        self.sliderTone.valueChanged.connect(sliderUpdate)
        self.sliderTone.sliderReleased.connect(formUpdate)

        def enableSliders():
            op = self.listWidget1.options
            useRadius = op[optionList[0]] or op[optionList[2]] or op[optionList[3]]
            useAmount = op[optionList[0]] or op[optionList[2]]
            useTone = op[optionList[3]]
            self.sliderRadius.setEnabled(useRadius)
            self.sliderAmount.setEnabled(useAmount)
            self.sliderTone.setEnabled(useTone)
            self.radiusValue.setEnabled(self.sliderRadius.isEnabled())
            self.amountValue.setEnabled(self.sliderAmount.isEnabled())
            self.toneValue.setEnabled(self.sliderTone.isEnabled())
            radiusLabel.setEnabled(self.sliderRadius.isEnabled())
            amountLabel.setEnabled(self.sliderAmount.isEnabled())
            toneLabel.setEnabled(self.sliderTone.isEnabled())

        # data changed event handler
        def updateLayer():
            enableSliders()
            for key in self.listWidget1.options:
                if self.listWidget1.options[key]:
                    self.kernelCategory = filterDict[key]
                    break
            self.layer.applyToStack()
            self.layer.parentImage.onImageChanged()

        self.dataChanged.connect(updateLayer)
        # init
        self.sliderRadius.setValue(defaultRadius)
        self.sliderAmount.setValue(defaultAmount)
        self.sliderTone.setValue(defaultTone)
        enableSliders()
        sliderUpdate()

    def writeToStream(self, outStream):
        layer = self.layer
        outStream.writeQString(layer.actionName)
        outStream.writeQString(layer.name)
        outStream.writeQString(self.listWidget1.selectedItems()[0].text())
        outStream.writeFloat32(self.sliderRadius.value())
        outStream.writeFloat32(self.sliderAmount.value())
        return outStream

    def readFromStream(self, inStream):
        actionName = inStream.readQString()
        name = inStream.readQString()
        sel = inStream.readQString()
        radius = inStream.readFloat32()
        amount = inStream.readFloat32()
        for r in range(self.listWidget1.count()):
            currentItem = self.listWidget1.item(r)
            if currentItem.text() == sel:
                self.listWidget.select(currentItem)
        self.sliderRadius.setValue(radius)
        self.sliderAmount.setValue(amount)
        self.repaint()
        return inStream

