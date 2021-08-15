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


def get_my_ip(config) -> str:
    LOG.info("Getting external IP address")
    ping = json.loads(
        requests.post(
            f"{config['endpoint']}/ping",
            data=json.dumps(config)
        ).text
    )
    LOG.debug("Response: %s", ping)
    return ping["yourIp"]


def delete_record(config, root_domain, record_id):
    resp = json.loads(
        requests.post(
            f"{config['endpoint']}/dns/delete/{root_domain}/{record_id}",
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

    # Is the IP already correct?
    new_record_needed = True
    records = get_records(config, root_domain)
    for record in records:
        if record["name"].startswith(sub_domain) and record["type"] in ('A', 'ALIAS', 'CNAME'):
            if record["content"] == ip:
                LOG.info("Existing record is correct: %s %s", record["type"], record["content"])
                new_record_needed = False
                continue
            
            LOG.info("Existing record out of date, removing: %s %s", record["type"], record["content"])
            delete_record(config, root_domain, record["id"])
    
    if new_record_needed:
        create_record(config, root_domain, sub_domain, ip)


if __name__ == "__main__":
    sys.exit(main())
