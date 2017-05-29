#!/usr/bin/env python
# file2zone.py - convert a file into b64 encoded DNS TXT records
# Project Repos:  https://bitbucket.org/memoryresident/file2zone
#                 https://github.com/glens/file2zone
# Author URL:     https://glenscott.net

import sys
import argparse
import hashlib
from base64 import b64encode


def makezone(args):
    filename = args.filename
    domain = args.domain

    if args.subdomain:
        subdomain = args.subdomain
    else:
        subdomain = ""

    with open(filename, 'rb') as infile:
    # todo: add a check for already compressed files, otherwise compress with zip
        infile_data = infile.read()
        b64_infile = b64encode(infile_data)
        filehash = hashfile(infile_data)
        filesize = len(infile_data)

    record_length = 255

    infile_chunked = [b64_infile[i:i+record_length] for i in range(0, len(b64_infile), record_length)]

    zonetxt = '''
$TTL 1m ; default TTL is 1 min
$ORIGIN %s.
@               IN      SOA   ns.%s. hostmaster.%s. (
                2003080800 ; serial number
                1m         ; refresh =  1 min 
                15M        ; update retry = 15 minutes
                1h      	; expiry = 1 hour
                2h20M      ; minimum = 2 hours + 20 minutes
                )
; main domain name servers
                IN      NS     ns.%s.

''' % (domain, domain, domain, domain)

    totalchunks = str(len(infile_chunked))

    metainf = "%s %s %s" % (totalchunks, b64encode(filename), filehash)

    # todo: work out max length for names below and put a warning into the script execution

    script1 = b64encode('foreach($i in 1..%s){(Resolve-DNSName -type txt "$i.%s.%s").Strings|Out-File -encoding ascii -append out.b64}' % (totalchunks, subdomain, domain))
    script2 = b64encode('Set-Content -Encoding Byte -Path out.bin -Value $([System.Convert]::FromBase64String($(Get-Content "out.b64")))')

    if len(script1) > 255:
        sys.exit("Error: Encoded script1 record is too long!")

    if len(script2) > 255:
        sys.exit("Error: Encoded script2 record is too long!")

    zonetxt += "meta.%s 60 IN TXT \"%s\"\n" % (subdomain, metainf)
    zonetxt += "s1.%s 60 IN TXT %s\n" % (subdomain, script1)
    zonetxt += "s2.%s 60 IN TXT %s\n" % (subdomain, script2)
    count = 1

    for line in infile_chunked:
        '''
        deliberate omission of quotations around txt record data here
        as the quotes cause issues with the zone2sql script.
        since all records are 255char base64 there should be no spaces to cause issue
        '''
        zonetxt += "%d.%s 60 IN TXT %s\n" % (count, subdomain, line)
        count += 1

    zonetxt += "\n\n"
    zonetxt += ";Created by file2zone. \n"
    zonetxt += ";github.com/glens/file2zone\n"
    zonetxt += "\n"
    zonetxt += ";Summary:\n"
    zonetxt += ";filename:      %s\n" % str(filename)
    zonetxt += ";filesize:      %s\n" % str(filesize)
    zonetxt += ";b64 size:      %i\n" % len(b64_infile)
    zonetxt += ";txt records:   %i\n" % count

    return zonetxt


def outputzone(zonetext, args):
    if args.outfile:
        outfile = args.outfile

        with open(outfile, "w") as text_file:
            text_file.write(zonetext)

        print "Zone written to %s" % outfile

    else:
        print zonetext


def hashfile(infile):
    # Choose whichever type of hash keeping in mind the hexdigest needs to fit within the 255 char
    # TXT record limit. (SHA1 is 40 chars).
    filehash = hashlib.sha1(infile)
    return filehash.hexdigest()


def main():
    parser = argparse.ArgumentParser(description='file2zone - convert a file into b64 encoded DNS TXT records.')

    parser.add_argument("filename", help='filename to encode into zone')
    parser.add_argument("domain", help='domain name of the target zone')
    parser.add_argument("-subdomain", help='subdomain to use for this file encoding. Default is to use the parent domain with no subdomain.')
    parser.add_argument("-outfile", help='filename to save the zone to. If this is not specified output is to stdout')
    args = parser.parse_args()

    zonetext = makezone(args)
    outputzone(zonetext, args)


if __name__ == '__main__':
    main()
