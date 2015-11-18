#!/usr/bin/python

import sys
import ldap
from jinja2 import Environment, FileSystemLoader
import os


def ldapQuery(baseDN, searchScope, retrieveAttributes, searchFilter):

	print "baseDN:              " + baseDN
	print "search filter:       " + searchFilter
	print "retrieve attributes: " + ', '.join(retrieveAttributes)

	try:
		ldap_result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)
		result_set = []
		while 1:
			result_type, result_data = l.result(ldap_result_id, 0)
			if (result_data == []):
				break
			else:
				## here you don't have to append to a list
				## you could do whatever you want with the individual entry
				## The appending to list is just for illustration.
				if result_type == ldap.RES_SEARCH_ENTRY:
					result_set.append(result_data)

	except ldap.LDAPError, error_message:
		print error_message

	print len(result_set)
	if len(result_set) == 0:
		print "No Results."

	return result_set


## open connection to the top bdii
try:
	l = ldap.open(host="egee-bdii.cnaf.infn.it", port=2170)
	## searching doesn't require a bind in LDAP V3.  If you're using LDAP v2, set the next line appropriately
	## and do a bind as shown in the above example.
	# you can also set this to ldap.VERSION2 if you're using a v2 directory
	# you should  set the next option to ldap.VERSION2 if you're using a v2 directory
	l.protocol_version = ldap.VERSION3
except ldap.LDAPError, e:
	print e
	quit()
	# handle error however you like

## The next lines will also need to be changed to support your search requirements and directory
baseDN = "GLUE2GroupID=grid,o=glue"
searchScope = ldap.SCOPE_SUBTREE

## retrieve all attributes - again adjust to your needs - see documentation for more options
retrieveAttributes = ["GLUE2ManagerProductVersion"]
searchFilter = "GLUE2ManagerProductName=StoRM"

result_set = ldapQuery(baseDN, searchScope, retrieveAttributes, searchFilter)

domains = dict()
versions = dict()

n = len("/storage")

for i in range(len(result_set)):
	for entry in result_set[i]:
		dn = entry[0]
		version = entry[1]['GLUE2ManagerProductVersion'][0]
		domain = dn.split(',')[3].split('=')[1]
		hostname = dn.split(",")[1].split("=")[1][:-n]
		#print "%d.\nDn: %s\nDomain: %s\nHostname: %s\nVersion: %s" % (i+1, dn, domain, hostname, version)

		if not domain in domains:
			domains[domain] = dict()
		domains[domain][hostname] = version

		if version in versions:
			versions[version] += 1
		else:
			versions[version] = 1

tot_istances = len(result_set)

print "\n%-25s\t%-25s\t%-10s" % ("Domain", "Hostname", "Version")
for domain, hosts in sorted(domains.items()):
	for host, version in sorted(hosts.items()):
		print "%-25s\t%-25s\t%-10s" % (domain, host, version)

print "\n## Summary ##"
print "Total sites: %d" % (len(domains))
print "Total instances: %d" % (tot_istances)
print "Versions:"
for version in versions:
	print "\t%s [%d instances]" % (version, versions[version])
print ""

# Capture our current directory
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_report(p_versions, p_domains):
	j2_env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)
	out_file = open("report.html","w")
	out_file.write(j2_env.get_template('template.html').render(versions=p_versions, domains=p_domains))
	out_file.close()
	print "Report generated: report.html"

if __name__ == '__main__':
    generate_report(versions, domains)
