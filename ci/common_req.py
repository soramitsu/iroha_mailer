# pylint: disable=C0114
import sys
from logging import info
from argparse import ArgumentParser, Action
from aiohttp import ClientSession
from aiohttp.formdata import FormData

# Messages to display in the log
REQUEST_MESSAGES = {
    'email': {
        200: 'Emails sent successfully',
        'default': 'Unable to send the emails. HTTP status: {status}'
    },
    'print': {
        200: 'The result was generated',
        'default': 'Unable to generate the print version. HTTP status: {status}'
    }
}

async def prepare_request(data_path, totp):
    """
    Prepares the FormData instance with a TOTP key
    for the request.
    """
    data = FormData()
    data.add_field('password', totp)
    with open(data_path, 'rb') as template_data:
        data.add_field('template_data', template_data.read())
    return data

async def log_request(mode, status):
    """
    Log the request result,
    displaying the result and using an appropriate message.
    """
    result = ''
    result = REQUEST_MESSAGES[mode].get(status if status == 200 else 'default')
    result = result.format(status=status)
    info(result)

async def perform_mail_request(addr: str, data_path: str, totp: str):
    """
    Sends a request for mailing.
    """
    async with ClientSession() as session:
        data = await prepare_request(data_path, totp)
        req = await session.post(addr, data=data)
        await log_request('email', req.status)

async def perform_print_request(addr: str, data_path: str, totp: str):
    """
    Sends a request for a print version.
    """
    result = ''
    async with ClientSession() as session:
        data = await prepare_request(data_path, totp)
        req = await session.post(addr, data=data)
        await log_request('print', req.status)
        if req.status == 200:
            result = await req.text()
    return result

class FixPrintRouteAction(Action):
    """
    Fixes the route, adding the "/generate_print" part.
    """

    def __call__(self, parser, args, value, option_string=None):
        value = value.removesuffix('/generate_print').removesuffix('/generate_print/')
        setattr(args, self.dest, f'{value}/generate_print')

class FixMailRouteAction(Action):
    """
    Fixes the route, adding the "/schedule" part.
    """

    def __call__(self, parser, args, value, option_string=None):
        value = value.removesuffix('/schedule').removesuffix('/schedule/')
        setattr(args, self.dest, f'{value}/schedule')

def get_arguments(mode: str):
    """
    Retrieves the Argparse arguments.

    Args:
        mode (str): (mail or print)
    """
    fix_route_action = None
    if mode == 'mail':
        description = 'Mail requester utility'
        fix_route_action = FixMailRouteAction
    elif mode == 'print':
        description = 'Print version requester utility'
        fix_route_action = FixPrintRouteAction
    else:
        # Fail early as it's a potential code error
        description = 'Incorrect argument configuration mode detected'
        sys.exit(1)
    parser = ArgumentParser(description=description)
    parser.add_argument(
        '-s',
        '--secret_path',
        help='Path to the secret file for the TOTP generator',
        required=True
    )
    parser.add_argument(
        '-a',
        '--address',
        help="HTTP address",
        required=True,
        action=fix_route_action
    )
    parser.add_argument(
        '-d',
        "--data_path",
        help="Path to the data file",
        required=True
    )
    if mode == 'print':
        parser.add_argument(
            '-o',
            "--output_path",
            help="Path to the output HTML file",
            required=True
        )
    return parser.parse_args()
