from PyQt5 import QtCore, QtWidgets

import client.gui.UISettings as UISet
from client.gui.UIMeasure import UIMeasure


class UIStaff(QtWidgets.QGraphicsItemGroup):
    def __init__(self, measureList, startMeasure, endMeasure, *args, **kwargs):
        """
        :param measureLists: A list of lists of measures, each containing at
            least endMeasure measures.
        :param startMeasure: The index of the first measure to be displayed in
            this staff group.
        :param endMeasure: The index of the measure after the last one to be
            displayed by this staff group.
        """
        super(UIStaff, self).__init__(*args, **kwargs)
        self.__measureList = measureList
        self.__startMeasure = startMeasure
        self.__endMeasure = endMeasure

        xpos = 0
        for i in range(startMeasure, endMeasure):
            self.__measureList[i].setParentItem(self)
            self.__measureList[i].setPos(xpos, 0)
            xpos += self.__measureList[i].width()

    def measures(self):
        """
        Return the number of measures that this UIStaff is displaying.
        """
        return self.__endMeasure - self.__startMeasure

    def length(self):
        """
        Return the time length of this staff, i.e. the time between the first
        beat of this line and the first beat of the next one.
        """
        return sum(
            map(length(self.__measures[self.__startMeasure : self.__endMeasure]))
        )

    def boundingRect(self):
        """
        Return a QRectF giving the boundaries of the object being drawn; used in
        score layout, and by Qt for calculating redraws.

        :returns: A QRectF which contains everything drawn by this staff group.
        """
        childBoundRect = self.childrenBoundingRect()
        x = childBoundRect.x()
        y = childBoundRect.y()
        width = childBoundRect.width()
        height = childBoundRect.height()
        return QtCore.QRectF(
            x - UISet.STAFF_X_PAD,
            y - UISet.STAFF_Y_PAD,
            width + 2 * UISet.STAFF_X_PAD,
            height + 2 * UISet.STAFF_Y_PAD,
        )
