import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def plot(x, y, title=''):
    fig, ax = plt.subplots()
    ax.plot(x, y)

    ax.set(xlabel='x (n)', ylabel='y (avg. reward)',
           title=title)
    ax.grid()

    plt.show()