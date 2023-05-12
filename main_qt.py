import sys
sys.path.append('optimizers')
import random
import string
import subprocess
from functools import reduce
import importlib

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

from sympy import symbols, lambdify
from sympy.parsing.sympy_parser import parse_expr

from PyQt6 import QtCore, QtWidgets

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLineEdit,
    QLabel,
    QFormLayout,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox
)


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


from optimizers.swarm_method import SwarmMethod


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, fig=None, width=5, height=4, dpi=100):
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QMainWindow):

    z_data = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setFixedSize(1030, 768)

        self.hlayout = QHBoxLayout()

        self.vlayout0 = QVBoxLayout()
        self.vlayout1 = QVBoxLayout()

        self.hlayout.addLayout(self.vlayout0)
        self.hlayout.addLayout(self.vlayout1)

        # methods init
        self.optimizer = SwarmMethod(n=10, iterations=1000, tol=0.1)

        # vlayout0 init
        width, height= 12, 12
        dpi = 100
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = MplCanvas(self, self.fig, width=width, height=height, dpi=dpi)
        self.vlayout0.addWidget(self.canvas)

        self.ledit_func = QLineEdit()
        qf_layout0 = QFormLayout()
        qf_layout0.addRow("function", self.ledit_func)
        self.vlayout0.addLayout(qf_layout0)

        # vlayout1 init
        self.vlayout1.addStretch()
        start_stop_button = QPushButton("START/STOP")
        start_stop_button.clicked.connect(self.toggle_start_stop)
        self.vlayout1.addWidget(start_stop_button)

        draw_button = QPushButton("Draw")
        self.vlayout1.addWidget(draw_button)
        draw_button.clicked.connect(self.draw_n_init_function)

        self.ledit_nargs = QLineEdit()
        qf_layout1 = QFormLayout()
        qf_layout1.addRow("n args", self.ledit_nargs)
        self.ledit_nargs.setText("2")
        
        self.ledit_ndots = QLineEdit()
        qf_layout1.addRow("n dots", self.ledit_ndots)
        self.ledit_ndots.setText(str(self.optimizer.n))
        
        self.ledit_iter = QLineEdit()
        qf_layout1.addRow("n iterations", self.ledit_iter)
        self.ledit_iter.setText(str(self.optimizer.iterations))
        
        self.ledit_x = QLineEdit()
        qf_layout1.addRow("x init", self.ledit_x)
        self.ledit_x.setText('0.0, 0.0')
        
        self.ledit_a = QLineEdit()
        qf_layout1.addRow("a init", self.ledit_a)
        self.ledit_a.setText(str(self.optimizer.a))
        
        self.ledit_b = QLineEdit()
        qf_layout1.addRow("b init", self.ledit_b)
        self.ledit_b.setText(str(self.optimizer.b))
        
        self.ledit_shift_x = QLineEdit()
        qf_layout1.addRow("shift x", self.ledit_shift_x)
        self.ledit_shift_x.setText(str(self.optimizer.shift_x))
        
        self.ledit_shift_y = QLineEdit()
        qf_layout1.addRow("shift y", self.ledit_shift_y)
        self.ledit_shift_y.setText(str(self.optimizer.shift_y))
        
        self.ledit_tol = QLineEdit()
        qf_layout1.addRow("tolerance", self.ledit_tol)
        self.ledit_tol.setText(str(self.optimizer.tol))
        
        self.combox_optim = QComboBox(self)
        self.combox_optim.addItems(["classic", "inertia"])
        qf_layout1.addRow("optim", self.combox_optim)
        self.vlayout1.addLayout(qf_layout1)
        
        self.vlayout1.addStretch()

        # self.setCentralWidget(self.canvas)
        centralWidget = QWidget(self)
        centralWidget.setLayout(self.hlayout)
        self.setCentralWidget(centralWidget)

        # end window init
        self.update_plot()
        self.show()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot)
        # self.timer.start()
        self.timer_started = False 
        

    def draw_n_init_function(self):
        n_args = int(self.ledit_nargs.text())
        f_str = str(self.ledit_func.text())
        n_dots = int(self.ledit_ndots.text())
        n_iterations = int(self.ledit_iter.text())
        init_a = float(self.ledit_a.text())
        init_b = float(self.ledit_b.text())
        shift_x = float(self.ledit_shift_x.text())
        shift_y = float(self.ledit_shift_y.text())
        tolerance = float(self.ledit_tol.text())
        method = str(self.combox_optim.currentText())

        self.optimizer.n = n_dots
        self.optimizer.iterations = n_iterations
        self.optimizer.a = init_a
        self.optimizer.b = init_b
        self.optimizer.shift_x = shift_x
        self.optimizer.shift_y = shift_y    
        self.optimizer.tol = tolerance  
        self.optimizer.optim = method
        
        self.func = create_function(f_str, n_args)

        x_init = list(map(float, self.ledit_x.text().split(", ")))

        self.method_gen = self.optimizer.minimize(self.func, x_init)
        self.xs, self.x_best, inform = next(self.method_gen)

        self.x_min = self.optimizer.xmin
        self.x_max = self.optimizer.xmax
        self.y_min = self.optimizer.ymin
        self.y_max = self.optimizer.ymax

        x_data = np.linspace(self.x_min, self.x_max, 1000)
        y_data = np.flip(np.linspace(self.y_min, self.y_max, 1000))

        self.x_data = np.repeat(x_data[None, :], 1000, axis=0)
        self.y_data = np.repeat(y_data[:, None], 1000, axis=1)

        tmp_data = self.func(self.x_data, self.y_data)

        self.z_data = tmp_data

        self.update_plot()
        # self.toggle_start_stop()

    def update_plot(self):
        # Drop off the first y element, append a new one.
        # self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        # self.canvas.axes.cla()  # Clear the canvas.
        # self.canvas.axes.plot(self.xdata, self.ydata, 'r')
        # # Trigger the canvas to update and redraw.
        # self.canvas.draw()

        self.canvas.axes.cla()  # Clear the canvas.

        if self.z_data is None:
            self.x_min = -25
            self.x_max = 15
            self.y_min = -20
            self.y_max = 20

            x_data = np.linspace(self.x_min, self.x_max, 1000)
            y_data = np.linspace(self.y_min, self.y_max, 1000)

            self.x_data = np.repeat(x_data[None, :], 1000, axis=0)
            self.y_data = np.repeat(y_data[:, None], 1000, axis=1)
            self.z_data = np.ones((1000, 1000))

            # self.canvas.axes.imshow(self.z_data)
            self.c = self.canvas.axes.pcolormesh(self.x_data, self.y_data, self.z_data, cmap='viridis')
            self.canvas.axes.figure.colorbar(self.c)

            # update time
            self.iterations = -1
            self.canvas.axes.set_title(f"Iterations: {self.iterations}")
        else:
            self.canvas.axes.set_xticks(np.arange(self.x_min, self.x_max+1, 4))
            self.canvas.axes.set_yticks(np.arange(self.y_min, self.y_max+1, 4))
            self.canvas.axes.imshow(self.z_data, extent=[self.x_min, self.x_max, self.y_min, self.y_max])
            self.c.set_clim(vmin=self.z_data.min(), vmax=self.z_data.max())

            # update time
            self.iterations += 1
            self.canvas.axes.set_title(f"Iterations: {self.iterations}")

            self.canvas.axes.scatter(self.xs[:, 0], self.xs[:, 1], color='red')
            self.canvas.axes.scatter(self.x_best[0], self.x_best[1], color='black')

            self.xs, self.x_best, inform = next(self.method_gen)

            if inform == "END":
                self.toggle_start_stop()
            print(self.x_best)


        # Trigger the canvas to update and redraw.
        self.canvas.draw()
        
    def toggle_start_stop(self):
        if self.timer_started:
            self.timer.stop()
            self.timer_started = False
        else:
            self.timer.start()
            self.timer_started = True


def create_function(f_str, n_args):
    vocabulary = ['sin', 'cos', 'tan', 'exp', 'log', 'log10', 'log2', 'abs', 'sqrt', 'arcsin', 'arccos', 'arctan']
    alphabet = string.ascii_lowercase[:n_args]
    xs = reduce(lambda a, b: f'{a}, {b}', alphabet)

    for tmp_func in vocabulary:
        f_str = f_str.replace(tmp_func, f'np.{tmp_func}')
    
    with open("tmp_function.py", "w") as f:
        f.write("import numpy as np\n\ndef func({}): return {}".format(xs, f_str))

    import tmp_function
    importlib.reload(tmp_function)

    return tmp_function.func


app = QApplication(sys.argv)
w = MainWindow()
app.exec()
