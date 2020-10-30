import argparse
import os

from matplotlib import pyplot as plt

from improver.verify.plotlib import plot_crossover_with_coverage, hist_crossover_with_regime
from improver.verify.regimes import GOOD_REGIMES, BAD_REGIMES
from improver.verify.statistics import SkillCrossover


def make_plots(crossover, filespine, zero_threshold):

    pwet, regime, c_time, c_csi = crossover.calculate_crossovers(zero_threshold=zero_threshold)

    if zero_threshold:
        plottitle = f'{crossover.nowcast} CSI crossover: rain / no rain threshold'
        thresh = 'zero'
        cmax=0.7  
    else:
        plottitle = f'{crossover.nowcast} CSI crossover: 1 mm/h threshold'
        thresh = '1mmh'
        cmax=0.5

    plotname1a = f'{filespine}_{thresh}.png'
    plotname1b = f'{filespine}_{thresh}_good.png'
    plotname1c = f'{filespine}_{thresh}_bad.png'
    plotname2a = f'{filespine}_{thresh}_with_regime.png'
    plotname2b = f'{filespine}_{thresh}_with_regime_good.png'
    plotname2c = f'{filespine}_{thresh}_with_regime_bad.png'    
    plotname3a = f'{filespine}_{thresh}_ctime_regime.png'
    plotname3b = f'{filespine}_{thresh}_ctime_regime_good.png'
    plotname3c = f'{filespine}_{thresh}_ctime_regime_bad.png'

    """
    plot_crossover_with_coverage(
        pwet, c_time, c_csi, cmax, title=plottitle, savepath=plotname1a
    )

    plot_crossover_with_coverage(
        pwet, c_time, c_csi, cmax, regimes=regime, subset=GOOD_REGIMES,
        title=plottitle, savepath=plotname1b
    )

    plot_crossover_with_coverage(
        pwet, c_time, c_csi, cmax, regimes=regime, subset=BAD_REGIMES,
        title=plottitle, savepath=plotname1c
    )

    plot_crossover_with_coverage(
        pwet, c_time, regime, None, title=plottitle, savepath=plotname2a
    )

    plot_crossover_with_coverage(
        pwet, c_time, regime, None, title=plottitle, subset=GOOD_REGIMES, savepath=plotname2b
    )

    plot_crossover_with_coverage(
        pwet, c_time, regime, None, title=plottitle, subset=BAD_REGIMES, savepath=plotname2c
    )
    """
 
    hist_crossover_with_regime(c_time, regime, savepath=plotname3a)
    #hist_crossover_with_regime(c_time, regime, subset=GOOD_REGIMES, savepath=plotname3b)
    #hist_crossover_with_regime(c_time, regime, subset=BAD_REGIMES, savepath=plotname3c)


def main(countfiles, regimes, plotdir, startdate, enddate):
    """
    Read textfiles with lines of the form:

    YYYYMMDDTHHmmZ lead_time_mins threshold_mmh hits misses false_alarms no_det

    Calculate point at which nowcast skill matches UKV as a function of "wet pixels"
    in inputs.

    Args:
        countfiles (list of str):
            List of files containing counts from trial
        regimes (str or None):
            File containing weather regimes for each day in trial
        plotdir (str):
            Full path to directory to save plot
        startdate (int or None):
            Date to start calculation in YYYYMMDD format
        enddate (int or None):
            Date to end calculation in YYYYMMDD format
    """
    # set start and end times for item filtering
    start = startdate
    end = enddate
    if start is None:
        start = 20200601
    if end is None:
        end = 20200731

    crossover = SkillCrossover(
        countfiles, regimes, start, end, verbose_read=False, use_eu=False
    )

    nc_name = f'{crossover.nowcast}'.replace(' ', '_').lower()
    filespine = os.path.join(plotdir, f'{start}-{end}_{nc_name}')

    make_plots(crossover, filespine, True)
    make_plots(crossover, filespine, False)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('countfiles', type=str, nargs='+', help='List of textfiles '
                        'containing counts per month and model')
    parser.add_argument('--regimes', type=str, help='Textfile containing regimes '
                        'for each day', default=None)
    parser.add_argument('--plotdir', type=str, help='Output directory to save plot')
    parser.add_argument('--startdate', type=int, default=None)
    parser.add_argument('--enddate', type=int, default=None)
    args = parser.parse_args()

    main(args.countfiles, args.regimes, args.plotdir, args.startdate, args.enddate)
