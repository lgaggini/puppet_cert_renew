#! /usr/bin/env python

import argparse
import logging
import coloredlogs
from paramiko import SSHClient, WarningPolicy
import sys
from fqdn import FQDN


logger = logging.getLogger('puppet_cert_renew')
LOG_LEVELS = ['debug', 'info', 'warning', 'error', 'critical']


def log_init(loglevel):
    """ initialize the logging system """
    FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
    logging.basicConfig(format=FORMAT, level=getattr(logging,
                                                     loglevel.upper()))
    coloredlogs.install(level=loglevel.upper())


def get_ssh(hostname):
    """ get a ssh connection to hostname """
    logger.info('opening connection to %s' % hostname)
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(WarningPolicy())
    ssh.connect(hostname, username='root')
    return ssh


def remote_command(ssh, command):
    """ execute a remote command by the ssh connection """
    logger.debug(command)
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout_str = ' ,'.join(stdout.readlines())
    stderr_str = ' ,'.join(stderr.readlines())
    logger.debug('stdout: ' + stdout_str)
    logger.debug('stderr: ' + stderr_str)
    return stdout.channel.recv_exit_status(), stdout_str, stderr_str


def check_exit(exit, stdout, stderr, block=True):
    """ check the exit code and if not 0 log stderror and exit
    (if blocking command) """
    if exit == 0:
        return
    else:
        logger.error(stderr)
        if block:
            sys.exit(127)


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
        check_exit(*remote_command(ssh, command))


def puppetmaster_cert_sign(ssh, server, puppetmaster, readonly):
    """ sign the new certificate on the puppetmaster """
    logger.info('sign %s certificate on %s' % (server, puppetmaster))
    command = 'puppet cert sign %s' % (server)
    logger.debug(command)
    if not readonly:
        check_exit(*remote_command(ssh, command))


def server_cert_backup(ssh, server, readonly):
    """ backup the old cert on the host """
    logger.info('backup %s certificate' % (server))
    command = 'mv /var/lib/puppet/ssl /var/lib/puppet/ssl.bak'
    logger.debug(command)
    if not readonly:
        check_exit(*remote_command(ssh, command))


def server_cert_clean(ssh, server, readonly):
    """ remove the backup on the host """
    logger.info('remove %s certificate backup ' % (server))
    command = 'rm /var/lib/puppet/ssl.bak'
    logger.debug(command)
    if not readonly:
        check_exit(*remote_command(ssh, command))


def server_puppet_run(ssh, server, readonly):
    """ run puppet on the host """
    logger.info('run puppet on %s' % (server))
    command = 'puppet agent -t'
    logger.debug(command)
    if not readonly:
        check_exit(*remote_command(ssh, command))


def puppet_cert_renew(puppetmaster, server, readonly):
    """ renew puppet clien certificate """
    puppetmaster_ssh = get_ssh(puppetmaster)
    puppetmaster_cert_clean(puppetmaster_ssh, server, puppetmaster,
                            readonly)
    server_ssh = get_ssh(server)
    server_cert_backup(server_ssh, server, readonly)
    server_puppet_run(server_ssh, server, readonly)
    puppetmaster_cert_sign(puppetmaster_ssh, server, puppetmaster,
                           readonly)
    server_puppet_run(server_ssh, server, readonly)
    puppetmaster_ssh.close()
    server_ssh.close()


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
    parser.add_argument('-l', '--log-level', default=LOG_LEVELS[1],
                        help='log level (default info)', choices=LOG_LEVELS)

    # parse cli options
    cli_options = parser.parse_args()
    log_init(cli_options.log_level)
    logger.debug(cli_options)

    # puppet cert renew
    puppet_cert_renew(cli_options.puppetmaster.relative,
                      cli_options.server.relative,
                      cli_options.readonly)
