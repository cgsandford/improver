import argparse
import os

from matplotlib import pyplot as plt

from improver.verify.statistics import SkillCrossover


def main(infiles, plotdir, startdate, enddate):
    """
    Read textfiles with lines of the form:

    YYYYMMDDTHHmmZ lead_time_mins threshold_mmh hits misses false_alarms no_det

    Calculate binary statistics (POD, FAR, CSI), and plot with lead time

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


    data = SkillCrossover(infiles, start, end, verbose_read=False)

    nwet, pwet, crossover_time, crossover_csi = data.calculate_crossovers()

    plt.scatter(nwet, crossover_time, c=crossover_csi)
    plt.colorbar()
    plt.ylim(40, 400)
    plt.ylabel('Crossover time (mins)')
    plt.show()



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', type=str, nargs='+', help='List of textfiles to read')
    parser.add_argument('--plotdir', type=str, help='Output directory to save plot')
    parser.add_argument('--startdate', type=int, default=None)
    parser.add_argument('--enddate', type=int, default=None)
    args = parser.parse_args()

    main(args.infiles, args.plotdir, args.startdate, args.enddate)
