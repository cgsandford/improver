"""Module to plot statistics with lead time"""

import numpy as np
from matplotlib import pyplot as plt


def plot_by_leadtime(stats_dict, stat, thresholds, outname):
    """Plots statistic "stat" by lead time for a range of thresholds"""
    plt.figure(figsize=(8, 6))
    for thresh in thresholds:
        leadtime, skill = stats_dict.trend_with_leadtime(thresh, stat)
        plt.plot(leadtime, skill, label='{:.2f} mm/h'.format(thresh))
    plt.legend()
    plt.xlabel('Lead time (minutes)')
    plt.xlim(left=0)
    plt.xticks(np.arange(0, leadtime[-1]+1, 60))
    plt.ylabel(stat)
    plt.ylim(0, 1)
    plt.title(f'{stat} with lead time')
    plt.tight_layout()
    plt.savefig(outname)


def plot_by_threshold(stats_dicts, stat, thresh, outname):
    """Plots statistic "stat" by lead time for each model at a single threshold"""
    plt.figure(figsize=(8, 6))
    for model in stats_dicts:
        leadtime, skill = stats_dicts[model].trend_with_leadtime(thresh, stat)
        plt.plot(leadtime, skill, label=f'{model}')
    plt.legend()
    plt.xlabel('Lead time (minutes)')
    plt.xlim(left=0)
    plt.xticks(np.arange(0, leadtime[-1]+1, 60))
    plt.ylabel(stat)
    plt.ylim(0, 1)
    plt.title('{} at {:.2f} mm/h'.format(stat, thresh))
    plt.tight_layout()
    plt.savefig(outname)


def plot_crossover_with_coverage(
        pwet, ctime, ccsi, cmax, cmin=0.0, title=None, savepath=None
):
    """Plot crossover skill with amount of rain in original image"""
    plt.figure(figsize=(8, 6))
    ax = plt.subplot(111)

    ax.axhline(y=150, color='black', linestyle='dashed')
    plt.scatter(pwet[ccsi >= cmin], ctime[ccsi >= cmin], c=ccsi[ccsi >= cmin],
                vmin=0.0, vmax=cmax)
    plt.colorbar(ticks=np.arange(0, cmax+0.1, 0.1))

    plt.ylim(40, 400)
    plt.ylabel('Crossover time (mins)')
    plt.xlim(0, 0.6)
    plt.xlabel('Proportion of "wet" pixels in T+0 radar')

    plt.tight_layout()

    if title is not None:
        plt.title(title)

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()

