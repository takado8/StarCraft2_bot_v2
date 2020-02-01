import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def plot(time, y1, y2):

    fig, ax = plt.subplots()
    plt.ion()
    ax.set(xlabel='time (s)', ylabel='lost cost', title='')
    ax.grid()
    ax.plot(time,y1)
    ax.plot(time,y2)
    plt.show(1)
