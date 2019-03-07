def get_context(middleware):
    context = {
        'is_freenas': middleware.call_sync('system.is_freenas'),
        'failover_licensed': False,
    }

    if not context['is_freenas']:
        context['failover_licensed'] = middleware.call_sync('failover.licensed')

    return context


def host_config(middleware, context):
    config = middleware.call_sync('network.configuration.config')
    yield f'hostname="{config["hostname"]}.{config["domain"]}"'

    if config['ipv4gateway']:
        yield f'defaultrouter="{config["ipv4gateway"]}"'

    if config['ipv6gateway']:
        yield f'ipv6_defaultrouter="{config["ipv6gateway"]}"'

    if config['netwait_enabled']:
        yield 'netwait_enable="YES"'
        if not config['netwait_ip']:
            if config['ipv4gateway']:
                config['netwait_ip'] = config['ipv4gateway']
            elif config['ipv6gateway']:
                config['netwait_ip'] = config['ipv6gateway']
        yield f'netwait_ip="{config["netwait_ip"]}"'


def services_config(middleware, context):
    services = middleware.call_sync('datastore.query', 'services.services', [], {'prefix': 'srv_'})
    mapping = {
        'afp': ['netatalk'],
        'cifs': ['samba_server', 'smbd', 'nmbd', 'winbindd'],
        'dynamicdns': ['inadyn'],
        'ftp': ['proftpd'],
        'iscsitarget': ['ctld'],
        'lldp': ['ladvd'],
        'netdata': ['netdata'],
        'nfs': ['nfs_server', 'rpc_lockd', 'rpc_statd', 'mountd', 'nfsd', 'rpcbind'],
        'rsync': ['rsyncd'],
        'snmp': ['snmpd', 'snmp_agent'],
        'ssh': ['openssh'],
        'tftp': ['inetd'],
        'webdav': ['apache24'],
    }

    if context['failover_licensed'] is False:
        # These services are handled by HA script
        # smartd #76242
        mapping.update({
            'smartd': ['smartd_daemon'],
            'asigra': ['dssystem', 'postgresql'],
        })

    for service in services:
        rcs_enable = mapping.get(service['service'])
        if not rcs_enable:
            continue
        value = 'YES' if service['enable'] else 'NO'
        for rc_enable in rcs_enable:
            yield f'{rc_enable}_enable="{value}"'


def render(service, middleware):

    context = get_context(middleware)

    rcs = []
    for i in (
        services_config,
        host_config,
    ):
        rcs += list(i(middleware, context))

    with open('/etc/rc.conf.freenas', 'w') as f:
        f.write('\n'.join(rcs) + '\n')
