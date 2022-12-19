import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
import numpy as np
from minimizer import Minimizer

class DividingMethod(Minimizer):
    def __init__(self, delta=1e-10, eps=1e-9, n=900, x_path = []):
        '''
        Segment dividing optimizer

        Arguments
        ---------
        delta: indentation parameter
        eps: minimal distance to minumum, should be less than delta
        n: maximum number of iterations
        x_path: list of pairs [xi - delta/2, xi + delta/2], where xi is a center of the interval on i-th iteration
        '''
        self.delta = delta
        self.eps = eps
        self.n = n
        self.x_path = x_path

    def _dividing_method(self, func, a, b, delta, eps, itera, n, x_path):
        if itera == n:
            print("Reached max number of iterations")
            return (a + b) / 2
        elif (b - a) < eps:
            return (a + b) / 2

        x1 = (a + b - delta) / 2
        x2 = (a + b + delta) / 2
        x_path.append([x1, x2])

        if func(x1) <= func(x2):
            a1 = a
            b1 = x2
        else:
            a1 = x1
            b1 = b
        return self._dividing_method(func, a1, b1, delta, eps, itera+1, n, x_path)

    def minimize(self, func, a, b):
        '''
        Segment dividing optimizer method

        Arguments
        ---------
        func: unimodal function to minimize
        a: left edge of considered segment
        b: right edge of considered segment
        '''
        eps = self.eps
        delta = self.delta
        n = self.n
        x_path = self.x_path
        assert delta < eps, 'delta should be less than eps'
        x = self._dividing_method(func, a, b, delta, eps, 1, n, x_path)
        self.visualize_results(func, a, b, x_path)
        return x

    def visualize_results(self, func, a, b, x_path):
        xlist = np.linspace(a, b, 1000)
        ylist = [func(x) for x in xlist]
        
        fig = plt.figure()
        plt.xlim((min(xlist), max(xlist)))
        plt.ylim((min(ylist), min(ylist) + (max(xlist) - min(xlist))))
        l, = plt.plot([], [],  marker="o", markersize=5, c="red")

        metadata = dict(title="Movie")
        writer = PillowWriter(fps=2, metadata=metadata)

        with writer.saving(fig, "Dividing method.gif", dpi=300):
            plt.plot(xlist, ylist, c='b')
            for i in range(len(x_path)):
                plt.title(f"{i} iteration")

                l.set_data(x_path[i], [func(x) for x in x_path[i]])
                writer.grab_frame()    