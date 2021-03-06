from PyQt5 import QtWidgets, uic, QtGui, QtCore, QtSvg
import numpy
import maze
import os

ROWS = 15
COLUMNS = 15
CELL_SIZE = 32
VALUE_ROLE = QtCore.Qt.UserRole


def get_filename(name):
    return os.path.join(os.path.dirname(__file__), name)


def pixels_to_logical(x, y):
        return y // CELL_SIZE, x // CELL_SIZE


def logical_to_pixels(row, column):
        return column * CELL_SIZE, row * CELL_SIZE


SVG_GRASS = QtSvg.QSvgRenderer(get_filename('img/grass.svg'))
SVG_WALL = QtSvg.QSvgRenderer(get_filename('img/wall.svg'))

SVG_DUDE = QtSvg.QSvgRenderer(get_filename('img/dude1.svg'))

SVG_CASTLE = QtSvg.QSvgRenderer(get_filename('img/castle.svg'))
SVG_UP = QtSvg.QSvgRenderer(get_filename('img/arrows/up.svg'))
SVG_DOWN = QtSvg.QSvgRenderer(get_filename('img/arrows/down.svg'))
SVG_LEFT = QtSvg.QSvgRenderer(get_filename('img/arrows/left.svg'))
SVG_RIGHT = QtSvg.QSvgRenderer(get_filename('img/arrows/right.svg'))


class GridWidget(QtWidgets.QWidget):

    def __init__(self, array):
        super().__init__()
        self.array = array
        self.analyzed_maze = None
        self.path = None
        self._resize()

    def _resize(self):
        size = logical_to_pixels(*self.array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)
        self.update()

    def paintEvent(self, event):
        rect = event.rect()
        painter = QtGui.QPainter(self)  # self aby nam kreslil na to okynko
        # minimal coordinates
        row_min, col_min = pixels_to_logical(rect.left(), rect.top())
        row_min = max(row_min, 0)  # kdyz dostanu zaporny index od OS k prekresleni, musi mzacit od nuly
        col_min = max(col_min, 0)
        # max coordinates
        row_max, col_max = pixels_to_logical(rect.right(), rect.bottom())
        row_max = min(row_max + 1, self.array.shape[0])
        col_max = min(col_max + 1, self.array.shape[1])
        # ted vime kde zacit a kde skoncit
        for row in range(row_min, row_max):
            for column in range(col_min, col_max):
                # get rectangle to paint
                x, y = logical_to_pixels(row, column)
                rect = QtCore.QRectF(x, y, CELL_SIZE, CELL_SIZE)
                # white for semi-opacity images
                color = QtGui.QColor(255, 255, 255)
                painter.fillRect(rect, QtGui.QBrush(color))
                # at the beginning fill everything eith grass
                SVG_GRASS.render(painter, rect)
                self.render_maze(row, column, painter, rect)

    def render_maze(self, row, column, painter, rect):
        """ Fills up the maze with walls, castle and arrows """
        self.analyzed_maze = maze.solver.analyze(self.array)
        dude = None
        # basic maze and walls
        if self.array[row, column] < 0:
            SVG_WALL.render(painter, rect)
        if self.array[row, column] == 1:
            SVG_CASTLE.render(painter, rect)

        if self.array[row, column] == 2:
            SVG_DUDE.render(painter, rect)
            self.path = self.analyzed_maze.path(row, column)
            dude = (row, column)

        if self.analyzed_maze.directions[row, column] == b'^':
            if self.path and (row, column) in self.path and (row, column) != dude:
                SVG_UP.render(painter, rect)
        if self.analyzed_maze.directions[row, column] == b'v':
            if self.path and (row, column) in self.path and (row, column) != dude:
                SVG_DOWN.render(painter, rect)
        if self.analyzed_maze.directions[row, column] == b'>':
            if self.path and (row, column) in self.path and (row, column) != dude:
                SVG_RIGHT.render(painter, rect)
        if self.analyzed_maze.directions[row, column] == b'<':
            if self.path and (row, column) in self.path and (row, column) != dude:
                SVG_LEFT.render(painter, rect)

    def mousePressEvent(self, event):
        row, column = pixels_to_logical(event.x(), event.y())
        rows, columns = self.array.shape
        # je to, kam jsem kliknul mezi nulou a koncem matice?
        # muzu totiz kliknout uplne vedle
        if 0 <= row < rows and 0 <= column < columns:
            if event.button() == QtCore.Qt.LeftButton:
                self.array[row, column] = self.selected
            elif event.button() == QtCore.Qt.RightButton:
                self.array[row, column] = 0
            else:
                return
            self.update()



class MazeGui(object):
    """ Class representing maze GUI """
    def __init__(self):
        """ Init all neded stuff """
        self.app = QtWidgets.QApplication([])  # init app
        self.window = window = QtWidgets.QMainWindow()  # set main GUI window
        self.array = maze.generator.generate_maze(COLUMNS, ROWS)
        self.new_dialog = None
        self.path = None

        with open(get_filename('ui/MainWindow.ui')) as file:
            uic.loadUi(file, window)

        self.scroll_area = window.findChild(QtWidgets.QScrollArea, 'scrollArea')
        self.grid = grid = GridWidget(self.array)
        self.scroll_area.setWidget(grid)
        self.palette = window.findChild(QtWidgets.QListWidget, 'listWidget')
        self._fill_palette()
        self.palette.itemSelectionChanged.connect(self._activate_item)
        self.palette.setCurrentRow(1)  # set wall as default selection in the list

        self._action('actionNew').triggered.connect(self._new_dialog)

    def _fill_palette(self):
        """ Fill palette list with all the items """
        self._add_item('Grass', 'img/grass.svg', 0)
        self._add_item('Wall', 'img/wall.svg', -1)
        self._add_item('Dude1', 'img/dude1.svg', 2)

    def _add_item(self, name, file, flag):
        """ Add one item into the palette """
        item = QtWidgets.QListWidgetItem(name)
        icon = QtGui.QIcon(get_filename(file))
        item.setIcon(icon)
        item.setData(VALUE_ROLE, flag)
        self.palette.addItem(item)

    def _action(self, name):
        return self.window.findChild(QtWidgets.QAction, name)

    def _activate_item(self):
        """ Activate an item selected byt a user"""
        for item in self.palette.selectedItems():
            self.grid.selected = item.data(VALUE_ROLE)

    def _new_dialog(self):
        """ Creates a new maze """
        dialog = QtWidgets.QDialog(self.window)
        dialog.setModal(True)
        # load QT designer layout
        with open(get_filename('ui/newmaze.ui')) as file:
            uic.loadUi(file, dialog)

        if not dialog.exec():
            dialog.destroy()
            return
        # choose particular widget and call the value
        cols = dialog.findChild(QtWidgets.QSpinBox, 'spinWidth').value()
        rows = dialog.findChild(QtWidgets.QSpinBox, 'spinHeight').value()
        dialog.destroy()
        self.array = self.grid.array = maze.generator.generate_maze(cols, rows)
        # re-draw the whole grid
        self.grid._resize()

    def run(self):
        self.window.show()
        return self.app.exec()


def main():
    gui = MazeGui()
    return gui.run()
