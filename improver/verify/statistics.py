"""Module to calculate and plot binary statistics from counts"""

import numpy as np
from datetime import timedelta

from improver.utilities.temporal import cycletime_to_datetime, datetime_to_cycletime
from improver.verify.parse_file import format_line, get_model


def calc_stats(hits, misses, false, no_det):
    """Calculate binary statistics"""
    a, b, c, d = [float(x) for x in [hits, misses, false, no_det]]

    POD = a / (a + b)
    FAR = c / (a + c)
    CSI = a / (a + b + c)
    HSS = 2*(a*d - b*c) / ((a+c)*(c+d) + (a+b)*(b+d))

    return POD, FAR, CSI, HSS


class StatsDict:
    """Dictionary wrapper with accessors to simplify plotting by threshold
    and lead time"""

    def __init__(self, counts):
        """Creates a new dictionary containing binary statistics by
        leadtime and threshold"""
        self.data = {}
        for lt in counts:
            self.data[lt] = {}
            for thresh in counts[lt]:
                self.data[lt][thresh] = {}
                pod, far, csi, hss = calc_stats(
                    counts[lt][thresh]['hits'],
                    counts[lt][thresh]['misses'],
                    counts[lt][thresh]['false'],
                    counts[lt][thresh]['no_det'],
                )
                self._set_pod(lt, thresh, pod)
                self._set_far(lt, thresh, far)
                self._set_csi(lt, thresh, csi)
                self._set_hss(lt, thresh, hss)

    def _set_pod(self, lt, thresh, pod):
        self.data[lt][thresh]['POD'] = pod

    def _set_far(self, lt, thresh, far):
        self.data[lt][thresh]['FAR'] = far

    def _set_csi(self, lt, thresh, csi):
        self.data[lt][thresh]['CSI'] = csi

    def _set_hss(self, lt, thresh, hss):
        self.data[lt][thresh]['HSS'] = hss

    @staticmethod
    def _sort_by_x(x, skill):
        sorted_lists = sorted(zip(x, skill))
        x = [item for item, _ in sorted_lists]
        skill = [item for _, item in sorted_lists]    
        return x, skill    

    def trend_with_leadtime(self, thresh, stat):
        """Returns a statistic with lead time for a given threshold"""
        leadtimes = []
        skill = []
        for lt in self.data:
            leadtimes.append(lt)
            skill.append(self.data[lt][thresh][stat])
        return self._sort_by_x(leadtimes, skill)

    def trend_with_threshold(self, leadtime, stat):
        """Returns a statistic with threshold for a given lead time"""
        thresholds = []
        skill = []
        for thresh in self.data[leadtime]:
            thresholds.append(thresh)
            skill.append(self.data[leadtime][thresh][stat])
        return self._sort_by_x(thresholds, skill)


class SkillCrossover:
    """Deep dictionary containing trends of CSI with lead time for each model,
    in order to calculate nowcast / UKV crossovers"""

    def __init__(self, infiles, startdate, enddate, verbose_read=True):
        """Read counts straight from files, retaining cycle association

        Args:
            infiles (list of str)
            startdate (int)
                Date in YYYYMMDD format, or 0
            enddate (int)
                Date in YYYYMMDD format
            verbose_read (bool):
                If True, print out reasons for removing certain cycles in
                data checking
        """
        self.verbose = verbose_read
        self.nowcast = None
        self.data = {}
        for datafile in infiles:
            # find out which model this file is associated with
            model = get_model(datafile)
            print(f'Reading {model} data from {datafile}')
            nowcast = False
            if model != 'UKV':
                nowcast = True
                if self.nowcast is None:
                    self.nowcast = model

            with open(datafile) as dtf:
                line = dtf.readline()
                while line:
                    vt, lt, thresh, hits, misses, false, no_det = format_line(line)
                    cycle = self._get_cycle(vt, lt)
                    day = int(cycle[:8])

                    # read only hourly cycles
                    if day >= startdate and day <= enddate and self._is_hourly(cycle):
                        # initialise dictionary item for this cycle
                        self._initialise_cycle(cycle, model)

                        # crude count of amount of rain in input radar using nowcast at 15 minutes
                        if nowcast and lt == 15 and np.isclose(thresh, 0.03):
                            self._wet_dry_count(cycle, hits, misses, false, no_det)
                    
                        # append data to lists (assumes thresholds complete and in ascending order)
                        if np.isclose(thresh, 0.03):
                            self.data[cycle][model]['leadtimes'].append(lt)
                            self.data[cycle][model]['CSI_0'].append(self._csi(hits, misses, false))
                        elif np.isclose(thresh, 1):
                            self.data[cycle][model]['CSI_1'].append(self._csi(hits, misses, false))

                    line = dtf.readline()

        # check all entries in self.data have required info
        print(f'Read {len(self.data)} cycles into dict')
        self._check_data()
        print(f'Retained {len(self.data)} cycles for analysis')


    @staticmethod
    def _get_cycle(vt, lt):
        """Get forecast cycle that generated this line in YYYYMMDDTHHMMZ format"""
        vt_datetime = cycletime_to_datetime(vt)
        cycle_datetime = vt_datetime - timedelta(seconds=lt*60)
        return datetime_to_cycletime(cycle_datetime)

    @staticmethod
    def _is_hourly(cycle):
        """Return True if cycletime is on-hour: YYYYMMDDTHHMMZ"""
        if cycle[-3:] == "00Z":
            return True
        return False

    def _initialise_cycle(self, cycle, model):
        """Add new cycle and / or model to data dictionary"""
        if cycle not in self.data:
            self.data[cycle] = {}
        if model not in self.data[cycle]:
            self.data[cycle][model] = {'leadtimes': [], 'CSI_0': [], 'CSI_1': []}

    def _wet_dry_count(self, cycle, hits, misses, false, no_det):
        """Count number of wet and dry pixels in initialising radar image"""
        if 'wet_pixels' in self.data[cycle]:
            raise UserWarning(f'Wet / dry counts already defined for {cycle}')
        else:
            self.data[cycle]['wet_pixels'] = hits + misses
            self.data[cycle]['dry_pixels'] = false + no_det

    @staticmethod
    def _csi(hits, misses, false):
        """Calculate CSI"""
        if float(hits + misses + false) > 0:
            return float(hits) / float(hits + misses + false)
        return np.nan

    def _check_data(self):
        """Validate each entry in data dict"""

        def unexpected_keys(item, keys, expected):
            return f'{item} has {keys}, expected {expected}'

        expected_keys = {'wet_pixels', 'dry_pixels', 'UKV', self.nowcast}
        model_keys = {'leadtimes', 'CSI_0', 'CSI_1'}
        remove_cycles = []

        for cycle in self.data:
            if self.data[cycle].keys() != expected_keys:
                if self.verbose:
                    print(unexpected_keys(cycle, self.data[cycle].keys(), expected_keys),
                          '- marked cycle for removal')
                remove_cycles.append(cycle)
                continue

            for model in ['UKV', self.nowcast]:
                if self.data[cycle][model].keys() != model_keys:
                    raise ValueError(
                        unexpected_keys(
                            self.data[cycle][model], self.data[cycle][model].keys(), model_keys
                        )
                    )

                missing = self._check_leadtimes(
                    model, self.data[cycle][model]['leadtimes']
                )
                if missing:
                    if self.verbose:
                        print(f'{cycle} {model} missing lead times {missing} '
                              '- marked cycle for removal')
                    remove_cycles.append(cycle)

        for cycle in set(remove_cycles):
            self.data.pop(cycle)

    def _check_leadtimes(self, model, leadtimes):
        """Check for missing leadtimes"""
        expected_leadtimes = {
            'UKV': np.arange(60, 361, 60),
            self.nowcast: np.arange(15, 361, 15)
        }
        missing_leadtimes = set(expected_leadtimes[model]) - set(leadtimes)
        return missing_leadtimes

    def calculate_crossovers(self, zero_threshold=True):
        """From dictionary, calculate the crossover skill lead time and value for each
        cycle.  If CSI is invalid, filter out.

        Returns:
            nwet (list of int):
                Number of wet pixels in input radar image
            pwet (list of float):
                Proportion of wet pixels in input radar image (range 0-1)
            crossover_time (list of float):
                Interpolated time at which nowcast skill dips below UKV, in minutes
            crossover_csi (list of float):
                Interpolated CSI at which nowcast skill dips below UKV.  If any of
                the input CSI values are invalid, meaning this crossover cannot be
                calculated, no entry is returned.  This filters out "no rain" cases.
            zero_threshold (bool):
                If True, calculate crossover time and CSI for the "zero" (0.03 mm/h)
                threshold.  If False, calculate for 1 mm/h.
        """
        nwet = []
        pwet = []
        crossover_time = []
        crossover_csi = []

        for cycle in self.data:
            csi_index = 'CSI_0' if zero_threshold else 'CSI_1'

            nc_lt = self.data[cycle][self.nowcast]['leadtimes']
            nc_csi = self.data[cycle][self.nowcast][csi_index]
            nc_dict = {lt: csi for lt, csi in zip(nc_lt, nc_csi)}

            ukv_lt = self.data[cycle]['UKV']['leadtimes']
            ukv_csi = self.data[cycle]['UKV'][csi_index]
            ukv_dict = {lt: csi for lt, csi in zip(ukv_lt, ukv_csi)}

            # exclude timeseries containing nans
            if (np.nan in self.data[cycle][self.nowcast][csi_index] or
                    np.nan in self.data[cycle]['UKV'][csi_index]):
                continue

            # find first lead time at which UKV skill exceeds nowcast
            cross_found = False
            for lt in ukv_lt:
                if nc_dict[lt] <= ukv_dict[lt]:

                    # if we hit at the first lead time, go back until we find a
                    # nowcast with higher skill than the UKV at T+1
                    if lt == 60:
                        tcross = None
                        for nclt in [45, 30, 15]:
                            if nc_dict[nclt] > ukv_dict[60]:
                                tcross = nclt
                        if tcross is None:
                            tcross = 15
                        csi_cross = ukv_dict[60]
                        cross_found = True
                        break

                    # look back over the previous hour to pinpoint crossover
                    ukv0 = ukv_dict[lt-60]
                    ukv1 = ukv_dict[lt]
                    diff = ukv1 - ukv0
                    ukv_interp = []
                    nc_interp = []
                    for i in range(5):
                        ukv_interp.append(ukv0 + i*diff/4.)
                        nc_interp.append(nc_dict[lt-(4-i)*15])

                    for i in range(4):
                        if nc_interp[i+1] <= ukv_interp[i+1]:
                            # interpolate linearly over 15 minute timestep:
                            # nc_csi = at + b ; ukv_csi = ct + d
                            a = (nc_interp[i+1] - nc_interp[i]) / 15.
                            b = nc_interp[i]
                            c = (ukv_interp[i+1] - ukv_interp[i]) / 15.
                            d = ukv_interp[i]

                            dt_cross = (d - b) / (a - c)
                            csi_cross = a*dt_cross + b
                            t_cross = dt_cross + (lt - 60 + i*15)

                            cross_found = True
                            break

                    break

            if cross_found:
                nwet.append(self.data[cycle]['wet_pixels'])
                pwet.append(float(nwet[-1]) / float(nwet[-1] + self.data[cycle]['dry_pixels']))
                crossover_time.append(t_cross)
                crossover_csi.append(csi_cross)

        return (np.array(nwet), np.array(pwet), np.array(crossover_time), np.array(crossover_csi))



