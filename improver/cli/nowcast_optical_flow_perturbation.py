#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2020 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Script to calculate optical flow advection velocities as perturbations
from a previous estimate"""

from improver import cli

# Creates the value_converter that clize needs.
inputadvection = cli.create_constrained_inputcubelist_converter(
    "precipitation_advection_x_velocity", "precipitation_advection_y_velocity",
)


@cli.clizefy
@cli.with_output
def process(
    current_obs: cli.inputcube,
    previous_forecast: cli.inputcube,
    previous_advection: inputadvection,
    orographic_enhancement: cli.inputcube,
    *,
    forecast_period=15,
):
    """Calculate optical flow components as a perturbation from the previous
    advection components, using the difference between a current observation
    and forecast from the previous time step.

    Args:
        current_obs (iris.cube.Cube):
            Cube containing latest radar observation
        previous_forecast (iris.cube.Cube):
            Cube containing advection nowcast for this time, created at an
            earlier timestep
        previous_advection (iris.cube.CubeList):
            Advection velocities in the x- and y- directions used to generate
            the previous forecast
        orographic_enhancement (iris.cube.Cube):
            Cube containing orographic enhancement for this timestep
        forecast_period (int):
            Forecast period of previous forecast, in minutes.  Used to extract
            a forecast from a cube that may contain multiple lead times.

    Returns:
        iris.cube.CubeList:
            List of the umean and vmean cubes.

    """
    from iris import Constraint
    from improver.nowcasting.optical_flow import (
        generate_advection_velocities_as_perturbations,
    )

    previous_forecast.coord("forecast_period").convert_units("seconds")
    previous_forecast = previous_forecast.extract(
        Constraint(forecast_period=60 * forecast_period)
    )

    advection_velocities = generate_advection_velocities_as_perturbations(
        current_obs, previous_forecast, previous_advection, orographic_enhancement
    )

    return advection_velocities