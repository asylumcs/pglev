#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  pglev.py
  MIT license (c) 2021 Asylum Computer Services LLC
  https://asylumcs.net
"""

import re
import os
import sys
import pprint
import argparse
import datetime
from time import gmtime, strftime


def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(
                    1 + min((distances[i1], distances[i1 + 1], distances_[-1]))
                )
        distances = distances_
    return distances[-1]


class Pglev(object):
    def __init__(self, args):
        self.srcfile = args["infile"]
        self.outfile = args["outfile"]
        self.verbose = args["verbose"]
        self.wb = []
        self.wmap = {}  # word map
        self.ddict = {}  # dictionary words
        self.report = []  # report to save in outfile
        self.pnames = {}  # proper names dictionary
        self.encoding = ""
        self.root = os.path.dirname(os.path.realpath(__file__))
        self.pp = pprint.PrettyPrinter(indent=4)
        self.bwlist = []  # words that will be checked
        self.NOW = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " GMT"
        self.VERSION = "2020.12.28"

    # display (fatal) error and exit
    def fatal(self, message):
        sys.stderr.write("fatal: " + message + "\r\n")
        exit(1)

    # load wb from specified source file
    # accept either UTF-8 or Latin-1 and remember which for output
    def loadFile(self):
        try:
            wbuf = open(self.srcfile, "r", encoding="UTF-8").read()
            self.encoding = "UTF-8"
            self.wb = wbuf.split("\n")
        except UnicodeDecodeError:
            wbuf = open(self.srcfile, "r", encoding="Latin-1").read()
            self.encoding = "Latin-1"
            self.wb = wbuf.split("\n")
        except:
            self.fatal("loadFile: cannot open source file {}".format(self.srcfile))
        self.wb = [s.rstrip() for s in self.wb]

    # load dictionary
    def loadDict(self):
        tmpdict = []
        try:
            wbuf = open(self.root + "/wordlist.txt", "r", encoding="UTF-8").read()
            tmpdict = wbuf.split("\n")
        except:
            self.fatal("loadFile: cannot open dictionary")
        tmpdict = [s.rstrip() for s in tmpdict]
        self.ddict = set(tmpdict)

    # this splits the words on each line and populates the wtext map
    # the map is the word and a list; the list is
    #  (bool) T/F if it is a dictionary word
    #  (int) count of how many times it occurs
    #  (string) comma separated list of the line number(s) where it appears
    def splitWords(self):
        totalwords = 0
        # for each line
        for n, s in enumerate(self.wb):
            s = re.sub(r"(\w)'(\w)", r"\1ᒽ\2", s)  # internal apostrophe
            s = re.sub(r"(\w)’(\w)", r"\1ᒽ\2", s)  # internal apostrophe (curly)
            s = re.sub(r"(\w)-(\w)", r"\1ᗮ\2", s)  # internal hyphen
            s = re.sub(r"_", r" ", s)  # italics markup
            s = re.sub(r"=", r" ", s)  # bold markup
            s = re.sub(r"\W", r" ", s)

            # into a short list
            words = s.split(" ")

            # restore apostrophes, internal hyphens
            for i, word in enumerate(words):
                if word == "":
                    continue
                words[i] = re.sub(
                    r"ᒽ", r"'", words[i]
                )  # replace apostrophe (also straightens)
                words[i] = re.sub(r"ᗮ", r"-", words[i])  # replace hyphen

            # ignore Roman numerals
            for i, word in enumerate(words):
                s = re.sub(r"[ivxlcIVXLC]", r"", word)
                if s == "":
                    del words[i]

            totalwords += len(words)
            # go through the list of words and populate the map
            for i, _ in enumerate(words):

                # if a word is capitalized, test to see if it's a proper name
                # simple test: if in lower case it's a dictionary word then
                # don't classify it as a proper name. misses some i.e. "Frank"

                wlower = True
                if words[i].capitalize() == words[i]:
                    # starts with a capital leter
                    if (
                        words[i].lower() not in self.ddict
                        and "'" not in words[i]
                        and len(words[i]) >= 4
                    ):
                        wlower = False
                        if words[i] in self.pnames:
                            self.pnames[words[i]] = self.pnames[words[i]] + 1
                        else:
                            self.pnames[words[i]] = 1

                if wlower:
                    words[i] = words[i].lower()

                # create or modify an entry in the map
                # fewer than three letters are ignored completely
                if len(words[i]) > 3:
                    if words[i] not in self.wmap:
                        self.wmap[words[i]] = [False, 0, "{},".format(n)]  # first entry
                    else:
                        self.wmap[words[i]] = [
                            False,
                            0,
                            self.wmap[words[i]][2] + "{},".format(n),
                        ]  # additional entry
        if self.verbose:
            print("total words {}".format(totalwords))

        # map is built with all "False" and 0 for count.
        # once through to fix that an clean up trailing comma
        for key in self.wmap:
            # look up word
            if key in self.ddict:
                self.wmap[key][0] = "True"
            else:
                self.wmap[key][0] = "False"
            # hyphenated words always checked
            if "-" in key:
                self.wmap[key][0] = "False"
            # count occurrences
            self.wmap[key][1] = self.wmap[key][2].count(",")
            # strip trailing comma
            self.wmap[key][2] = self.wmap[key][2][:-1]

        # create a list of words not in dictionary
        for key in self.wmap:
            if self.wmap[key][0] == "False":
                self.bwlist.append(key)
        # print(self.bwlist, len(self.bwlist), len(self.wmap))
        # now reduce the number of words in bwlist
        for i, word in enumerate(self.bwlist):
            # common contractions
            if word.endswith("n't") and word[:-3] in self.ddict:
                self.bwlist[i] = ""
            if word.endswith("'s") and word[:-2] in self.ddict:
                self.bwlist[i] = ""
            if word.endswith("'ve") and word[:-3] in self.ddict:
                self.bwlist[i] = ""
            if word.endswith("'re") and word[:-3] in self.ddict:
                self.bwlist[i] = ""
        self.bwlist = list(filter(None, self.bwlist))

    def crunch(self):
        if self.verbose:
            print("words to check: {}".format(len(self.bwlist)))
        for firstword in self.bwlist:
            if len(firstword) <= 5:
                continue
            for secondword in self.wmap:
                if levenshteinDistance(firstword, secondword) == 1:
                    if firstword in self.bwlist:
                        self.bwlist.remove(firstword)
                    if secondword in self.bwlist:
                        self.bwlist.remove(secondword)
                    # limit report
                    fwl = firstword.lower()
                    swl = secondword.lower()
                    # do not report Shoutin shoutin
                    if fwl == swl:
                        continue
                    # do not report equinoctials equinoctial
                    if fwl + "s" == swl or fwl == swl + "s":
                        continue
                    # do not report swimmin swimming
                    if fwl.endswith("g") and fwl[:-1] == swl:
                        continue
                    if swl.endswith("g") and swl[:-1] == fwl:
                        continue
                    # finally make an entry into the report
                    self.report.append(
                        "{} ({}) <=> {} ({})".format(
                            firstword,
                            self.wmap[firstword][1],
                            secondword,
                            self.wmap[secondword][1],
                        )
                    )
                    line1 = int(self.wmap[firstword][2].split(",")[0])
                    line2 = int(self.wmap[secondword][2].split(",")[0])
                    self.report.append("    {:5d} {}".format(line1, self.wb[line1]))
                    self.report.append("    {:5d} {}".format(line2, self.wb[line2]))

    # write the report in the same encoding as the source file
    #
    def saveReport(self):
        f1 = open(self.outfile, "w", encoding=self.encoding)
        f1.write("<pre>")
        f1.write("pglev run report\n")
        f1.write(f"run started: {str(datetime.datetime.now())}\n")
        f1.write("source file: {}\n".format(os.path.basename(self.srcfile)))
        f1.write(
            f"<span style='background-color:#FFFFDD'>close this window to return to the UWB.</span>\n"
        )
        f1.write("\n")
        for r in self.report:
            f1.write("{:s}\n".format(r))
        f1.write("</pre>")
        f1.close()

    def run(self):
        self.loadFile()
        self.loadDict()
        self.splitWords()
        self.crunch()
        self.saveReport()

    def __str__(self):
        return "pplev"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infile", help="input file", required=True)
    parser.add_argument("-o", "--outfile", help="output file", default="log-pplev.txt")
    parser.add_argument("-v", "--verbose", help="verbose", action="store_true")
    args = vars(parser.parse_args())
    return args


def main():
    args = parse_args()
    pglev = Pglev(args)
    pglev.run()


if __name__ == "__main__":
    sys.exit(main())
