from PyQt5 import QtWidgets, QtCore
from client.gui.UIStaff import UIStaff
import client.gui.UISettings as UISet


class UIStaffGroup(QtWidgets.QGraphicsItemGroup):

    """
    A collection of staff lines representing multiple parts over some range of
    measures.
    """

    def __init__(self, canvas, measureLists, startMeasure, endMeasure, *args, **kwargs):
        """
        :param canvas: QGraphicsScene being used to manage the score view.
        :param measureLists: A list of lists of measures, each containing at
            least endMeasure measures.
        :param startMeasure: The index of the first measure to be displayed in
            this staff group.
        :param endMeasure: The index of the measure after the last one to be
            displayed by this staff group.
        """
        super(UIStaffGroup, self).__init__(*args, **kwargs)
        # Because of some weirdness in how QGraphicsScene scene graphs work, we
        # need to have access to the graphics scene in order to be able to
        # remove items correctly.
        self.__canvas = canvas

        self.__measureLists = measureLists
        self.__startMeasure = startMeasure
        self.__endMeasure = endMeasure

        # List containing the staff lines for each part
        self.__staves = []
        # Update and redraw everything
        self.refresh()

    def length(self):
        """
        Return the time length of this staff group, i.e. the time between the
        first beat of this line and the first beat of the next one.
        """
        if not self.__staves:
            return 0
        return self.__staves[0].length()

    def refresh(self):
        """
        Recreate the staves based on the measure list, and re-space them to
        reflect new notes, etc.
        """
        self.__updateStaves()
        self.__updatePositions()

    def __updateStaves(self):
        """
        Recreate all staves to reflect changes in the measure lists.
        """
        for s in self.__staves:
            self.__canvas.removeItem(s)
        self.__staves = [
            UIStaff(ml, self.__startMeasure, self.__endMeasure, parent=self)
            for ml in self.__measureLists
        ]

    def __updatePositions(self):
        """
        Move staff lines around to be appropriately spaced.
        """
        y_offset = 0
        for s in self.__staves:
            y = s.boundingRect().y()
            h = s.boundingRect().height()
            s.setPos(0, y_offset)
            y_offset += y + h

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
            x, y - UISet.STAFF_GROUP_Y_PAD, width, height + 2 * UISet.STAFF_GROUP_Y_PAD
        )
