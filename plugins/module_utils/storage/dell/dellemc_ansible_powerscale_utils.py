""" import powerscale sdk"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ApiException = None
HAS_POWERSCALE_SDK = False
isi_sdk = None
ISI_SDK_VERSION_9 = False
IMPORT_PKGS_FAIL = []
POWERSCALE_SDK_9_0_0 = "isi_sdk_9_0_0"
POWERSCALE_SDK_8_1_1 = "isi_sdk_8_1_1"

'''import urllib3'''
try:
    import urllib3

    urllib3.disable_warnings()
except ImportError:
    IMPORT_PKGS_FAIL.append("urllib3")

'''import dateutil'''
try:
    import dateutil.relativedelta
except ImportError:
    IMPORT_PKGS_FAIL.append("python-dateutil")

'''import pkg_resources'''
try:
    from pkg_resources import parse_version
    import pkg_resources
    HAS_PKG_RESOURCES = True
except ImportError:
    HAS_PKG_RESOURCES = False
    IMPORT_PKGS_FAIL.append("pkg_resources")

'''import importlib'''
try:
    import importlib
    HAS_IMPORTLIB = True
except ImportError:
    HAS_IMPORTLIB = False
    IMPORT_PKGS_FAIL.append("importlib")

import logging
import math
from decimal import Decimal
import re
import sys

''' Check and Get required libraries '''


def get_powerscale_sdk():
    return isi_sdk


'''
Check if required PowerScale SDK version is installed
'''


def powerscale_sdk_version_check():
    try:
        supported_version = False
        min_ver = '0.2.7'
        curr_version = pkg_resources.require(isi_sdk.__name__)[0].version
        unsupported_version_message =\
            "PowerScale sdk {0} is not supported by this module. Minimum " \
            "supported version is : {1} ".format(curr_version, min_ver)
        supported_version = parse_version(curr_version) >= parse_version(
            min_ver)

        isi_sdk_version = dict(
            supported_version=supported_version,
            unsupported_version_message=unsupported_version_message)

        return isi_sdk_version

    except Exception as e:
        unsupported_version_message = \
            "Unable to get the powerscale sdk version," \
            " failed with error {0} ".format(str(e))
        isi_sdk_version = dict(
            supported_version=False,
            unsupported_version_message=unsupported_version_message)
        return isi_sdk_version


'''
This method provides common access parameters required for the Ansible Modules on PowerScale
options:
  onefshost:
    description:
    - IP of the PowerScale OneFS host
    required: true
  port_no:
    decription:
    - The port number through which all the requests will be addressed by the OneFS host.
  verifyssl:
    description:
    - Boolean value to inform system whether to verify ssl certificate or not.
  api_user:
    description:
    - User name to access OneFS
  api_password:
    description:
    - password to access OneFS
'''


def get_powerscale_management_host_parameters():
    return dict(
        onefs_host=dict(type='str', required=True, no_log=True),
        verify_ssl=dict(choices=[True, False], type='bool', required=True),
        port_no=dict(type='str', default='8080', no_log=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True)
    )


'''
This method is to establish connection to PowerScale
using its SDK.
parameters:
  module_params - Ansible module parameters which contain below OneFS details
                 to establish connection on to OneFS
     - onefshost: IP of OneFS host.
     - verifyssl: Boolean value to inform system whether to verify ssl certificate or not.
     - port_no: The port no of the OneFS host.
     - username:  Username to access OneFS
     - password: Password to access OneFS
returns configuration object
'''


def get_powerscale_connection(module_params):
    if HAS_POWERSCALE_SDK:
        conn = isi_sdk.Configuration()
        if module_params['port_no'] is not None:
            conn.host = module_params['onefs_host'] + ":" + module_params[
                'port_no']
        else:
            conn.host = module_params['onefs_host']
        conn.verify_ssl = module_params['verify_ssl']
        conn.username = module_params['api_user']
        conn.password = module_params['api_password']
        api_client = isi_sdk.ApiClient(conn)
        return api_client


'''
This method is to initialize logger and return the logger object
parameters:
     - module_name: Name of module to be part of log message.
     - log_file_name: name of the file in which the log meessages get appended.
     - log_devel: log level.
returns logger object
'''


def get_logger(module_name, log_file_name='dellemc_ansible_provisioning.log',
               log_devel=logging.INFO):
    FORMAT = '%(asctime)-15s %(filename)s %(levelname)s : %(message)s'
    logging.basicConfig(filename=log_file_name, format=FORMAT)
    LOG = logging.getLogger(module_name)
    LOG.setLevel(log_devel)
    return LOG


'''
Convert the given size to bytes
'''
KB_IN_BYTES = 1024
MB_IN_BYTES = 1024 * 1024
GB_IN_BYTES = 1024 * 1024 * 1024
TB_IN_BYTES = 1024 * 1024 * 1024 * 1024


def get_size_bytes(size, cap_units):
    if size is not None and size > 0:
        if cap_units in ('kb', 'KB'):
            return size * KB_IN_BYTES
        elif cap_units in ('mb', 'MB'):
            return size * MB_IN_BYTES
        elif cap_units in ('gb', 'GB'):
            return size * GB_IN_BYTES
        elif cap_units in ('tb', 'TB'):
            return size * TB_IN_BYTES
        else:
            return size
    else:
        return 0


'''
Convert size in byte with actual unit like KB,MB,GB,TB,PB etc.
'''


def convert_size_with_unit(size_bytes):
    if not isinstance(size_bytes, int):
        raise ValueError('This method takes Integer type argument only')
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


'''
Convert the given size to size in GB, size is restricted to 2 decimal places
'''


def get_size_in_gb(size, cap_units):
    size_in_bytes = get_size_bytes(size, cap_units)
    size = Decimal(size_in_bytes / GB_IN_BYTES)
    size_in_gb = round(size, 2)
    return size_in_gb


'''
Validates the package pre-requisites of invoking module
'''


def validate_module_pre_reqs(module_params):
    error_message = ""
    min_py_ver = '2.8.0'
    max_py_ver = '3.7.0'
    cur_py_ver = "{0}.{1}.{2}".format(str(sys.version_info[0]),
                                      str(sys.version_info[1]),
                                      str(sys.version_info[2]))

    is_supported_py_version = (parse_version(min_py_ver) <=
                               parse_version(cur_py_ver) <
                               parse_version(max_py_ver))

    if not is_supported_py_version:
        prereqs_check = dict(
            all_packages_found=False,
            error_message="Python version {0} is not yet supported by this"
                          " module. Please refer the support metrics for more"
                          " information.".format(cur_py_ver))
        return prereqs_check

    if not HAS_IMPORTLIB or not HAS_PKG_RESOURCES:
        prereqs_check = dict(
            all_packages_found=False,
            error_message=get_missing_pkgs()
        )
        return prereqs_check

    POWERSCALE_SDK_IMPORT = find_compatible_powerscale_sdk(module_params)
    if POWERSCALE_SDK_IMPORT and \
            not POWERSCALE_SDK_IMPORT["powerscale_package_imported"]:
        if POWERSCALE_SDK_IMPORT['error_message']:
            error_message = POWERSCALE_SDK_IMPORT['error_message']
        elif IMPORT_PKGS_FAIL:
            error_message = get_missing_pkgs()
        prereqs_check = dict(
            all_packages_found=False,
            error_message=error_message
        )
        return prereqs_check

    POWERSCALE_SDK_VERSION_CHECK = powerscale_sdk_version_check()
    if POWERSCALE_SDK_VERSION_CHECK and \
            not POWERSCALE_SDK_VERSION_CHECK['supported_version']:
        if IMPORT_PKGS_FAIL:
            error_message = get_missing_pkgs()
        prereqs_check = dict(
            all_packages_found=False,
            error_message=error_message + POWERSCALE_SDK_VERSION_CHECK
            ['unsupported_version_message'])
        return prereqs_check
    else:
        if IMPORT_PKGS_FAIL:
            prereqs_check = dict(
                all_packages_found=False,
                error_message=get_missing_pkgs()
            )
            return prereqs_check

    return dict(all_packages_found=True, error_message=None)


''' Import compatible powerscale sdk based on onefs version '''


def import_powerscale_sdk(sdk):
    try:
        global isi_sdk
        global ApiException
        global HAS_POWERSCALE_SDK
        global ISI_SDK_VERSION_9

        isi_sdk = importlib.import_module(sdk)
        ApiException = getattr(importlib.import_module(sdk + ".rest"),
                               'ApiException')
        HAS_POWERSCALE_SDK = True
        ISI_SDK_VERSION_9 = True if isi_sdk.__name__ == POWERSCALE_SDK_9_0_0 \
            else False

    except ImportError:
        HAS_POWERSCALE_SDK = False


''' Find compatible powerscale sdk based on onefs version '''


def find_compatible_powerscale_sdk(module_params):
    global HAS_POWERSCALE_SDK
    error_message = ""
    targeted_onefs_version = "9.0.0.0"

    powerscale_packages = [pkg for pkg in pkg_resources.working_set
                           if pkg.key.startswith("isi-sdk")]
    if powerscale_packages:
        powerscale_sdk = powerscale_packages[0].key.replace('-', '_')
        import_powerscale_sdk(powerscale_sdk)
        try:
            api_client = get_powerscale_connection(module_params)
            cluster_api = isi_sdk.ClusterApi(api_client)
            if parse_version(cluster_api.get_cluster_config()
                             .to_dict()['onefs_version']['release']) \
                    < parse_version(targeted_onefs_version):
                compatible_powerscale_sdk = POWERSCALE_SDK_8_1_1
            else:
                compatible_powerscale_sdk = POWERSCALE_SDK_9_0_0
            if powerscale_sdk != compatible_powerscale_sdk:
                import_powerscale_sdk(compatible_powerscale_sdk)
        except Exception as e:
            HAS_POWERSCALE_SDK = False
            error_message = 'Unable to fetch version of array {0}, ' \
                            'failed with error: {1}'.format(
                                module_params["onefs_host"], str(
                                    determine_error(error_obj=e)))

    if not HAS_POWERSCALE_SDK:
        IMPORT_PKGS_FAIL.append('PowerScale python library. Please install'
                                ' isi-sdk-9-0-0 for OneFS version 9.0 and above'
                                ' and isi-sdk-8-1-1 for OneFS version less'
                                ' than 9.0')

    return dict(powerscale_package_imported=HAS_POWERSCALE_SDK,
                error_message=error_message)


''' Returns threshold overhead param name based on imported sdk version '''


def get_threshold_overhead_parameter():
    if ISI_SDK_VERSION_9:
        return "thresholds_on"
    else:
        return "thresholds_include_overhead"


''' Validates threshold overhead parameter based on imported sdk version '''


def validateThresholdOverheadParameter(quota, threshold_overhead_param):
    error_msg = None
    key = 'thresholds_on'
    if ISI_SDK_VERSION_9:
        if quota and key in quota \
                and quota[key]:
            thresholds_on_value = quota[key]
            if thresholds_on_value == 'physical_size':
                quota[key] = 'physicalsize'
            elif thresholds_on_value == 'fs_logical_size':
                quota[key] = 'fslogicalsize'
            elif thresholds_on_value == 'app_logical_size':
                quota[key] = 'applogicalsize'
            else:
                error_msg = 'Invalid thresholds_on provided, ' \
                            'only app_logical_size, fs_logical_size ' \
                            'and physical_size are supported.'

    else:
        if quota and key in quota \
                and quota[key]:
            error_msg = "The parameter 'thresholds_on' is not supported. " \
                        "Please use " + threshold_overhead_param + " option."

    return dict(param_is_valid=error_msg is None,
                error_message=error_msg)


''' Determine the error message to return '''


def determine_error(error_obj):
    if isinstance(error_obj, ApiException):
        error = re.sub("[\n \"]+", ' ', str(error_obj.body))
    else:
        error = str(error_obj)
    return error


''' Returns missing packages '''


def get_missing_pkgs():
    return "Unable to import " + ",".join(IMPORT_PKGS_FAIL) + \
        ". Please install the required package(s)."


''' Returns time in seconds '''


def get_time_in_seconds(time, time_units):

    min_in_sec = 60
    hour_in_sec = 60 * 60
    day_in_sec = 24 * 60 * 60
    weeks_in_sec = 7 * 24 * 60 * 60
    months_in_sec = 30 * 24 * 60 * 60
    years_in_sec = 365 * 24 * 60 * 60
    if time and time > 0:
        if time_units in 'minutes':
            return time * min_in_sec
        elif time_units in 'hours':
            return time * hour_in_sec
        elif time_units in 'days':
            return time * day_in_sec
        elif time_units in 'weeks':
            return time * weeks_in_sec
        elif time_units in 'months':
            return time * months_in_sec
        elif time_units in 'years':
            return time * years_in_sec
        else:
            return time
    else:
        return 0


''' Returns time with unit '''


def get_time_with_unit(time):
    sec_in_min = 60
    sec_in_hour = 60 * 60
    sec_in_day = 24 * 60 * 60

    if time % sec_in_day == 0:
        time = time / sec_in_day
        unit = 'days'

    elif time % sec_in_hour == 0:
        time = time / sec_in_hour
        unit = 'hours'

    else:
        time = time / sec_in_min
        unit = 'minutes'
    return "%s %s" % (time, unit)


'''
Check whether input string is empty
'''


def is_input_empty(item):
    if item == "" or item.isspace():
        return True
    else:
        return False
