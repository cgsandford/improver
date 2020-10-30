import argparse
import os

from improver.verify.parse_file import get_model, accumulate_count_files
from improver.verify.statistics import StatsDict
from improver.verify.make_plots import make_4D_plot


def main(infiles, plotdir, startdate, enddate):
    """
    Read textfiles with lines of the form:

    YYYYMMDDTHHmmZ lead_time_mins threshold_mmh hits misses false_alarms no_det

    Calculate binary statistics (POD, FAR, CSI) with threshold and lead time.
    Make plot of POD vs success ratio (1-FAR), with CSI background contours, and
    a line for each of the three models at different thresholds.  Each plot is
    for a single lead time.

    Args:
        infiles (list of str):
            List of files to read
        plotdir (str):
            Full path to directory to save plots
        startdate (int or None):
            Date to start calculation in YYYYMMDD format
        enddate (int or None):
            Date to end calculation in YYYYMMDD format
    """
    # set start and end times for item filtering
    start = startdate
    end = enddate
    if start is None:
        start = 0
    if end is None:
        end = 20500101

    # sort input files by model
    file_lists = {}
    for name in infiles:
        model = get_model(name)
        if model in file_lists:
            file_lists[model].append(name)
        else:
            file_lists[model] = [name]

    stats_dicts = {}
    for model in file_lists:
        counts_dict = accumulate_count_files(file_lists[model], start, end)
        stats_dicts[model] = StatsDict(counts_dict)

    outname = os.path.join(plotdir, '4D_1hr.png')
    make_4D_plot(stats_dicts, 60, outname)

    outname = os.path.join(plotdir, '4D_2hr.png')
    make_4D_plot(stats_dicts, 120, outname)

    outname = os.path.join(plotdir, '4D_3hr.png')
    make_4D_plot(stats_dicts, 180, outname)

    outname = os.path.join(plotdir, '4D_4hr.png')
    make_4D_plot(stats_dicts, 240, outname)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', type=str, nargs='+', help='List of textfiles to read')
    parser.add_argument('--plotdir', type=str, help='Output directory to save plots')
    parser.add_argument('--startdate', type=int, default=None)
    parser.add_argument('--enddate', type=int, default=None)
    args = parser.parse_args()

    main(args.infiles, args.plotdir, args.startdate, args.enddate)
