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


from PySide.QtCore import Qt

import cv2
from copy import copy
from PySide.QtGui import QPixmap, QImage, QColor, QPainter, QMessageBox
from PySide.QtCore import QRect
from icc import convertQImage
from imgconvert import *
from LUT3D import interpVec
from time import time
import icc
from utils import savitzky_golay, Channel

class ColorSpace:
    notSpecified = -1; sRGB = 1

class metadata:
    """
    Container for vImage meta data
    """
    def __init__(self, name=''):
        self.name, self.colorSpace, self.rawMetadata, self.profile, self.orientation = name, ColorSpace.notSpecified, [], '', None

class vImage(QImage):
    """
    versatile image class.
    This is the base class for all multi-layered and interactive image classes.
    It gathers all image information, including meta-data.
    Each image owns a mask (disabled by default). When enabled, masking operation is bitwise AND.
    """
    def __init__(self, filename=None, cv2Img=None, QImg=None, mask=None, format=QImage.Format_ARGB32,
                                            name='', colorSpace=-1, orientation=None, meta=None, rawMetadata=[], profile=''):
        """
        With no parameter, builds a null image.
        Mask is disabled by default.
        :param filename:
        :param cv2Img:
        :param QImg:
        :param mask: Image mask (type QImage); Should have format and dims identical to those of image
        :param format: QImage format (default QImage.Format_ARGB32)
        :param name:
        :param colorSpace: type ColorSpace (default notSpecified)
        :param orientation: Qtransform object (default None)
        :param meta: metadata object (default None)
        :param rawMetadata: list of dictionaries (default [])
        :param profile: embedded profile (default '')
        """
        self.colorTransformation = None
        self.isModified = False
        self.onModify = lambda : 0
        self.rect, self.mask, = None, mask
        self.filename = filename

        if meta is None:
            # init container
            self.meta = metadata()
            self.meta.name, self.meta.colorSpace, self.meta.rawMetadata, self.meta.profile, self.meta.orientation = name, colorSpace, rawMetadata, profile, orientation
        else:
            self.meta = meta

        if (filename is None and cv2Img is None and QImg is None):
            # creates a null image
            super(vImage, self).__init__()

        if filename is not None:
            # loads image from file (should be a 8 bits/channel color image)
            if self.meta.orientation is not None:
                tmp =QImage(filename).transformed(self.meta.orientation)
            else:
                tmp = QImage(filename)
            # call to super is mandatory. Shallow copy : no harm !
            super(vImage, self).__init__(tmp)
        elif QImg is not None:
            # builds image from QImage, shallow copy
            super(vImage, self).__init__(QImg)
            if hasattr(QImg, "meta"):
                self.meta = copy(QImg.meta)
        elif cv2Img is not None:
            # builds image from buffer
            super(vImage, self).__init__(ndarrayToQImage(cv2Img, format=format))
        # Format check
        if self.depth() != 32:
            raise ValueError('vImage : should be a 8 bits/channel color image')
        # mask
        self.maskIsEnabled = False
        self.maskIsSelected = False
        if self.mask is None:
            self.mask = QImage(self.width(), self.height(), format)
            self.mask.fill(QColor(255,0,0, 255))
        self.updatePixmap()

    def setModified(self, b):
        """
        Sets the flag isModified and calls hook for menu updating.
        :param b: boolean
        """
        self.isModified = b
        self.onModify()

    def updatePixmap(self):
        """
        Updates image pixmap
        """
        if icc.COLOR_MANAGE:
            img = convertQImage(self)
        else:
            img = QImage(self)
        if self.maskIsEnabled:
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.RasterOp_SourceAndDestination)
            qp.drawImage(0, 0, self.mask)
            qp.end()
        self.qPixmap = QPixmap.fromImage(img)

    def resetMask(self):
        self.mask.fill(QColor(255, 255, 255, 255))

    def resize(self, pixels, interpolation=cv2.INTER_CUBIC):
        """
        Resize an image while keeping its aspect ratio. We use
        the opencv finction cv2.resize() to perform the resizing operation, so we
        can choose the resizing method (default cv2.INTER_CUBIC)
        The original image is not modified.
        :param pixels: pixel count for the resized image
        :param interpolation method (default cv2.INTER_CUBIC)
        :return : the resized vImage
        """
        ratio = self.width() / float(self.height())
        w, h = int(np.sqrt(pixels * ratio)), int(np.sqrt(pixels / ratio))
        hom = w / float(self.width())
        # resizing
        cv2Img = cv2.resize(QImageBuffer(self), (w, h), interpolation=interpolation)
        rszd = vImage(cv2Img=cv2Img, meta=copy(self.meta), format=self.format())

        #resize rect and mask
        if self.rect is not None:
            rszd.rect = QRect(self.rect.left() * hom, self.rect.top() * hom, self.rect.width() * hom, self.rect.height() * hom)
        if self.mask is not None:
            # tmp.mask=cv2.resize(self.mask, (w,h), interpolation=cv2.INTER_NEAREST )
            rszd.mask = self.mask.scaled(w, h)
        self.setModified(True)
        return rszd

    def applyLUT(self, stackedLUT, options={}):
        """
        Applies per channel LUTS to the image

        :param stackedLUT: array color values (in range 0..255). Shape must be (3, 255) : a line for each RGB channel
        :param options: not used yet
        """
        # get image buffers (BGR order on intel proc.)
        ndImg0 = QImageBuffer(self.inputImg)[:, :, :3] #[:, :, ::-1]
        ndImg1 = QImageBuffer(self)[:, :, :3]
        # apply LUTS to the 3 channels
        rList = np.array([2,1,0]) #BGR
        ndImg1[:, :, :]= stackedLUT[rList[np.newaxis,:], ndImg0]
        #update
        self.updatePixmap()

    def apply3DLUT(self, LUT, options={}):
        """
        Applies 3D LUT to the image
        :param LUT: LUT3D array (see module LUT3D.py)
        :param options: dict of string:boolean records
        """
        # get selection
        w1, w2, h1, h2 = (0.0,) * 4
        if options['use selection']:
            if self.rect is not None:
                w1, w2, h1,h2= self.rect.left(), self.rect.right(), self.rect.top(), self.rect.bottom()
            if w1>=w2 or h1>=h2:
                msg = QMessageBox()
                msg.setText("Empty selection\nSelect a region with the marquee tool")
                msg.exec_()
                return
        else:
            w1, w2, h1, h2 = 0, self.inputImg.width(), 0, self.inputImg.height()

        ndImg0 = QImageBuffer(self.inputImg)[h1+1:h2+1, w1+1:w2+1, :3]

        ndImg1 = QImageBuffer(self)[:, :, :3]

        # apply LUT
        start=time()
        ndImg1[h1+1:h2+1,w1+1:w2+1,:] = interpVec(LUT, ndImg0)
        end=time()
        print 'time %.2f' % (end-start)

        self.updatePixmap()


    def histogram(self, size=200, channel=Channel.RGB):
        """
        Plots the histogram of the image for the
        specified channels (all channels or single channel)
        :param size: size of the histogram plot
        :param channel: type Channel
        :return: histogram plot (type QImage)
        """
        # scaling factor for the bin edges
        scale = size / 255.0

        def drawChannelHistogram(qp, channel):
            """
            Computes and draws the (smoothed) histogram of the image for a single channel.
            :param channel: channel index (BGRA (intel) or ARGB )
            """
            buf0 = buf[:,:,2-channel]
            hist, bin_edges = np.histogram(buf0, bins='auto', density=True)
            # smooth hist
            hist = savitzky_golay(hist, 11, 3)
            p = len(hist) - len(bin_edges)
            # P > 1 iff hist was padded by savitzky_golay filter
            # then, we pad bin_edges accordingly
            if p >1:
                p = p /2 +1
                bin_firstVals = (bin_edges[0] - np.arange(p))[::-1]
                bin_lastVals = bin_edges[-1] + np.arange(p-1)
                bin_edges = np.concatenate((bin_firstVals, bin_edges, bin_lastVals))
            # draw hist
            color = Qt.red if channel == Channel.Red else Qt.green if channel == Channel.Green else Qt.blue
            qp.setPen(color)
            for i, y in enumerate(hist):
                qp.drawRect(int(bin_edges[i]*scale), max(img.height()-int(y*20*255),0), int((bin_edges[i+1]-bin_edges[i])*scale), int(y*20*255))

        buf = QImageBuffer(self)
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.white)
        qp = QPainter(img)
        if channel == Channel.RGB:
            for channel in [0,1,2]:
                drawChannelHistogram(qp, channel)
        else:
            drawChannelHistogram(qp, channel)
        qp.end()
        buf = QImageBuffer(img)
        return img

class mImage(vImage):
    """
    Multi-layer image. A mImage object holds at least a background
    layer. All layers share the same metadata object. To correctly render a
    mImage, widgets must override their paint event handler.
    """

    def __init__(self, *args, **kwargs):
        # as updatePixmap uses layersStack, must be before super __init__
        self._layers = {}
        self.layersStack = []
        super(mImage, self).__init__(*args, **kwargs)
        # add background layer
        bgLayer = QLayer.fromImage(self, parentImage=self)
        self.setModified(False)
        self.activeLayerIndex = None
        self.addLayer(bgLayer, name='background')
        self.isModified = False

    def getActiveLayer(self):
        return self.layersStack[self.activeLayerIndex]

    def setActiveLayer(self, value, signaling=True):
        self.activeLayerIndex = value
        if hasattr(self, 'layerView'):
            self.layerView.selectRow(len(self.layersStack) - 1 - value)

    def getActivePixel(self,x, y):
        """
        Reads pixel value from active layer. For
        adjustment or segmentation layer, we read pixel value
        from input image.
        :param x, y: coordinates of pixel
        :return: pixel value (type QRgb : unsigned int ARGB)
        """
        activeLayer = self.getActiveLayer()
        if  hasattr(activeLayer, "inputImg") and activeLayer.inputImg is not None:
            # layer is adjustment or segmentation : read from input image
            return activeLayer.inputImg.pixel(x, y)
        else:
            # read from image
            return activeLayer.pixel(x, y)

    def updatePixmap(self):
        """
        Overrides vImage.updatePixmap()
        """
        vImage.updatePixmap(self)
        for layer in self.layersStack:
                vImage.updatePixmap(layer)


    def addLayer(self, layer, name='', index=None):
        """
        Adds layer.

        :param layer: layer to add (fresh layer if None, type QLayer)
        :param name:
        :param index: index of insertion in layersStack (top of active layer if index=None)
        :return: the layer added
        """
        # building a unique name
        usedNames = [l.name for l in self.layersStack]
        a = 1
        trialname = name if len(name) > 0 else 'noname'
        while trialname in usedNames:
            trialname = name + '_'+ str(a)
            a = a+1
        if layer is None:
            layer = QLayer(QImg=QImage(self))
            layer.fill(Qt.white)
        layer.name = trialname
        layer.parentImage = self
        if index==None:
            if self.activeLayerIndex is not None:
                # add on top of active layer if any
                index = self.activeLayerIndex
            else:
                # empty stack
                index = 0
        self.layersStack.insert(index, layer)
        self.setActiveLayer(index)
        layer.meta = self.meta
        layer.parentImage = self
        self.setModified(True)
        return layer

    def addAdjustmentLayer(self, name='', index=None):
        if index == None:
            # add on top of active layer
            index = self.activeLayerIndex
        # adjust active layer only
        #layer = QLayer(QImg=self.layersStack[index])
        layer = QLayer.fromImage(self.layersStack[index], parentImage=self)
        layer.inputImg = self.layersStack[index]
        self.addLayer(layer, name=name, index=index + 1)
        #layer.parent = self
        #self.setModified(True)
        return layer

    def addSegmentationLayer(self, name='', index=None):
        if index == None:
            index = self.activeLayerIndex
        layer = QLayer.fromImage(self.layersStack[index], parentImage=self)
        layer.inputImg = self.layersStack[index]
        #layer.mask = QImage(self.width(), self.height(), self.format())
        self.addLayer(layer, name=name, index=index + 1)
        layer.parent = self
        self.setModified(True)
        return layer

    def dupLayer(self, index=None):
        if index == None:
            index = len(self.layersStack) - 1
        layer =QLayer.fromImage(self.layersStack[index], parentImage=self)
        self.addLayer(layer, name=self.layersStack[index].name, index=index+1)

    def save(self, filename, quality=-1):
        # build resulting image
        img = QImage(self.width(), self.height(), self.format())
        qpainter = QPainter(img)
        for layer in self.layersStack:
            if layer.visible:
                qpainter.drawImage(0,0, layer)
        qpainter.end()
        # save to file
        if not img.save(filename, quality=quality):
            msg = QMessageBox()
            msg.setText("unable to save file %s" % filename)
            msg.exec_()
        else:
            self.setModified(False)


class imImage(mImage) :
    """
    Interactive multi-layer image
    """
    def __init__(self, *args, **kwargs):
        super(imImage, self).__init__(*args, **kwargs)
        # Zoom_coeff = 1.0 displays an image fitting the
        # size of the current window ( NOT the actual pixels of the image).
        self.Zoom_coeff = 1.0
        self.xOffset, self.yOffset = 0, 0
        self.isMouseSelectable =True
        self.isModified = False

    def resize_coeff(self, widget):
        """
        return the current resizing coefficient. It is used by
        the paint event handler to display the image
        :param widget: Qwidget object
        :return: the (multiplicative) resizing coefficient
        """
        r_w, r_h = float(widget.width()) / self.width(), float(widget.height()) / self.height()
        r = max(r_w, r_h)
        return r * self.Zoom_coeff

    def resize(self, pixels, interpolation=cv2.INTER_CUBIC):
        """
        Resize image and layers
        :param pixels:
        :param interpolation:
        :return: resized imImage object
        """
        # resized vImage
        rszd0 = super(imImage, self).resize(pixels, interpolation=interpolation)
        # resized imImage
        rszd = imImage(QImg=rszd0,meta=copy(self.meta))
        rszd.rect = rszd0.rect
        for k, l  in enumerate(self.layersStack):
            if l.name != "background" and l.name != 'drawlayer':
                img = QLayer.fromImage(self._layers[l.name].resize(pixels, interpolation=interpolation), parentImage=rszd)
                rszd.layersStack.append (img)
                rszd._layers[l.name] = img
        self.isModified = True
        return rszd

    def view(self):
        return self.Zoom_coeff, self.xOffset, self.yOffset

    def setView(self, zoom=1.0, xOffset=0.0, yOffset=0.0):
        self.Zoom_coeff, self.xOffset, self.yOffset = zoom, xOffset, yOffset

    def fit_window(self, win):
        self.Zoom_coeff = 1.0
        self.xOffset, self.yOffset = 0.0, 0.0

    def snapshot(self):
        """
        build a snapshot of image
        :return: imImage object
        """
        snap = imImage(QImg=self, meta=self.meta)
        #snap = QImage(self.width(), self.height(), QImage.Format_ARGB32)
        snap.fill(0)
        qp = QPainter(snap)
        for layer in self.layersStack:
            if layer.visible:
                # monitor profile is applied to all pixmaps, thus we should not build
                # images from pixmaps
                """
                #qp.setOpacity(layer.opacity)
                if layer.qPixmap is not None:
                    qp.drawPixmap(QRect(0, 0, self.width(), self.height()),  layer.transfer() )
                else:
                """
                qp.drawImage(QRect(0, 0, self.width(), self.height()),  layer)
        qp.end()
        # update background layer and call updatePixmap
        snap.layersStack[0].setImage(snap)
        return snap

class QLayer(vImage):
    @classmethod
    def fromImage(cls, mImg, parentImage=None):
        mImg.visible = True
        mImg.alpha = 255
        mImg.window = None
        # for adjustment layer
        mImg.transfer = lambda: mImg.qPixmap
        mImg.inputImg = None
        layer = QLayer(QImg=mImg)
        layer.parentImage=parentImage
        layer.updatePixmap()
        return layer #QLayer(QImg=mImg) #mImg

    def __init__(self, *args, **kwargs):
        self.adjustView = None
        self.parentImage = None
        super(QLayer, self).__init__(*args, **kwargs)
        self.name='noname'
        self.visible = True
        # layer opacity is used by QPainter operations.
        # Its value must be in the range 0.0...1.0
        self.opacity = 1.0
        self.transfer = lambda : self.qPixmap
        # link to grid or curves view for adjustment layers
    """
    def updatePixmap(self):
        if icc.COLOR_MANAGE and self.parentImage is not None:
            # layer color model is parent image colopr model
            img = convertQImage(self, transformation=self.parentImage.colorTransformation)
        else:
            img = QImage(self)
        if self.maskIsEnabled:
            qp=QPainter(img)
            qp.setOpacity(128)
            qp.drawImage(0,0,self.mask)
            qp.end()
        self.qPixmap = QPixmap.fromImage(img)
    """
    def setImage(self, qimg):
        """
        replace layer image with a copy of qimg buffer.
        The layer and qimg must have identical dimensions and type.
        :param qimg: QImage object
        """
        buf1, buf2 = QImageBuffer(self), QImageBuffer(qimg)
        if buf1.shape != buf2.shape:
            raise ValueError("QLayer.setImage : new image and layer must have identical shapes")
        buf1[...] = buf2
        self.updatePixmap()

    def reset(self):
        """
        reset layer by ressetting it to imputImg
        :return:
        """
        self.setImage(self.inputImg)

    def setOpacity(self, value):
        """
        set the opacity attribute to value/100.0
        :param value:
        """
        self.opacity = value /100.0
        return




