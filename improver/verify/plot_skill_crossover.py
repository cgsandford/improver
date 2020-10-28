import argparse
import os

from matplotlib import pyplot as plt

from improver.verify.statistics import SkillCrossover
from improver.verify.make_plots import plot_crossover_with_coverage, hist_crossover_with_regime

def make_plots(crossover, filespine, zero_threshold, rtype):

    pwet, regime, c_time, c_csi = crossover.calculate_crossovers(zero_threshold=zero_threshold)

    if zero_threshold:
        plottitle = f'{crossover.nowcast} CSI crossover: rain / no rain threshold'
        thresh = 'zero'
        cmax=0.7  
    else:
        plottitle = f'{crossover.nowcast} CSI crossover: 1 mm/h threshold'
        thresh = '1mmh'
        cmax=0.5

    plotname1 = f'{filespine}_{thresh}.png'
    plotname2a = f'{filespine}_{thresh}_with_{rtype}_regime.png'
    plotname2b = f'{filespine}_{thresh}_with_{rtype}_regime_subset.png'
    plotname3a = f'{filespine}_{thresh}_ctime_with_{rtype}_regime.png'
    plotname3b = f'{filespine}_{thresh}_ctime_with_{rtype}_regime_subset.png'
         
    plot_crossover_with_coverage(
        pwet, c_time, c_csi, cmax, title=plottitle, savepath=plotname1
    )

    plot_crossover_with_coverage(
        pwet, c_time, regime, None, title=plottitle, savepath=plotname2a
    )


    if rtype == 'eu':
        rsubset = [1, 2, 3]
    else:
        rsubset = [6, 8]

    plot_crossover_with_coverage(
        pwet, c_time, regime, None, title=plottitle, regimes=rsubset, savepath=plotname2b
    )
  
    hist_crossover_with_regime(c_time, regime, savepath=plotname3a)
    hist_crossover_with_regime(c_time, regime, min_count=150, savepath=plotname3b)


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

    use_eu = False
    if use_eu:
        rtype = 'eu'
    else:
        rtype = 'uk'

    crossover = SkillCrossover(
        countfiles, regimes, start, end, verbose_read=False, use_eu=use_eu
    )

    nc_name = f'{crossover.nowcast}'.replace(' ', '_').lower()
    filespine = os.path.join(plotdir, f'{start}-{end}_{nc_name}')

    make_plots(crossover, filespine, True, rtype)
    make_plots(crossover, filespine, False, rtype)


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
