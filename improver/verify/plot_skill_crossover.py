import argparse
import os

from matplotlib import pyplot as plt

from improver.verify.statistics import SkillCrossover
from improver.verify.make_plots import plot_crossover_with_coverage


def main(infiles, plotdir, startdate, enddate):
    """
    Read textfiles with lines of the form:

    YYYYMMDDTHHmmZ lead_time_mins threshold_mmh hits misses false_alarms no_det

    Calculate point at which nowcast skill matches UKV as a function of "wet pixels"
    in inputs.

    Args:
        infiles (list of str):
            List of files to read
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

    crossover = SkillCrossover(infiles, start, end, verbose_read=False)

    _, pwet, crossover_time, crossover_csi = crossover.calculate_crossovers(zero_threshold=True)
    plottitle = f'{crossover.nowcast} CSI crossover: rain / no rain threshold'
    plotname = f'{start}-{end}_{crossover.nowcast}_zero.png'.replace(' ', '_')
    plot_crossover_with_coverage(
        pwet, crossover_time, crossover_csi, 0.7,
        title=plottitle, savepath=os.path.join(plotdir, plotname)
    )

    """
    _, pwet, crossover_time, crossover_csi = crossover.calculate_crossovers(zero_threshold=True)
    plottitle = f'{crossover.nowcast} CSI crossover: rain / no rain threshold'
    plotname = f'{start}-{end}_{crossover.nowcast}_zero_filtered.png'.replace(' ', '_')
    plot_crossover_with_coverage(
        pwet, crossover_time, crossover_csi, 0.7, cmin=0.1,
        title=plottitle, savepath=os.path.join(plotdir, plotname)
    )
    """

    _, pwet, crossover_time, crossover_csi = crossover.calculate_crossovers(zero_threshold=False)
    plottitle = f'{crossover.nowcast} CSI crossover: 1 mm/h'
    plotname = f'{start}-{end}_{crossover.nowcast}_1mmh.png'.replace(' ', '_')
    plot_crossover_with_coverage(
        pwet, crossover_time, crossover_csi, 0.5, 
        title=plottitle, savepath=os.path.join(plotdir, plotname)
    )


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', type=str, nargs='+', help='List of textfiles to read')
    parser.add_argument('--plotdir', type=str, help='Output directory to save plot')
    parser.add_argument('--startdate', type=int, default=None)
    parser.add_argument('--enddate', type=int, default=None)
    args = parser.parse_args()

    main(args.infiles, args.plotdir, args.startdate, args.enddate)
