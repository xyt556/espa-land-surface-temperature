#! /usr/bin/env python

'''
    File: lst_generate_products.py

    Purpose: Runs all of the sub-applications required to generate LST
             products.

    Project: Land Satellites Data Systems Science Research and Development
             (LSRD) at the USGS EROS

    License: NASA Open Source Agreement 1.3
'''

import os
import sys
import logging
import glob
import shutil
from argparse import ArgumentParser
from ConfigParser import ConfigParser

import lst_utilities as util

from lst_grid_points import (GRID_POINT_HEADER_NAME,
                             GRID_POINT_BINARY_NAME)

from lst_build_modtran_input import PARAMETERS

import build_lst_data


def retrieve_command_line_arguments():
    """Read arguments from the command line

    Returns:
        args <arguments>: The arguments read from the command line
    """

    parser = ArgumentParser(description='Runs MODTRAN on a pre-determined'
                                        ' set of points')

    parser.add_argument('--version',
                        action='version',
                        version=util.Version.version_text())

    parser.add_argument('--xml',
                        action='store', dest='xml_filename',
                        required=False, default=None,
                        help='The XML metadata file to use')

    parser.add_argument('--keep-intermediate-data',
                        action='store_true', dest='intermediate',
                        required=False, default=False,
                        help='Keep any intermediate products generated')

    parser.add_argument('--keep-temporary-data',
                        action='store_true', dest='temporary',
                        required=False, default=False,
                        help='Keep any temporary files generated')

    parser.add_argument('--debug',
                        action='store_true', dest='debug',
                        required=False, default=False,
                        help='Output debug messages and/or keep debug data')

    args = parser.parse_args()

    # Verify that the --xml parameter was specified
    if args.xml_filename is None:
        raise Exception('--xml must be specified on the command line')

    return args


def get_cfg_file_path(filename):
    """Build the full path to the config file

    Args:
        filename <str>: The name of the file to append to the full path

    Raises:
        Exception(<str>)
    """

    # Use the users home directory as the base source directory for
    # configuration
    if 'HOME' not in os.environ:
        raise Exception('[HOME] not found in environment')
    home_dir = os.environ.get('HOME')

    # Build the full path to the configuration file
    config_path = os.path.join(home_dir, '.usgs', 'espa', filename)

    return config_path


def retrieve_cfg(cfg_filename):
    """Retrieve the configuration for the cron

    Args:
        cfg_filename <str>: Name of the configuration file

    Returns:
        cfg <ConfigParser>: Configuration for ESPA cron

    Raises:
        Exception(<str>)
    """

    # Build the full path to the configuration file
    config_path = get_cfg_file_path(cfg_filename)

    if not os.path.isfile(config_path):
        raise Exception('Missing configuration file [{}]'
                        .format(config_path))

    # Create the object and load the configuration
    cfg = ConfigParser()
    cfg.read(config_path)

    return cfg


def determine_grid_points(xml_filename, data_path, debug):
    """Determines the grid points to utilize

    Args:
        xml_filename <str>: XML metadata filename
        data_path <str>: Directory for LST data files
        debug <bool>: Debug logging and processing
    """

    output = ''
    try:
        cmd = ['lst_determine_grid_points.py',
               '--xml', xml_filename,
               '--data_path', data_path]

        if debug:
            cmd.append('--debug')

        output = util.System.execute_cmd(' '.join(cmd))
    finally:
        if len(output) > 0:
            logger = logging.getLogger(__name__)
            logger.info(output)


def extract_auxiliary_narr_data(xml_filename, aux_path, debug):
    """Determines the grid points to utilize

    Args:
        xml_filename <str>: XML metadata filename
        aux_path <str>: Directory for the auxiliary data files
        debug <bool>: Debug logging and processing
    """

    output = ''
    try:
        cmd = ['lst_extract_auxiliary_narr_data.py',
               '--xml', xml_filename,
               '--aux_path', aux_path]

        if debug:
            cmd.append('--debug')

        output = util.System.execute_cmd(' '.join(cmd))
    finally:
        if len(output) > 0:
            logger = logging.getLogger(__name__)
            logger.info(output)


def build_modtran_input(xml_filename, data_path, debug):
    """Determines the grid points to utilize

    Args:
        xml_filename <str>: XML metadata filename
        data_path <str>: Directory for LST data files
        debug <bool>: Debug logging and processing
    """

    output = ''
    try:
        cmd = ['lst_build_modtran_input.py',
               '--xml', xml_filename,
               '--data_path', data_path]

        if debug:
            cmd.append('--debug')

        output = util.System.execute_cmd(' '.join(cmd))
    finally:
        if len(output) > 0:
            logger = logging.getLogger(__name__)
            logger.info(output)


def generate_emissivity_products(xml_filename, server_name, server_path,
                                 debug):
    """Generate the required Emissivity products

    Args:
        xml_filename <str>: XML metadata filename
        server_name <str>: Name of the ASTER GED server
        server_path <str>: Path on the ASTER GED server
        debug <bool>: Debug logging and processing
    """

    output = ''
    try:
        cmd = ['estimate_landsat_emissivity.py',
               '--xml', xml_filename,
               '--aster-ged-server-name', server_name,
               '--aster-ged-server-path', server_path]

        if debug:
            cmd.append('--debug')

        output = util.System.execute_cmd(' '.join(cmd))
    finally:
        if len(output) > 0:
            logger = logging.getLogger(__name__)
            logger.info(output)


def run_modtran(modtran_data_path, process_count, debug):
    """Determines the grid points to utilize

    Args:
        modtran_data_path <str>: Directory for the MODTRAN 'DATA' files
        process_count <str>: Number of processes to use
        debug <bool>: Debug logging and processing
    """

    output = ''
    try:
        cmd = ['lst_run_modtran.py',
               '--modtran_data_path', modtran_data_path,
               '--process_count', process_count]

        if debug:
            cmd.append('--debug')

        output = util.System.execute_cmd(' '.join(cmd))
    finally:
        if len(output) > 0:
            logger = logging.getLogger(__name__)
            logger.info(output)


def cleanup_temporary_data():
    """Cleanup/remove all the LST temporary files and directories 
    """

    GRID_POINT_ELEVATION_NAME = 'grid_elevations.txt'
    MODTRAN_ELEVATION_NAME = 'modtran_elevations.txt'
    ATMOSPHERE_PARAMETERS_NAME = 'atmospheric_parameters.txt'
    USED_POINTS_NAME = 'used_points.txt'
    EMISSIVITY_HEADER_NAME = '*_emis.img.aux.xml'

    # File cleanup
    cleanup_list = [GRID_POINT_HEADER_NAME, GRID_POINT_BINARY_NAME, 
                    GRID_POINT_ELEVATION_NAME, MODTRAN_ELEVATION_NAME,
                    ATMOSPHERE_PARAMETERS_NAME, USED_POINTS_NAME]

    for filename in cleanup_list:
        if os.path.exists(filename):
            os.unlink(filename)

    # Cleanup file pattern.
    for filename in glob.glob(EMISSIVITY_HEADER_NAME):
        os.unlink(filename)

    # Directory cleanup
    for directory in glob.glob('[0-9][0-9][0-9]_[0-9][0-9][0-9]_'
                               '[0-9][0-9][0-9]_[0-9][0-9][0-9]'):
        shutil.rmtree(directory)

    for directory in PARAMETERS:
        if os.path.exists(directory):
            shutil.rmtree(directory)


def cleanup_intermediate_bands():
    """Cleanup/remove the intermediate bands used to make the LST band
    """

    # File cleanup
    EMISSIVITY_PATTERN = '*_landsat_emis.*'
    ATMOSPHERIC_TRANSMITTANCE_PATTERN = '*_lst_atmospheric_transmittance.*'
    DOWNWELLED_RADIANCE_PATTERN = '*_lst_downwelled_radiance.*'
    UPWELLED_RADIANCE_PATTERN = '*_lst_upwelled_radiance.*'
    THERMAL_RADIANCE_PATTERN = '*_lst_thermal_radiance.*'

    # Cleanup file patterns.
    cleanup_list = [EMISSIVITY_PATTERN, ATMOSPHERIC_TRANSMITTANCE_PATTERN,
                    DOWNWELLED_RADIANCE_PATTERN, UPWELLED_RADIANCE_PATTERN,
                    THERMAL_RADIANCE_PATTERN]
    for pattern in cleanup_list:
        for filename in glob.glob(pattern):
            os.unlink(filename)


PROC_CFG_FILENAME = 'processing.conf'


def main():
    """Main processing for building the points list
    """

    # Command Line Arguments
    args = retrieve_command_line_arguments()

    # Check logging level
    logging_level = logging.INFO
    if args.debug:
        logging_level = logging.DEBUG

    # Setup the default logger format and level.  Log to STDOUT.
    logging.basicConfig(format=('%(asctime)s.%(msecs)03d %(process)d'
                                ' %(levelname)-8s'
                                ' %(filename)s:%(lineno)d:'
                                '%(funcName)s -- %(message)s'),
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging_level,
                        stream=sys.stdout)
    logger = logging.getLogger(__name__)

    logger.info('*** Begin LST Generate Products ***')

    # Retrieve the processing configuration
    proc_cfg = retrieve_cfg(PROC_CFG_FILENAME)

    # Determine number of process to use
    process_count = proc_cfg.get('processing', 'omp_num_threads')

    # Determine LST data locations
    data_path = proc_cfg.get('processing', 'lst_data_path')

    # Determine NARR data locations
    aux_path = proc_cfg.get('processing', 'lst_aux_path')

    # Determine MODTRAN 'DATA' location
    modtran_data_path = proc_cfg.get('processing', 'modtran_data_path')

    # Determine the server name and path to get the ASTER data from
    server_name = proc_cfg.get('processing', 'aster_ged_server_name')
    server_path = proc_cfg.get('processing', 'aster_ged_server_path')

    # -------------- Generate the products --------------
    determine_grid_points(xml_filename=args.xml_filename,
                          data_path=data_path,
                          debug=args.debug)

    extract_auxiliary_narr_data(xml_filename=args.xml_filename,
                                aux_path=aux_path,
                                debug=args.debug)

    build_modtran_input(xml_filename=args.xml_filename,
                        data_path=data_path,
                        debug=args.debug)

    generate_emissivity_products(xml_filename=args.xml_filename,
                                 server_name=server_name,
                                 server_path=server_path,
                                 debug=args.debug)

    run_modtran(modtran_data_path=modtran_data_path,
                process_count=process_count,
                debug=args.debug)

    # Generate the thermal, upwelled, and downwelled radiance bands as well as
    # the atmospheric transmittance band
    cmd = ['lst_atmospheric_parameters', '--xml', args.xml_filename]
    if args.debug:
        cmd.append('--debug')

    cmd = ' '.join(cmd)
    output = ''
    try:
        logger.info('Calling [{0}]'.format(cmd))
        output = util.System.execute_cmd(cmd)
    except Exception:
        logger.error('Failed creating atmospheric parameters and generating '
                     'intermediate data')
        raise
    finally:
        if len(output) > 0:
            logger.info(output)

    # Generate Land Surface Temperature band
    try:
        current_processor = build_lst_data.BuildLSTData(
            xml_filename=args.xml_filename)
        current_processor.generate_data()
    except Exception:
        logger.error('Failed processing Land Surface Temperature')
        raise

    # Clean up files and directories according to user selections.
    if not args.temporary:
        cleanup_temporary_data()

    if not args.intermediate:
        cleanup_intermediate_bands()

    logger.info('*** LST Generate Products - Complete ***')


if __name__ == '__main__':
    main()
