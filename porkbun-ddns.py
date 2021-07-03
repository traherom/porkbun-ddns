#!/usr/bin/env pytnon3
import json
import sys
import logging
import argparse
import requests

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def get_records(config, domain):
    """
    grab all the records so we know which ones to delete to make room for our record

    Also checks to make sure we've got the right domain
    """
    LOG.info("Getting existing domain records")
    resp = json.loads(
        requests.post(
            f"{config['endpoint']}/dns/retrieve/{domain}",
            data=json.dumps(config)
        ).text
    )
    if resp["status"] == "ERROR":
        LOG.error(
            'Error getting domain. Check to make sure you specified the correct'
            'domain, and that API access has been switched on for this domain.'
        )
        sys.exit()
    LOG.debug("Response: %s", resp)
    return resp["records"]


def get_my_ip(config):
    LOG.info("Getting external IP address")
    ping = json.loads(requests.post(config["endpoint"] + '/ping/', data=json.dumps(config)).text)
    LOG.debug("Response: %s", ping)
    return ping["yourIp"]


def delete_record(config, root_domain, sub_domain):
    LOG.info("Removing domain if it already exists")
    for i in get_records(config, root_domain):
        if i["name"].startswith(sub_domain) and i["type"] in ('A', 'ALIAS', 'CNAME'):
            LOG.info("Deleting existing " + i["type"] + " Record")
            resp = json.loads(
                requests.post(
                    f"{config['endpoint']}/dns/delete/{root_domain}/{i['id']}",
                    data=json.dumps(config)
                ).text
            )
            LOG.debug("Response: %s", resp)


def create_record(config, root_domain, sub_domain, ip):
    config.update({'name': sub_domain, 'type': 'A', 'content': ip, 'ttl': 300})
    LOG.info("Creating record: %s with answer %s", sub_domain, ip)
    resp = json.loads(
        requests.post(
            f"{config['endpoint']}/dns/create/{root_domain}",
            data=json.dumps(config)
        ).text
    )
    LOG.debug("Response: %s", resp)
    return resp


def main():
    parser = argparse.ArgumentParser(description='Update a Porkbun DNS entry')
    parser.add_argument('--config', '-c', required=True, help='Path to configuration file')
    parser.add_argument('domain', help='Domain to update')
    args = parser.parse_args()

    config = json.load(open(args.config))

    fqdn_domain = args.domain
    domain_parts = fqdn_domain.rsplit(".")
    root_domain = ".".join(domain_parts[-2:])
    sub_domain = ".".join(domain_parts[:-2])

    ip = get_my_ip(config)
    delete_record(config, root_domain, sub_domain)
    create_record(config, root_domain, sub_domain, ip)


if __name__ == "__main__":
    sys.exit(main())

# if len(sys.argv) > 2:  # at least the config and root domain is specified
#     apiConfig = json.load(open(sys.argv[1]))  # load the config file into a variable
#     rootDomain = sys.argv[2]
#
#     if len(sys.argv) > 3 and sys.argv[3] != '-i':  # check if a subdomain was specified as the third argument
#         subDomain = sys.argv[3]
#         fqdn = subDomain + "." + rootDomain
#     else:
#         subDomain = ''
#         fqdn = rootDomain
#
#     if len(sys.argv) > 4 and sys.argv[
#         3] == '-i':  # check if IP is manually specified. There's probably a more-elegant way to do this
#         myIP = sys.argv[4]
#     elif len(sys.argv) > 5 and sys.argv[4] == '-i':
#         myIP = sys.argv[5]
#     else:
#         myIP = getMyIP()  # otherwise use the detected exterior IP address
#
#     deleteRecord()
#     print(createRecord()["status"])
#
# else:
#     print(
#         "Porkbun Dynamic DNS client, Python Edition\n\nError: not enough arguments. Examples:\npython porkbun-ddns.py /path/to/config.json example.com\npython porkbun-ddns.py /path/to/config.json example.com www\npython porkbun-ddns.py /path/to/config.json example.com '*'\npython porkbun-ddns.py /path/to/config.json example.com -i 10.0.0.1\n")
