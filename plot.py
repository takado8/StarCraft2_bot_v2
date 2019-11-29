import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def plot(x, y, title=''):
    fig, ax = plt.subplots()

    ax.set(xlabel='x (n=10 games avg)', ylabel='y (avg. kil)',
           title=title)
    ax.grid()
    ax.plot(x,y)
    # plt.draw()
    plt.show()