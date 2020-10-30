"""Module to plot statistics with lead time"""

import numpy as np
from matplotlib import pyplot as plt


def plot_by_leadtime(stats_dicts, stat, thresholds, outname, one_model=False):
    """Plots statistic "stat" by lead time

    Args:
        stats_dicts (list of StatsDict):
            List of stats from each model.  If one_model=True, only the first
            item is plotted.
        stat (string):
            Name of statistic to be plotted.  Must match a key in StatsDict.
        thresholds (list of float):
            List of thresholds.  If one_model=False, only the first item is
            plotted.
        outname (str):
            Full path to save output plot
        one_model (bool):
            If True, plot range of thresholds from one model on a single axis.
            If False, plot one threshold from a range of models on a single axis.
    """
    plt.figure(figsize=(8, 6))

    if one_model:
        title = f'{stat} with lead time'
        for thresh in thresholds:
            leadtime, skill = stats_dicts[0].trend_with_leadtime(thresh, stat)
            plt.plot(leadtime, skill, label='{:.2f} mm/h'.format(thresh))
    else:
        title = '{} at {:.2f} mm/h'.format(stat, thresholds[0])
        for model in stats_dicts:
            leadtime, skill = stats_dicts[model].trend_with_leadtime(thresholds[0], stat)
            plt.plot(leadtime, skill, label=f'{model}')

    plt.legend()
    plt.xlabel('Lead time (minutes)')
    plt.xlim(left=0)
    plt.xticks(np.arange(0, leadtime[-1]+1, 60))
    plt.ylabel(stat)
    plt.ylim(0, 1)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outname)
    plt.close()


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


def _annotate_4D_plot_points(plt, stm, model, leadtime):
    """Annotate 4D plot points"""
    offset = 0.015
    if model == 'UKV':
        # add value annotations
        for x, y, t in zip(stm['SR'], stm['POD'], stm['thresholds']):
            yoffset = -0.015 if t == 0.03 else offset
            plt.text(x+offset, y-yoffset, f'{t:.2f} mm/h',
                     horizontalalignment='left', verticalalignment='top')

    if model == 'Optical flow' and leadtime <= 90:
        # label all nowcast thresholds up to T+1.5
        for x, y, t in zip(stm['SR'], stm['POD'], stm['thresholds']):
            yoffset = 0.025 if t == 0.03 else offset
            xoffset = 0 if t == 0.03 else offset
            plt.text(x-xoffset, y+yoffset, f'{t:.2f} mm/h',
                     horizontalalignment='right', verticalalignment='bottom')
    elif model == 'Optical flow' and leadtime <= 150:
        # label lower nowcast thresholds up to T+2.5
        for x, y, t in zip(stm['SR'][:3], stm['POD'][:3], stm['thresholds'][:3]):
            plt.text(x-offset, y+offset, f'{t:.2f} mm/h',
                     horizontalalignment='right', verticalalignment='bottom')

    if model == 'Optical flow' and leadtime >= 210:
        # label moderate nowcast thresholds beyond T+3.5
        for x, y, t in zip(stm['SR'][2:4], stm['POD'][2:4], stm['thresholds'][2:4]):
            plt.text(x-offset, y+offset, f'{t:.2f} mm/h',
                     horizontalalignment='right', verticalalignment='bottom')


def make_4D_plot(stats_dicts, leadtime, outname):
    """Based on plots seen at EPS-SRNWP meeting.  Plot POD against FAR for each
    model, one point per threshold.  Show background contour shading of CSI."""

    plot_markers = {}
    marker_list = ['d', '*', 'o']

    plot_stats = {}

    for i, model in enumerate(stats_dicts):
        plot_stats[model] = {"thresholds": [], "POD": [], "SR": []}
        plot_markers[model] = marker_list[i]
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
        plt.plot(plot_stats[model]['SR'], plot_stats[model]['POD'],
                 label=model, marker=plot_markers[model])
        _annotate_4D_plot_points(plt, plot_stats[model], model, leadtime)

    plt.xlabel('Success ratio')
    plt.ylabel('Hit rate')
    plt.legend()
    plt.title(f'Skill at T+{leadtime/60} hrs')
    plt.tight_layout()

    if outname is not None:
        plt.savefig(outname)
    else:
        plt.show()
    plt.close()


def _map_to_colorbar(regimes):
    """Returns a mapped array with its associated ticks and ticklabels"""
    map = {}
    for i, source in enumerate(sorted(np.unique(regimes))):
        map[source] = i
    ticks = sorted(map.values())
    ticklabels = [f'{source:d}' for source in sorted(map.keys())]
    mapped_regimes = [map[r] for r in regimes]
    return mapped_regimes, ticks, ticklabels


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
        if subset is not None:
            plot_where = np.where(np.isin(ccsi, subset))
            pwet = pwet[plot_where]
            ctime = ctime[plot_where]
            ccsi = ccsi[plot_where]

        # Cut out the numbers we're not using
        mapped_regimes, ticks, ticklabels = _map_to_colorbar(ccsi)
        cmap = 'Set2' if len(ticks) <= 8 else 'tab20'

        plt.scatter(pwet, ctime, c=mapped_regimes, vmin=0, vmax=max(ticks), cmap=cmap)
        cbar = plt.colorbar(ticks=ticks)
        cbar.ax.set_yticklabels(ticklabels)

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
    plt.xlim(0, 0.6)
    plt.xlabel('Proportion of "wet" pixels in T+0 radar')

    plt.tight_layout()

    if title is not None:
        plt.title(title)

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()
    plt.close()


def _get_mode(times, time_bins=np.arange(45, 380, 30)):
    n, bins = np.histogram(times, time_bins)
    return bins[list(n).index(max(n))]


def hist_crossover_with_regime(ctime, regime, subset=None, title=None, savepath=None):
    """Plot histograms of crossover time with regime"""
    time_bins = np.arange(45, 380, 30)
    
    plt.figure(figsize=(8, 5))
    ax = plt.subplot(111)

    ax.axvline(x=150, color='black', linestyle='dashed')
    for r in set(regime):
        times = np.array(ctime)[regime == r]
        count = len(times)
        if count < 110:
            continue
        if subset is not None and r not in subset:
            continue

        mode = _get_mode(times)
        ax.hist(times, time_bins, label=f"Regime {r} ({count}): {(mode+15)/60} hrs",
                histtype='step', density=True)

    # plot total
    if subset:
        all_times = np.array(ctime)[np.isin(regime, subset)]
    else:
        all_times = np.array(ctime)

    if subset and len(subset) > 1:
        count = len(all_times)
        mode = _get_mode(all_times)
        ax.hist(all_times, time_bins, label=f"Regimes {subset} ({count}): {(mode+15)/60} hrs",
                histtype='step', density=True, linewidth=2)   

    elif subset is None:
        count = len(all_times)
        mode = _get_mode(all_times)
        ax.hist(all_times, time_bins, label=f"All regimes ({count}): {(mode+15)/60} hrs",
                histtype='step', density=True, linewidth=2) 

    plt.xlim(30, 390)
    plt.xlabel('Skill crossover time (mins)')
    plt.legend(loc='upper center')

    if title is not None:
        plt.title(title)

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()
    plt.close()


def hist_exclude_regimes(ctime, regime, excluded, savepath=None):
    """Plot histograms of crossover time for all input data, and with and without
    excluded regimes"""
    time_bins = np.arange(45, 380, 30)
    
    plt.figure(figsize=(8, 5))
    ax = plt.subplot(111)

    ax.axvline(x=150, color='black', linestyle='dashed')

    # all regimes
    count = len(ctime)
    mode = _get_mode(ctime)
    ax.hist(ctime, time_bins, label=f"All regimes ({count}): {(mode+15)/60} hrs",
            histtype='step', density=True, linewidth=2)

    # separate excluded regime
    all_without_excluded = np.array(ctime)[~np.isin(regime, excluded)]
    count = len(all_without_excluded)
    mode = _get_mode(all_without_excluded)
    label = f"All excluding {excluded} ({count}): {(mode+15)/60} hrs"
    ax.hist(all_without_excluded, time_bins, label=label, histtype='step', density=True)

    only_excluded = np.array(ctime)[np.isin(regime, excluded)]
    count = len(only_excluded)
    mode = _get_mode(only_excluded)
    ax.hist(only_excluded, time_bins, label=f"Regimes {excluded} ({count}): {(mode+15)/60} hrs",
            histtype='step', density=True)

    plt.xlim(30, 390)
    plt.xlabel('Skill crossover time (mins)')
    plt.legend(loc='upper center')

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()
    plt.close()


def hist_groupings(ctime, regime, groupings, savepath=None):
    """Plot histograms of crossover time by groups of regime that show similar behaviour"""
    time_bins = np.arange(45, 380, 30)
    
    plt.figure(figsize=(8, 5))
    ax = plt.subplot(111)    
    ax.axvline(x=150, color='black', linestyle='dashed')

    for subset in groupings:
        times = np.array(ctime)[np.isin(regime, subset)]
        count = len(times)
        mode = _get_mode(times)
        label = f"Regimes {subset} ({count}): {(mode+15)/60} hrs"
        ax.hist(times, time_bins, label=label, histtype='step', density=True)

    plt.xlim(30, 390)
    plt.xlabel('Skill crossover time (mins)')
    plt.legend(loc='upper center')

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()
    plt.close()


def plot_crossover_with_leadtime_thresh_regime(
    thresholds, ctimes, regimes, subset=None, exclude=None, savepath=None
):
    """Takes parallel arrays at different thresholds; find modal crossover time per regime
    and threshold.  Very broad brush to see if we can group regimes by similar behaviour."""

    modal_crossover = {}
    if subset is not None:
        set_of_regimes = subset
    elif exclude is not None:
        set_of_regimes = set(regimes[0]) - set(exclude)
    else:
        set_of_regimes = set(regimes[0])

    for ct, rg, th in zip(ctimes, regimes, thresholds):
        for r in set_of_regimes:
            times = np.array(ct)[rg == r]
            count = len(times)
            if count < 40:
                continue
            if r not in modal_crossover:
                modal_crossover[r] = {"threshold": [], "crossover": [], "median": []}
            mode = _get_mode(times)
            modal_crossover[r]["threshold"].append(th)
            modal_crossover[r]["crossover"].append(mode)
            modal_crossover[r]["median"].append(np.median(times))


    # plot data where it exists
    plt.figure(figsize=(8, 10))
    ax = plt.subplot(211) 
    for rg in sorted(modal_crossover):
        if modal_crossover[rg]:
            ax.plot(modal_crossover[rg]["threshold"],
                    modal_crossover[rg]["crossover"],
                    label=f'Regime {rg}')

    plt.xlim(0, 4.2)
    plt.xlabel('Threshold (mm/h)')
    plt.ylim(30, 390)
    plt.ylabel('Modal skill crossover')
    plt.legend()

    ax = plt.subplot(212) 
    for rg in sorted(modal_crossover):
        if modal_crossover[rg]:
            ax.plot(modal_crossover[rg]["threshold"],
                    modal_crossover[rg]["median"],
                    label=f'Regime {rg}')

    plt.xlim(0, 4.2)
    plt.xlabel('Threshold (mm/h)')
    plt.ylim(30, 390)
    plt.ylabel('Median skill crossover')
    plt.legend()
    
    plt.tight_layout()

    if savepath is not None:
        plt.savefig(savepath)
    else:
        plt.show()
    plt.close()

