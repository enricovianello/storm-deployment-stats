#!/usr/bin/python

import sys
import ldap
from jinja2 import Environment, FileSystemLoader
import os

class Site:

	def __init__(self, name):
		self.name = name
		self.hosts = []

	def addHost(self, host):
		self.hosts.append(host)
		self.hosts.sort(key=lambda host: host.getHostname())

	def getHosts(self):
		return self.hosts

	def isHost(self, hostname):
		return len(self.getHost(hostname)) > 0

	def getHost(self, hostname):
		return [host for i,host in enumerate(self.hosts) if host.getHostname() == hostname]

	def getName(self):
		return self.name

	def __eq__(self, other):
		return self.name == other.getName()

	def __str__(self):
		return "{ Name: %s, Hosts: [%s] }" % (self.name, ", ".join(str(x) for x in self.hosts))

class Host:

	def __init__(self, hostname, version):
		self.hostname = hostname
		self.version = version
		self.SRMendpoint = None
		self.DAVendpoint = None
		self.glue2 = False
		self.glue1 = False

	def setGlue2(self):
		self.glue2 = True

	def setGlue1(self):
		self.glue1 = True

	def setVersion(self, version):
		self.version = version

	def addSRMEndpoint(self, endpoint):
		self.SRMendpoint = endpoint

	def getSRMEndpoint(self):
		return self.SRMendpoint

	def addDAVEndpoint(self, endpoint):
		self.DAVendpoint = endpoint

	def getDAVEndpoint(self):
		return self.DAVendpoint

	def isGlue2(self):
		return self.glue2

	def isGlue1(self):
		return self.glue1

	def getHostname(self):
		return self.hostname

	def getVersion(self):
		return self.version

	def __eq__(self, other):
		return self.hostname == other.getHostname()

	def __str__(self):
		return "{ Hostname: %s, Version: %s, Endpoint SRM: [%s], Endpoint DAV: [%s], Glue2: %r, Glue1: %r }" \
			% (self.hostname, self.version, self.SRMendpoint, self.DAVendpoint, \
				self.glue2, self.glue1)

class Endpoint:

	def __init__(self, protocol, url, version):
		self.protocol = protocol
		self.url = url
		self.version = version

	def getProtocol(self, protocol):
		return self.protocol

	def getURL(self):
		return self.url

	def getVersion(self):
		return self.version

	def __eq__(self, other):
		return self.url == other.getURL()

	def __str__(self):
		return "{ Protocol: %s, URL: %s, Version: %s }" \
			% (self.protocol, self.url, self.version)

class Stats:

	def __init__(self):
		self.numSites = 0
		self.numHosts = 0
		self.stormVersions = dict()

	def incSites(self):
		self.numSites += 1

	def incHosts(self):
		self.numHosts += 1

	def incStormVersions(self, version):
		if not version in self.stormVersions:
			self.stormVersions[version] = 0
		self.stormVersions[version] += 1

	def getNumSites(self):
		return self.numSites

	def getNumHosts(self):
		return self.numHosts

	def getStormVersions(self):
		return self.stormVersions


def findSite(sites, sitename):
	site = [s for i,s in enumerate(sites) if s.getName() == sitename]
	return site[0] if len(site) > 0 else None

def findHost(hosts, hostname):
	host = [h for i,h in enumerate(hosts) if h.getHostname() == hostname]
	return host[0] if len(host) > 0 else None


def openLDAPConnection(hostname, port):

	print "Opening LDAP connection to %s:%d ..." % (hostname, port)
	## open connection to the top bdii
	try:
		l = ldap.open(host=hostname, port=port)
		## searching doesn't require a bind in LDAP V3.  If you're using LDAP v2, set the next line appropriately
		## and do a bind as shown in the above example.
		# you can also set this to ldap.VERSION2 if you're using a v2 directory
		# you should  set the next option to ldap.VERSION2 if you're using a v2 directory
		l.protocol_version = ldap.VERSION3
	except ldap.LDAPError, e:
		print e
		quit()
		# handle error however you like
	return l

def ldapQuery(connection, baseDN, searchScope, retrieveAttributes, searchFilter):

	print "baseDN:              " + baseDN
	print "search filter:       " + searchFilter
	print "retrieve attributes: " + ', '.join(retrieveAttributes)

	try:
		ldap_result_id = connection.search(baseDN, searchScope, searchFilter, retrieveAttributes)
		result_set = []
		while 1:
			result_type, result_data = connection.result(ldap_result_id, 0)
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

def glue2Find(connection, retrieveAttributes, searchFilter):

	baseDN = "GLUE2GroupID=grid,o=glue"
	searchScope = ldap.SCOPE_SUBTREE
	return ldapQuery(connection, baseDN, searchScope, retrieveAttributes, searchFilter)

def glue1Find(connection, retrieveAttributes, searchFilter):

	baseDN = "o=grid"
	searchScope = ldap.SCOPE_SUBTREE
	return ldapQuery(connection, baseDN, searchScope, retrieveAttributes, searchFilter)

def generate_report_html(stats, sites):
	j2_env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)
	out_file = open("report.html","w")
	out_file.write(j2_env.get_template('template.html').render(stats=stats, sites=sites))
	out_file.close()
	print "Report generated: report.html"

def generate_report_csv(sites):
	j2_env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)
	out_file = open("report.csv","w")
	out_file.write(j2_env.get_template('template.csv').render(sites=sites))
	out_file.close()
	print "Report generated: report.csv"

def generate_site_list_txt(sites):
	j2_env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)
	out_file = open("report.txt","w")
	out_file.write(j2_env.get_template('template.txt').render(sites=sites))
	out_file.close()
	print "Report generated: report.txt"

def printSitesTable(sites):

	print "\n%-18s\t%-25s\t%-10s\t%-50s\t%-10s\t%-60s\t%-10s\t%-6s\t%-6s" % \
		("Domain", "Hostname", "Version",  "WebDAV URL",  "WebDAV version", \
			"SRM URL",  "SRM version", "Glue2", "Glue1")

	for site in sites:
		for host in site.getHosts():
			print "%-18s\t%-25s\t%-10s\t%-50s\t%-10s\t%-60s\t%-10s\t%-6r\t%-6r" % \
				(site.getName(), host.getHostname(), host.getVersion(), \
					"-" if host.getDAVEndpoint() is None else host.getDAVEndpoint().getURL(), \
					"-" if host.getDAVEndpoint() is None else host.getDAVEndpoint().getVersion(), \
					"-" if host.getSRMEndpoint() is None else host.getSRMEndpoint().getURL(), \
					"-" if host.getSRMEndpoint() is None else host.getSRMEndpoint().getVersion(), \
					host.isGlue2(), host.isGlue1())

def printStatsSummary(stats):

	print "\n## Summary ##"
	print "Total sites: %d" % (stats.getNumSites())
	print "Total instances: %d" % (stats.getNumHosts())
	print "Versions:"
	for version,count in sorted(stats.getStormVersions().items(), reverse = True):
		print "\t%s [%d instances]" % (version, count)
	print ""


if __name__ == '__main__':

	# init variables
	sites = []
	stats = Stats()

	# Open LDAP connection
	ldapConnection = openLDAPConnection("egee-bdii.cnaf.infn.it", 2170)

	## GLUE2 QUERY: find all StoRM sites and backend hostnames
	result_set = glue2Find(ldapConnection, [], "GLUE2ServiceType=storm")

	n = len("/storage")

	for i in range(len(result_set)):
		for entry in result_set[i]:
			dn = entry[0]
			domain = dn.split(',')[2].split('=')[1].upper()
			hostname = dn.split(",")[0].split("=")[1][:-n]
			#print "%d.\tDomain: %-20s\tHostname: %-30s" % (i+1, domain, hostname)

			site = findSite(sites, domain)
			if site is None:
				site = Site(domain)
				sites.append(site)
				# UPDATE stats
				stats.incSites()

			host = findHost(site.getHosts(), hostname)
			if host is None:
				host = Host(hostname, "-")
				host.setGlue2()
				site.addHost(host)
				# UPDATE stats
				stats.incHosts()

	## GLUE2 QUERY: find all hostname versions
	result_set = glue2Find(ldapConnection, ["GLUE2ManagerProductVersion"], "GLUE2ManagerProductName=StoRM")

	for i in range(len(result_set)):
		for entry in result_set[i]:
			dn = entry[0]
			domain = dn.split(',')[3].split('=')[1].upper()
			version = entry[1]['GLUE2ManagerProductVersion'][0]
			hostname = dn.split(",")[1].split("=")[1][:-n]
			#print "%d.\tDomain: %-20s\tHostname: %-30s\tVersion: %-10s" % (i+1, domain, hostname, version)

			# UPDATE sites
			site = findSite(sites, domain)
			if site is None:
				print "Site %s not found!! ERROR!" % (domain)
				continue
			host = findHost(site.getHosts(), hostname)
			if host is None:
				print "Hostname %s not found in %s!! ERROR!" % (hostname, domain)
				continue
			host.setVersion(version)

			# UPDATE stats
			stats.incStormVersions(version)

	## GLUE2 QUERY: find all webdav endpoints
	result_set = glue2Find(ldapConnection, ["GLUE2EndpointURL", "GLUE2EndpointImplementationVersion"], \
		"(&(GLUE2EndpointInterfaceName=webdav)(GLUE2EndpointID=*HTTPS))")

	for i in range(len(result_set)):
		for entry in result_set[i]:
			dn = entry[0]
			domain = dn.split(',')[3].split('=')[1].upper()
			hostname = dn.split(",")[1].split("=")[1][:-n]
			URL = entry[1]['GLUE2EndpointURL'][0]
			version = entry[1]['GLUE2EndpointImplementationVersion'][0]
			#print "%d.\tDomain: %-20s\tHostname: %-30s\tURL: %-50s\tVersion: %-10s" % (i+1, domain, hostname, URL, version)

			# UPDATE sites
			site = findSite(sites, domain)
			if site is None:
				print "Site %s not found!! ERROR!" % (domain)
				continue
			host = findHost(site.getHosts(), hostname)
			if host is None:
				print "Hostname %s not found in %s!! ERROR!" % (hostname, domain)
				continue
			host.addDAVEndpoint(Endpoint("webdav", URL, version))

	## GLUE2 QUERY: find all SRM endpoints
	result_set = glue2Find(ldapConnection, ["GLUE2EndpointURL", "GLUE2EndpointImplementationVersion"], \
		"(&(GLUE2EndpointInterfaceName=SRM)(GLUE2EndpointID=*/storage/endpoint/SRM))")

	for i in range(len(result_set)):
		for entry in result_set[i]:
			dn = entry[0]
			domain = dn.split(',')[3].split('=')[1].upper()
			hostname = dn.split(",")[1].split("=")[1][:-n]
			URL = entry[1]['GLUE2EndpointURL'][0]
			version = entry[1]['GLUE2EndpointImplementationVersion'][0]
			#print "%d.\tDomain: %-20s\tHostname: %-30s\tURL: %-60s\tVersion: %-10s" % (i+1, domain, hostname, URL, version)

			# UPDATE sites
			site = findSite(sites, domain)
			if site is None:
				print "Site %s not found!! ERROR!" % (domain)
				continue
			host = findHost(site.getHosts(), hostname)
			if host is None:
				print "Hostname %s not found in %s!! ERROR!" % (hostname, domain)
				continue
			host.addSRMEndpoint(Endpoint("srm", URL, version))

	## GLUE1 QUERY: find all StoRM sites and backend hostnames
	result_set = glue1Find(ldapConnection, ["GlueInformationServiceURL", "GlueSEUniqueID", \
		"GlueSEImplementationVersion"], "GlueSEImplementationName=StoRM")

	for i in range(len(result_set)):
		for entry in result_set[i]:
			dn = entry[0]
			version = entry[1]['GlueSEImplementationVersion'][0]
			domain = dn.split(',')[1].split('=')[1].upper()
			hostname = entry[1]['GlueInformationServiceURL'][0].split("/")[2].split(":")[0]
			#print "%d.\tDomain: %-20s\tHostname: %-30s\tVersion: %-10s" % (i+1, domain, hostname, version)

			# UPDATE sites
			site = findSite(sites, domain)
			if site is None:
				site = Site(domain)
				host = Host(hostname,version)
				host.setGlue1()
				site.addHost(host)
				sites.append(site)
				#UPDATE stats
				stats.incStormVersions(version)
				stats.incSites()
				continue

			host = findHost(site.getHosts(), hostname)
			if host is None:
				host = Host(hostname,version)
				host.setGlue1()
				site.addHost(host)
				#UPDATE stats
				stats.incStormVersions(version)
				stats.incHosts()
				continue

			host.setGlue1()

	# order site by name
	sites.sort(key=lambda site: site.getName())

	printSitesTable(sites)
	printStatsSummary(stats)

	# Capture our current directory
	THIS_DIR = os.path.dirname(os.path.abspath(__file__))

	generate_report_html(stats, sites)
	generate_report_csv(sites)
	generate_site_list_txt(sites)
