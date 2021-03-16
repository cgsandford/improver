# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017-2021 Met Office.
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
"""Unit tests for the MOMetadataInterpreter plugin"""

import pytest
from iris.coords import CellMethod
from iris.util import promote_aux_coord_to_dim_coord

from improver_tests.developer_tools import (
    ensemble_fixture,
    interpreter_fixture,
    percentile_fixture,
    probability_above_fixture,
    probability_below_fixture,
    snow_level_fixture,
    spot_fixture,
    wind_direction_fixture,
    wxcode_fixture,
)


def test_probabilities_above(probability_above_cube, interpreter):
    """Test interpretation of probability of temperature above threshold
    from UKV"""
    interpreter.run(probability_above_cube)
    assert interpreter.prod_type == "gridded"
    assert interpreter.field_type == "probabilities"
    assert interpreter.diagnostic == "air temperature"
    assert interpreter.relative_to_threshold == "greater than"
    assert not interpreter.methods
    assert interpreter.post_processed == "some"
    assert interpreter.model == "UKV"
    assert not interpreter.blended
    assert not interpreter.warning_string


def test_probabilities_below(blended_probability_below_cube, interpreter):
    """Test interpretation of blended probability of max temperature in hour
    below threshold"""
    interpreter.run(blended_probability_below_cube)
    assert interpreter.prod_type == "gridded"
    assert interpreter.field_type == "probabilities"
    assert interpreter.diagnostic == "air temperature"
    assert interpreter.relative_to_threshold == "less than"
    assert interpreter.methods == " maximum over time"
    assert interpreter.post_processed == "some"
    assert interpreter.model == "UKV, MOGREPS-UK"
    assert interpreter.blended
    assert not interpreter.warning_string


def test_percentiles(wind_gust_percentile_cube, interpreter):
    """Test interpretation of wind gust percentiles from MOGREPS-UK"""
    interpreter.run(wind_gust_percentile_cube)
    assert interpreter.prod_type == "gridded"
    assert interpreter.field_type == "percentiles"
    assert interpreter.diagnostic == "wind gust"
    assert interpreter.relative_to_threshold is None
    assert not interpreter.methods
    assert interpreter.post_processed == "no"
    assert interpreter.model == "MOGREPS-UK"
    assert not interpreter.blended
    assert not interpreter.warning_string


def test_realizations(ensemble_cube, interpreter):
    """Test interpretation of temperature realizations from MOGREPS-UK"""
    interpreter.run(ensemble_cube)
    assert interpreter.prod_type == "gridded"
    assert interpreter.field_type == "realizations"
    assert interpreter.diagnostic == "air temperature"
    assert interpreter.relative_to_threshold is None
    assert not interpreter.methods
    assert interpreter.post_processed == "no"
    assert interpreter.model == "MOGREPS-UK"
    assert not interpreter.blended
    assert not interpreter.warning_string


def test_snow_level(snow_level_cube, interpreter):
    """Test interpretation of a diagnostic cube with "probability" in the name,
    which is not designed for blending with other models"""
    interpreter.run(snow_level_cube)
    assert interpreter.prod_type == "gridded"
    assert interpreter.field_type == "realizations"
    assert (
        interpreter.diagnostic == "probability of snow falling level below ground level"
    )
    assert interpreter.relative_to_threshold is None
    assert not interpreter.methods
    assert interpreter.post_processed == "some"
    assert interpreter.model is None
    assert not interpreter.blended
    assert not interpreter.warning_string


def test_spot_median(blended_spot_median_cube, interpreter):
    """Test interpretation of spot median"""
    interpreter.run(blended_spot_median_cube)
    assert interpreter.prod_type == "spot"
    assert interpreter.field_type == "percentiles"
    assert interpreter.diagnostic == "air temperature"
    assert interpreter.relative_to_threshold is None
    assert not interpreter.methods
    assert interpreter.post_processed == "some"
    assert interpreter.model == "UKV, MOGREPS-UK"
    assert interpreter.blended
    assert not interpreter.warning_string


def test_error_invalid_probability_name(probability_above_cube, interpreter):
    """Test error raised if probability cube name is invalid"""
    probability_above_cube.rename("probability_air_temperature_is_above_threshold")
    with pytest.raises(ValueError, match="is not a valid probability cube name"):
        interpreter.run(probability_above_cube)


def test_error_no_threshold_coordinate(probability_above_cube, interpreter):
    """Test error raised if probability cube has no threshold coordinate"""
    cube = next(probability_above_cube.slices_over("air_temperature"))
    cube.remove_coord("air_temperature")
    with pytest.raises(ValueError, match="no coord with var_name='threshold' found"):
        interpreter.run(cube)


def test_error_invalid_threshold_name(probability_above_cube, interpreter):
    """Test error raised if threshold coordinate name does not match cube name"""
    probability_above_cube.coord("air_temperature").rename("screen_temperature")
    probability_above_cube.coord("screen_temperature").var_name = "threshold"
    with pytest.raises(ValueError, match="expected threshold coord.*incorrect name"):
        interpreter.run(probability_above_cube)


def test_error_no_threshold_var_name(probability_above_cube, interpreter):
    """Test error raised if threshold coordinate does not have var_name='threshold'"""
    probability_above_cube.coord("air_temperature").var_name = None
    with pytest.raises(ValueError, match="does not have var_name='threshold'"):
        interpreter.run(probability_above_cube)


def test_error_inconsistent_relative_to_threshold(probability_above_cube, interpreter):
    """Test error raised if the spp__relative_to_threshold attribute is inconsistent
    with the cube name"""
    probability_above_cube.coord("air_temperature").attributes[
        "spp__relative_to_threshold"
    ] = "less_than"
    with pytest.raises(
        ValueError, match="name.*above.*is not consistent with.*less_than"
    ):
        interpreter.run(probability_above_cube)


def test_multiple_error_concatenation(probability_above_cube, interpreter):
    """Test multiple errors are concatenated and returned correctly in a readable
    format"""
    probability_above_cube.coord("air_temperature").attributes[
        "spp__relative_to_threshold"
    ] = "less_than"
    probability_above_cube.coord("air_temperature").var_name = None
    probability_above_cube.attributes["um_version"] = "irrelevant"
    msg = (
        ".*does not have var_name='threshold'.*\n"
        ".*name.*above.*is not consistent with.*less_than.*\n"
        "Attributes.*include one or more forbidden values.*"
    )
    with pytest.raises(ValueError, match=msg):
        interpreter.run(probability_above_cube)


def test_error_wrong_percentile_name_units(wind_gust_percentile_cube, interpreter):
    """Test incorrect percentile coordinate name and units"""
    wind_gust_percentile_cube.coord("percentile").units = "1"
    wind_gust_percentile_cube.coord("percentile").rename("percentile_over_realization")
    msg = (
        ".*should have name percentile, has percentile_over_realization\n"
        ".*should have units of %, has 1"
    )
    with pytest.raises(ValueError, match=msg):
        interpreter.run(wind_gust_percentile_cube)


def test_error_missing_required_attribute(wind_gust_percentile_cube, interpreter):
    """Test error raised when a mandatory attribute is missing"""
    wind_gust_percentile_cube.attributes.pop("title")
    with pytest.raises(ValueError, match="missing.*mandatory attributes"):
        interpreter.run(wind_gust_percentile_cube)


def test_error_forbidden_attributes(wind_gust_percentile_cube, interpreter):
    """Test error raised when a forbidden attribute is present"""
    wind_gust_percentile_cube.attributes["mosg__forecast_run_duration"] = "wrong"
    with pytest.raises(ValueError, match="Attributes.*include.*forbidden values"):
        interpreter.run(wind_gust_percentile_cube)


def test_warning_unexpected_attributes(wind_gust_percentile_cube, interpreter):
    """The IMPROVER metadata standard is minimal - so while we don't forbid extra
    attributes, we raise a warning if it's not one we recognise as adding useful
    information"""
    wind_gust_percentile_cube.attributes["enigma"] = "intriguing and mysterious details"
    interpreter.run(wind_gust_percentile_cube)
    assert interpreter.warning_string == (
        "dict_keys(['source', 'title', 'institution', 'mosg__model_configuration', "
        "'wind_gust_diagnostic', 'enigma']) include unexpected attributes. "
        "Please check the standard to ensure this is valid.\n"
    )


def test_error_inconsistent_model_attributes(ensemble_cube, interpreter):
    """Test error raised when the model ID and title attributes are inconsistent"""
    ensemble_cube.attributes["mosg__model_configuration"] = "uk_det"
    with pytest.raises(ValueError, match="Title.*is inconsistent with model ID"):
        interpreter.run(ensemble_cube)


def test_improver_in_title(ensemble_cube, interpreter):
    """Test that an unblended title including 'IMPROVER' rather than a model name
    does not cause an error, and that the source model is still identified via the
    appropriate attribute"""
    ensemble_cube.attributes["title"].replace("MOGREPS-UK", "IMPROVER")
    interpreter.run(ensemble_cube)
    assert interpreter.model == "MOGREPS-UK"


def test_error_forbidden_cell_method(blended_probability_below_cube, interpreter):
    """Test error raised when a forbidden cell method is present"""
    blended_probability_below_cube.add_cell_method(
        CellMethod(method="mean", coords="forecast_reference_time")
    )
    with pytest.raises(ValueError, match="Non-standard cell method"):
        interpreter.run(blended_probability_below_cube)


def test_error_missing_spot_coords(blended_spot_median_cube, interpreter):
    """Test error raised if a spot cube doesn't have all the expected metadata"""
    blended_spot_median_cube.remove_coord("altitude")
    with pytest.raises(ValueError, match="Missing one or more coordinates"):
        interpreter.run(blended_spot_median_cube)


def test_error_missing_coords(probability_above_cube, interpreter):
    """Test error raised if an unblended cube doesn't have the expected time
    coordinates"""
    probability_above_cube.remove_coord("forecast_period")
    with pytest.raises(ValueError, match="Missing one or more coordinates"):
        interpreter.run(probability_above_cube)


def test_error_missing_blended_coords(blended_probability_below_cube, interpreter):
    """Test error raised if a blended cube doesn't have the expected time
    coordinates"""
    blended_probability_below_cube.remove_coord("blend_time")
    with pytest.raises(ValueError, match="Missing one or more coordinates"):
        interpreter.run(blended_probability_below_cube)


def test_error_time_coordinate_units(probability_above_cube, interpreter):
    """Test error raised if time coordinate units do not match the IMPROVER standard"""
    probability_above_cube.coord("forecast_period").convert_units("hours")
    with pytest.raises(ValueError, match="does not have required units"):
        interpreter.run(probability_above_cube)


def test_weather_code_success(wxcode_cube, interpreter):
    """Test interpretation of weather code field"""
    interpreter.run(wxcode_cube)
    assert interpreter.diagnostic == "weather code"
    assert interpreter.model == "UKV, MOGREPS-UK"
    assert interpreter.blended


def test_error_weather_code_unexpected_cell_methods(wxcode_cube, interpreter):
    """Test error if exception cubes have a cell method that would usually be
    permitted"""
    wxcode_cube.add_cell_method(CellMethod(method="maximum", coords="time"))
    with pytest.raises(ValueError, match="Unexpected cell methods"):
        interpreter.run(wxcode_cube)


def test_error_weather_code_missing_attribute(wxcode_cube, interpreter):
    """Test error when weather code required attributes are missing"""
    wxcode_cube.attributes.pop("weather_code")
    with pytest.raises(ValueError, match="missing .* required values"):
        interpreter.run(wxcode_cube)


def test_error_wind_gust_missing_attribute(wind_gust_percentile_cube, interpreter):
    """Test error when a wind gust percentile cube is missing a required attribute"""
    wind_gust_percentile_cube.attributes.pop("wind_gust_diagnostic")
    with pytest.raises(ValueError, match="missing .* required values"):
        interpreter.run(wind_gust_percentile_cube)


def test_warning_unexpected_attribute_wrong_diagnostic(
    wind_gust_percentile_cube, interpreter
):
    """Test a warning is raised if a known diagnostic-specific attribute is included
    on an unexpected diagnostic"""
    wind_gust_percentile_cube.rename("wind_speed")
    interpreter.run(wind_gust_percentile_cube)
    assert interpreter.warning_string == (
        "dict_keys(['source', 'title', 'institution', 'mosg__model_configuration', "
        "'wind_gust_diagnostic']) include unexpected attributes. "
        "Please check the standard to ensure this is valid.\n"
    )


def test_wind_direction_success(wind_direction_cube, interpreter):
    """Test interpretation of wind direction field with mean over realizations
    cell method"""
    interpreter.run(wind_direction_cube)
    assert interpreter.diagnostic == "wind from direction"
    assert interpreter.model == "MOGREPS-UK"
    assert not interpreter.blended


def test_error_wind_direction_unexpected_cell_methods(wind_direction_cube, interpreter):
    """Test error if exception cubes have a cell method that would usually be
    permitted"""
    wind_direction_cube.add_cell_method(CellMethod(method="maximum", coords="time"))
    with pytest.raises(ValueError, match="Unexpected cell methods"):
        interpreter.run(wind_direction_cube)
