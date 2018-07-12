# puppet cert renew

pupper cert renew is a tool to automate the steps needed to renew a puppet client certificate.
It performs various steps by ssh connection to the puppetmaster and the server with the expired, expiring certifcate:

* `puppet cert clean` on the puppetmaster
* `mv /var/lib/puppet/ssl /var/lib/puppet/ssl.bak` on the server
* `puppet agent -t` on the server
* `puppet cert sign` on the puppetmaster
* `rm /var/lib/puppet/ssl.bak` on the server (optional)

## Requirements
```
pip install -r requirements.txt
```

## Usage
```
usage: puppet_cert_renew.py [-h] -m PUPPETMASTER -s SERVER [-r] [-c] [-i]                                                                                                                                          
                            [-l {debug,info,warning,error,critical}]

puppet_cert_renew, renew puppet client certificate

optional arguments:
  -h, --help            show this help message and exit
  -m PUPPETMASTER, --puppetmaster PUPPETMASTER
                        fqdn of the puppetmaster
  -s SERVER, --server SERVER
                        fqdn of the server to be renewed
  -r, --readonly        readonly mode for debug (default disabled)
  -c, --cleanup         removes the old certicate backup from server (default
                        disabled
  -i, --inventory       reinventory the puppemaster certificates (default
                        disabled)
  -l {debug,info,warning,error,critical}, --log-level {debug,info,warning,error,critical}
                        log level (default info
```

## Example
Renew the certificate on the host `host.it` signed on the puppetmaster `puppet.master` on log debug level
```
./puppet_cert_renew.py -m puppet.master -s host.it -l debug
```
