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


def _csi_contours(pod, sr):
    """Takes the list of x and y axis points (POD and Success Ratio = 1 - FAR)
    and constructs the z-values we'll contour fill"""
    csi = np.zeros(shape=(len(sr), len(pod)))
    for x in range(len(sr)):
        for y in range(len(pod)):
            if pod[y] > 0 and sr[x] > 0:
                denom = (1./pod[y] + 1./sr[x]) - 1.
                csi[x, y] = 1. / denom
    return csi


def make_4D_plot(stats_dicts, leadtime, outname):
    """Based on plots seen at EPS-SRNWP meeting.  Plot POD against FAR for each
    model, one point per threshold.  Show background contour shading of CSI."""

    plot_stats = {}

    for model in stats_dicts:
        plot_stats[model] = {"thresholds": [], "POD": [], "SR": []}
        for thresh in sorted(stats_dicts[model].data[leadtime]):
            plot_stats[model]["thresholds"].append(thresh)
            plot_stats[model]["POD"].append(stats_dicts[model].data[leadtime][thresh]['POD'])       
            plot_stats[model]["SR"].append(1. - stats_dicts[model].data[leadtime][thresh]['FAR'])

    plt.figure(figsize=(8, 6))

    pod = sr = np.arange(0, 1.01, 0.05)
    plt.contourf(pod, sr, _csi_contours(pod, sr), cmap='Blues', levels=np.arange(0, 1.01, 0.05))
    cbar = plt.colorbar()
    cbar.ax.set_ylabel('Critical success index')
    cbar.set_ticks(np.arange(0, 1.01, 0.1))

    for model in plot_stats:
        plt.plot(plot_stats[model]['SR'], plot_stats[model]['POD'], label=model, marker='o')

    plt.xlabel('Success ratio')
    plt.ylabel('Hit rate')
    plt.legend()
    
    plt.tight_layout()

    if outname is not None:
        plt.savefig(outname)
    else:
        plt.show()


def plot_crossover_with_coverage(pwet, ctime, ccsi, cmax, regimes=None, subset=None,
                                 title=None, savepath=None):
    """Plot crossover skill with amount of rain in original image.
    Colour code by crossover CSI or weather regime.  Option to filter
    by shortlist of regimes."""
    plt.figure(figsize=(8, 6))
    ax = plt.subplot(111)

    ax.axhline(y=150, color='black', linestyle='dashed')

    if cmax is None:
        # Plot by regime - categorical colorbar
        rmax = max(ccsi)
        if subset is not None:
            plot_where = np.where(np.isin(ccsi, subset))
            pwet = pwet[plot_where]
            ctime = ctime[plot_where]
            ccsi = ccsi[plot_where]

        cmap='tab10'
        if rmax > 10:
            cmap='tab20'

        plt.scatter(pwet, ctime, c=ccsi, vmin=1, vmax=rmax, cmap=cmap)
        plt.colorbar(ticks=np.arange(1, rmax+0.1, 1))

    else:
        if regimes is not None and subset is not None:
            plot_where = np.where(np.isin(regimes, subset))
            pwet = pwet[plot_where]
            ctime = ctime[plot_where]
            ccsi = ccsi[plot_where]

        # Plot by CSI - continuous colorbar
        plt.scatter(pwet, ctime, c=ccsi, vmin=0.0, vmax=cmax)
        plt.colorbar(ticks=np.arange(0, cmax+0.1, 0.1))

    plt.ylim(40, 400)
    plt.ylabel('Crossover time (mins)')
    plt.xlim(left=0)  #, 0.6)
    plt.xlabel('Proportion of "wet" pixels in T+0 radar')

    plt.tight_layout()

    if title is not None:
        plt.title(title)

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()


def hist_crossover_with_regime(ctime, regime, subset=None, title=None, savepath=None):
    """Plot histograms of crossover time with regime"""
    set_of_regimes = set(regime)
    time_bins = np.arange(45, 380, 30)
    
    plt.figure(figsize=(8, 5))
    ax = plt.subplot(111)

    ax.axvline(x=150, color='black', linestyle='dashed')
    for r in set_of_regimes:
        times = np.array(ctime)[regime == r]
        count = len(times)
        if count < 75:
            continue
        if subset is not None and r not in subset:
            continue
        ax.hist(times, time_bins, label=f"Regime {r} ({count})", histtype='step', density=True)

    plt.xlim(30, 390)
    plt.xlabel('Skill crossover time (mins)')
    plt.legend(loc='upper center')

    if title is not None:
        plt.title(title)

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()

