#! /usr/bin/env python

import argparse
import logging
import coloredlogs
from pysshops import SshOps
from fqdn import FQDN
import datetime


logger = logging.getLogger('puppet_cert_renew')
LOG_LEVELS = ['debug', 'info', 'warning', 'error', 'critical']


def log_init(loglevel):
    """ initialize the logging system """
    FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
    logging.basicConfig(format=FORMAT, level=getattr(logging,
                                                     loglevel.upper()))
    coloredlogs.install(level=loglevel.upper())


def valid_fqdn(fqdn):
    """ syntax validator for fqdn """
    fqdn = FQDN(fqdn)
    if fqdn.is_valid:
        return fqdn
    else:
        raise argparse.ArgumentError('%s is not a valid fqdn' % fqdn)


def puppetmaster_cert_clean(ssh, server, puppetmaster, readonly):
    """ clean the old certificate from the puppetmaster """
    logger.info('clean %s certificate on %s' % (server, puppetmaster))
    command = 'puppet cert clean %s' % (server)
    logger.debug(command)
    if not readonly:
        ssh.remote_command(command)


def puppetmaster_cert_sign(ssh, server, puppetmaster, readonly):
    """ sign the new certificate on the puppetmaster """
    logger.info('sign %s certificate on %s' % (server, puppetmaster))
    command = 'puppet cert sign %s' % (server)
    logger.debug(command)
    if not readonly:
        ssh.remote_command(command)


def puppetmaster_cert_reinventory(ssh, puppetmaster, readonly):
    """ reinventory the updated certificate on the puppetmaster """
    logger.info('reinventory certificate on %s' % (puppetmaster))
    command = 'puppet cert reinventory'
    logger.debug(command)
    if not readonly:
        ssh.remote_command(command)


def server_cert_clean(ssh, server, readonly, cleanup):
    """ backup the old cert on the host """
    logger.info('backup %s certificate' % (server))
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if cleanup:
        command = 'sudo rm -rf /var/lib/puppet/ssl'
    else:
        command = 'sudo mv /var/lib/puppet/ssl /var/lib/puppet/ssl.bak.%s' % (now)
    logger.debug(command)
    if not readonly:
        ssh.remote_command(command)


def server_puppet_run(ssh, server, readonly, block=False):
    """ run puppet on the host """
    logger.info('run puppet on %s' % (server))
    command = 'puppet agent -t'
    logger.debug(command)
    if not readonly:
        ssh.remote_command(command, block=block)


def puppet_cert_renew(puppetmaster, server, readonly, cleanup, reinventory):
    """ renew puppet client certificate """
    puppetmaster_srv = SshOps(puppetmaster, 'root')
    server_srv = SshOps(server, 'root')

    with puppetmaster_srv as puppetmaster_ssh, server_srv as server_ssh:
        puppetmaster_cert_clean(puppetmaster_ssh, server, puppetmaster,
                                readonly)
        server_cert_backup(server_ssh, server, readonly)
        server_puppet_run(server_ssh, server, readonly)
        puppetmaster_cert_sign(puppetmaster_ssh, server, puppetmaster,
                               readonly)
        server_puppet_run(server_ssh, server, readonly)
        if cleanup:
            server_cert_clean(server_ssh, server, readonly)
        if reinventory:
            puppetmaster_cert_reinventory(puppetmaster_ssh, puppetmaster,
                                          readonly)


if __name__ == '__main__':

    description = 'puppet_cert_renew, renew puppet client certificate'

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-m', '--puppetmaster', required=True, type=valid_fqdn,
                        help='fqdn of the puppetmaster')
    parser.add_argument('-s', '--server', required=True, type=valid_fqdn,
                        help='fqdn of the server to be renewed')
    parser.add_argument('-r', '--readonly', dest='readonly',
                        action='store_true',
                        help='readonly mode for debug (default disabled)')
    parser.set_defaults(readonly=False)
    parser.add_argument('-c', '--cleanup', dest='cleanup',
                        action='store_true',
                        help='removes the old certicate backup from server \
                        (default disabled)')
    parser.set_defaults(readonly=False)
    parser.add_argument('-i', '--inventory', dest='reinventory',
                        action='store_true',
                        help='reinventory the puppemaster certificates\
                        (default disabled)')
    parser.set_defaults(readonly=False)

    parser.add_argument('-l', '--log-level', default=LOG_LEVELS[1],
                        help='log level (default info)', choices=LOG_LEVELS)

    # parse cli options
    cli_options = parser.parse_args()
    log_init(cli_options.log_level)
    logger.debug(cli_options)

    # puppet cert renew
    puppet_cert_renew(cli_options.puppetmaster.relative,
                      cli_options.server.relative,
                      cli_options.readonly,
                      cli_options.cleanup,
                      cli_options.reinventory)
