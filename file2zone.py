#!/usr/bin/env python

# file2zone by Glen Scott
# glenscott.net
# bitbucket.org/memoryresident
# github.com/glens

import sys
from base64 import b64encode

if len(sys.argv) <= 2:
	sys.exit('specify a file and zone name')

filearg = sys.argv[1]
zonename = sys.argv[2]

infile = open(filearg, 'rb')

b64_infile = b64encode(infile.read())

record_length = 255

# change the below values to your custom domain and subdomain to store this particular file
tld = 'domain.tld'
subdomain = zonename + ".subdomain"

infile_chunked = [b64_infile[i:i+record_length] for i in range(0, len(b64_infile), record_length)]

# cook a zone file
print '''
$TTL 1m ; default TTL is 1 min
$ORIGIN %s.
@              IN      SOA   ns.%s. hostmaster.%s. (
               2003080800 ; serial number
               1m         ; refresh =  1 min 
               15M        ; update retry = 15 minutes
               1h      	; expiry = 1 hour
               2h20M      ; minimum = 2 hours + 20 minutes
               )
; main domain name servers
              IN      NS     ns.%s.

''' % (tld, tld, tld, tld)

totalchunks = str(len(infile_chunked))

metainf = totalchunks + " " + b64encode(filearg)

#need to work out max length for names below and put a warning into the script execution

script1 = b64encode('foreach($i in 1..%s){(Resolve-DNSName -type txt "$i.%s.%s").Strings|Out-File -encoding ascii -append out.b64}' % (totalchunks, subdomain, tld))
script2 = b64encode('Set-Content -Encoding Byte -Path out.bin -Value $([System.Convert]::FromBase64String($(Get-Content "out.b64")))')

if len(script1) > 255:
  sys.exit("Error: Encoded script1 record is too long!")
if len(script2) > 255:
  sys.exit("Error: Encoded script2 record is too long!")

print "meta.%s 60 IN TXT \"%s\"" % (subdomain, metainf)
print "s1.%s 60 IN TXT %s" % (subdomain, script1)
print "s2.%s 60 IN TXT %s" % (subdomain, script2)
count = 1
for line in infile_chunked:
  # deliberate omission of quotations around txt record data here
  # as the quotes cause issues with the zone2sql script.
  # since all records are 255char base64 there should be no spaces to cause issue
  print "%d.%s 60 IN TXT %s" % (count, subdomain, line) 
  count += 1

print "\n\n"
print ";Zone Created. Summary:"
print ""
print ";filename:  %s" % (str(filearg))
print ";filesize:  %i" % (len(infile.read()))
print ";b64 size:  %i " % (len(b64_infile))
print ";txt count: %i" % (count)

infile.close()