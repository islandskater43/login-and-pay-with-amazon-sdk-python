import re
import os
import sys
import logging
import platform
import amazon_pay.ap_region as ap_region
import amazon_pay.report_version as ap_version
from amazon_pay.report_request import ReportRequest
from fileinput import filename


class ReportClient:

    logger = logging.getLogger('__amazon_pay_sdk__')
    logger.addHandler(logging.NullHandler())

    """This client allows you to make all the necessary API calls to
        integrate with MWS Reports.
    """
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # pylint: disable=too-many-arguments, too-many-lines

    def __init__(
            self,
            mws_access_key=None,
            mws_secret_key=None,
            merchant_id=None,
            region=None,
            currency_code=None,
            sandbox=False,
            handle_throttle=True,
            application_name=None,
            application_version=None,
            log_enabled=False,
            log_file_name=None,
            log_level=None):


        """
        Parameters
        ----------
        mws_access_key : string, optional
            Your MWS access key. If no value is passed, check environment.
            Environment variable: AP_MWS_ACCESS_KEY
            (mws_access_key must be passed or specified in environment or this
             will result in an error)

        mws_secret_key : string, optional
            Your MWS secret key. If no value is passed, check environment.
            Environment variable: AP_MWS_SECRET_KEY
            (mws_secret_key must be passed or specified in environment or this
             will result in an error)

        merchant_id : string, optional
            Your merchant ID. If you are a marketplace enter the seller's merchant
            ID. If no value is passed, check environment.
            Environment variable: AP_MERCHANT_ID
            (merchant_id must be passed or specified in environment or this
             will result in an error)

        region : string, optional
            The region in which you are conducting business. If no value is
            passed, check environment.
            Environment variable: AP_REGION
            (region must be passed or specified in environment or this
             will result in an error)

        sandbox : string, optional
            Toggle sandbox mode. Default: False.

        currency_code: string, required
            Currency code for your region.
            Environment variable: AP_CURRENCY_CODE

        handle_throttle: boolean, optional
            If requests are throttled, do you want this client to pause and
            retry? Default: True

        application_name: string, optional
            The name of your application. This will get set in the UserAgent.
            Default: None

        application_version: string, optional
            Your application version. This will get set in the UserAgent.
            Default: None

        log_file_name: string, optional
            The name of the file for logging
            Default: None

        log_level: integer, optional
            The level of logging recorded
            Default: "None"
            Levels: "CRITICAL"; "ERROR"; "WARNING"; "INFO"; "DEBUG"; "NOTSET"
        """
        env_param_map = {'mws_access_key': 'AP_MWS_ACCESS_KEY',
                         'mws_secret_key': 'AP_MWS_SECRET_KEY',
                         'merchant_id': 'AP_MERCHANT_ID',
                         'region': 'AP_REGION',
                         'currency_code': 'AP_CURRENCY_CODE'}
        for param in env_param_map:
            if eval(param) is None:
                try:
                    setattr(self, param, os.environ[env_param_map[param]])
                except:
                    raise ValueError('Invalid {}.'.format(param))
            else:
                setattr(self, param, eval(param))

        try:
            self._region = ap_region.regions[self.region]
            # used for Login with Amazon helper
            self._region_code = self.region
        except KeyError:
            raise KeyError('Invalid region code ({})'.format(self.region))

        self.mws_access_key = self.mws_access_key
        self.mws_secret_key = self.mws_secret_key
        self.merchant_id = self.merchant_id
        self.currency_code = self.currency_code
        self.handle_throttle = handle_throttle
        self.application_name = application_name
        self.application_version = application_version

        self._sandbox = sandbox
        self._api_version = ap_version.versions['api_version']
        self._api_name = ap_version.versions['api_name']
        self._application_library_version = ap_version.versions[
            'application_version']
        self._mws_endpoint = None
        self._set_endpoint()

        if log_enabled is not False:
            numeric_level = getattr(logging, log_level.upper(), None)
            if numeric_level is not None:
                if log_file_name is not None:
                    self.logger.setLevel(numeric_level)
                    fh = logging.FileHandler(log_file_name)
                    self.logger.addHandler(fh)
                    fh.setLevel(numeric_level)
                else:
                    self.logger.setLevel(numeric_level)
                    ch = logging.StreamHandler(sys.stdout)
                    self.logger.addHandler(ch)
                    ch.setLevel(numeric_level)

        app_name_and_ver = ''

        if application_name not in ['', None]:
            app_name_and_ver = app_name_and_ver + str(application_name)
            if application_version not in ['', None]:
                app_name_and_ver = app_name_and_ver + '/' + str(application_version)

        elif application_version not in ['', None]:
            app_name_and_ver = app_name_and_ver + str(application_version)

        if ((application_name not in ['', None]) | (application_version not in ['', None])):
            app_name_and_ver = app_name_and_ver + '; '

        current_py_ver = ".".join(map(str, sys.version_info[:3]))

        self._user_agent = 'amazon-pay-sdk-python/{0} ({1}Python/{2}; {3}/{4})'.format(
            str(self._application_library_version),
            str(app_name_and_ver),
            str(current_py_ver),
            str(platform.system()),
            str(platform.release())
        )

        self.logger.debug('user agent: %s', self._user_agent)

        self._headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self._user_agent}

    @property
    def sandbox(self):
        return self._sandbox

    @sandbox.setter
    def sandbox(self, value):
        """Set Sandbox mode"""
        self._sandbox = value
        self._set_endpoint()

    def _set_endpoint(self):
        """Set endpoint for API calls"""
        self._mws_endpoint = \
            'https://{}/{}/{}'.format(
                    self._region, self._api_name, self._api_version)

    def get_report_list(
            self,
            available_from=None,
            available_to=None,
            acknowledged=None,
            report_type_list=None,
            merchant_id=None,
            mws_auth_token=None):
        """Returns list of available reports.

        Parameters
        ----------
        xxx

        yyy

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """

        parameters = {
            'Action': 'GetReportList'}
        optionals = {
            'AvailableFromDate': available_from,
            'AvailableToDate': available_to,
            'Acknowledged': acknowledged,
            'ReportTypeList.Type.1': report_type_list,
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def get_report(
            self,
            report_id,
            merchant_id=None,
            mws_auth_token=None):
        """Returns report content.

        Parameters
        ----------
        report_id: unsigned integer, required
            The report ID you are trying to retrieve.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'GetReport',
            'ReportId': report_id}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def update_report_acknowledgements(
            self,
            report_id,
            acknowledged=None,
            merchant_id=None,
            mws_auth_token=None):
        """ Updates the acknowledged status of one report.

        Parameters
        ----------
        report_id: unsigned integer, required
            The report ID to acknowledge.

        acknowledged: boolean, optional
            A Boolean value that indicates that you have received and stored a report.

        mws_auth_token: string, optional
            Your marketplace web service auth token. Default: None
        """
        parameters = {
            'Action': 'UpdateReportAcknowledgements',
            'ReportIdList.Id.1': report_id,
            'Acknowledged': acknowledged}
        optionals = {
            'SellerId': merchant_id,
            'MWSAuthToken': mws_auth_token}
        return self._operation(params=parameters, options=optionals)

    def _operation(self, params, options=None):
        """Parses required and optional parameters and passes to the Request
        object.
        """
        if options is not None:
            for opt in options.keys():
                if options[opt] is not None:
                    params[opt] = options[opt]

        request = ReportRequest(
            params=params,
            config={'mws_access_key': self.mws_access_key,
                    'mws_secret_key': self.mws_secret_key,
                    'api_version': self._api_version,
                    'merchant_id': self.merchant_id,
                    'mws_endpoint': self._mws_endpoint,
                    'headers': self._headers,
                    'handle_throttle': self.handle_throttle})

        request.send_post()
        return request.response
