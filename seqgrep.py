#!/usr/bin/env python
"""A grep for sequence files.
"""


#--- standard library imports
#
import os
import sys
import logging
# optparse deprecated from Python 2.7 on
from optparse import OptionParser
import re
import gzip

#--- third-party imports
#
from Bio import SeqIO
from Bio.Seq import Seq

#--- project specific imports
#
#/
                                                        
__author__ = "Andreas Wilm"
__version__ = "0.1"
__email__ = "wilma@gis.a-star.edu.sg"
__license__ = "The MIT License (MIT)"


#global logger
# http://docs.python.org/library/logging.html
LOG = logging.getLogger("")
logging.basicConfig(level=logging.WARN,
                    format='%(levelname)s [%(asctime)s]: %(message)s')

  
def guess_seqformat(fseq):
    """Guess sequence format from file extension used by SeqIO
    """
    default = 'fasta'

    # Table for guessing the alignment format from the file extension.
    # See http://www.biopython.org/wiki/SeqIO
    #
    # Only define the ones I actually came accors here:
    ext_to_fmt_table = dict(
        aln = 'clustal',
        embl = 'embl',
        fasta = 'fasta',
        fa = 'fasta',
        genbank = 'genbank',
        gb = 'genbank',
        phylip = 'phylip',
        phy = 'phylip',
        ph = 'phylip',
        pir = 'pir',
        stockholm = 'stockholm',
        st = 'stockholm',
        stk = 'stockholm')

    try:
        fext = os.path.splitext(fseq)[1]
        fext = fext[1:].lower()
        fmt =  ext_to_fmt_table[fext]
    except KeyError:
        return default

    return fmt


def cmdline_parser():
    """
    creates an OptionParser instance
    """

    # http://docs.python.org/library/optparse.html
    usage = "%prog: " + __doc__ + "\n" \
            "usage: %prog [options] file[s]"
    parser = OptionParser(usage=usage)

    choices = ['seq', 'id']
    default = "id"
    parser.add_option("-s", "--search-in",
                      dest="search_in",
                      default=default, choices=choices,
                      help="Search in sequence or its name (one of %s; default %s)" % (choices, default))
    parser.add_option("", "--verbose",
                      action="store_true", 
                      dest="verbose",
                      help="be verbose")
    parser.add_option("", "--debug",
                      action="store_true", 
                      dest="debug",
                      help="debugging")
    parser.add_option("", "--revcomp",
                      action="store_true", 
                      dest="revcomp",
                      help="Reverse complement search string")
    parser.add_option("-i", "--ignore-case",
                      action="store_true", dest="ignore_case",
                      help="Make search case sensitive")
    parser.add_option("-v", "--invert-match",
                      action="store_true", dest="invert_match",
                      help="invert sense of matching")
    return parser


def main():
    """
    The main function
    """


    parser = cmdline_parser()
    (opts, args) = parser.parse_args()

    if opts.verbose:
        LOG.setLevel(logging.INFO)
    if opts.debug:
        LOG.setLevel(logging.DEBUG)
        
    if len(args)<2:
        parser.error("Need pattern and at least one seqfile as argument")
        sys.exit(1)

    
    # first arg is pattern. rest are files
    pattern_arg = args[0]
    if opts.revcomp:
        pattern_arg = str(Seq(pattern_arg).reverse_complement())
        LOG.info("Pattern after reverse complement: %s" % pattern_arg)
    seqfiles_arg = args[1:]
    LOG.debug("args=%s" % (args))
    LOG.debug("pattern_arg=%s" % (pattern_arg))
    LOG.debug("seqfiles_arg=%s" % (seqfiles_arg))

    if opts.ignore_case:
        regexp = re.compile(pattern_arg, flags=re.IGNORECASE)
    else:
        regexp = re.compile(pattern_arg)

        
    for fseq in seqfiles_arg:
        if fseq != "-" and not os.path.exists(fseq):
            LOG.fatal("input file %s does not exist.\n" % fseq)
            sys.exit(1)

    print_file_prefix = False
    if len(seqfiles_arg)>1:
        print_file_prefix = True
        
    for fseq in seqfiles_arg:
        if fseq == "-":
            fhandle = sys.stdin
        else:
            if fseq[-3:] == ".gz":
                fhandle = gzip.open(fseq)
            else:
                fhandle = open(fseq, "rU")
        
        fmt = guess_seqformat(fseq)
        if not fmt:
            fmt = 'fasta'
        LOG.info("Checking file %s (format %s)" % (fseq, fmt))
        
        for record in SeqIO.parse(fhandle, fmt):
            #LOG.debug("checking seq %s (len %d)" % (record.id, len(record.seq)))

            if opts.search_in == 'seq':
                target = record.seq
            elif opts.search_in == 'id':
                # special case fasta: id is everything before the
                # first whitespace. description contains this as well.
                if fmt == 'fasta':
                    target = record.description
                else:
                    target = record.id
            else:
                raise ValueError, (
                    "internal error...not sure where to search in")
            
            target = str(target)
            match = regexp.search(target) 
            print_match = False
            if match and not opts.invert_match:
                LOG.debug("match.string=%s" % match.string)
                print_match = True
            elif opts.invert_match and not match:
                print_match = True

            if print_match:
                #import pdb; pdb.set_trace()
                prefix = ""
                if print_file_prefix:
                    prefix = fseq + ":"
                if fmt == 'fasta':
                    print "%s>%s\n%s%s" % (prefix, record.description, prefix, record.seq)
                else:
                    print "%s>%s\n%s%s" % (prefix, record.id, prefix, record.seq)
        if fhandle != sys.stdin:
            fhandle.close()
            

if __name__ == "__main__":
    main()
    LOG.debug("FIXME: Add support coloured output, length filtering, support output format arg.")


