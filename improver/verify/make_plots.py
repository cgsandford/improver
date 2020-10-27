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
