#!/usr/bin/env python

# wbdiff.py - sophisticated diff utility
#
# Copyright: Witold Baryluk, 2013
#
# MIT license
#
# This is simplistic tool for detecting moved blocks
# and edits of code in text files.
#
# It can be used just like normal diff utility, but it additionally
# supports line movement detection, fuzzy matching, colored output,
# collapsing very long runs of similar lines / moves
# and runs up much slower.
#
# Algorithm is O(k*n^2*l^2), where k is context lenght, n number
# of lines, l lenght of lines.
#
# If no fuzzy matching is used, then algorithm is basically O(n^2*l).
#
# There are multiple features on the horizon, like automatic compressed
# files support, adaptative context length estimation, white space removal,
# custom replacments matching,
# speed optimizations for case of small number of block movements,
# side-by-side comparission (console and HTML)
# and graphical visualizer (using GraphViz probably) and GUI frontend.
#
# If you want to pipe output to less, use less -RS
#
# This script runs in 0.165 seconds on my benchmark (300 lines),
# compared to 0.019 seconds by diff -U 300 (unified diff, with big context).
#
# Difference is big, but this program should be usable for manual execution
# with files of about 5000 lines. For patches, and automatic execution
# classic diff algorithm is probably better because of O(n) algorithm used.
#
# Similar good programs, which can align codes in non-sequential manner:
#  WinDiff by Microsoft (free, comes with source code, runs under Windows, and WINE)
#    - very good results, but old UI
#  WinMerge (free open-source, for Windows, runs also on WINE, native port in preparation
#    - modern UI, but results are inferior
#  Araxis Merge by Araxis (commercial, for Windows, Mac OS X and WINE, with trial)
#    - very poor results
#    - even more advanced UI, but even more bad results, sometimes completly useless
#
# Other tools checked, which essentially doesn't support moved blocks detecion:
#   BeyondCompare by Scooter Software, Inc. (Mac OS X, Linux)
#   P4Merge: Visual Merge Tool by Perfore (Windows, Mac OS X, Linux)
#   DeltaWalker by Deltopia (Mac OS X, Windows, Linux)
#   DiffMerge by SourceGear (Windows, Mac OS X, Linux)
#   Code Compare by Devart (Windows)
#   ECMerge by Ellie Computing (Windows,Mac OS X, Linux, Solaris)
#   Compare It! by Grig Software (Windows)
#   Synchronize It! by Grig Software (Windows)
#   ExamDiff Pro by prestoSoft (Windows)
#   Open source: Meld, KDiff3, tkdiff, Advanced Diff (Linux, Windows, Mac OS X)
#
# Pretty sad, so many tools, non does main job good.
#
# I may think about creating GUI ala Meld, WinMerge, KDiff3 or Araxis Merge.
# I will probably use GTK+ (version 3), so stay tuned.


import sys

colors = True
line_prefixes = False
summary_left = False
summary_right = False
summary_stats = True
context_matching = 7   # 3..11 is sensible range
shorten_long_matches = 16 # lenght of biggest block to show, above that,
                          # we will split block in half, and show ...

import itertools

def iterseq(sequence):
  return zip(itertools.count(), sequence)

# http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
class _ansi:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = "\033[1m"

  def disable(self):
    self.HEADER = ""
    self.OKBLUE = ""
    self.OKGREEN = ""
    self.WARNING = ""
    self.FAIL = ""
    self.ENDC = ""
    self.BOLD = ""

ansi = _ansi()
if not colors:
  ansi.disable()

# Usage of backreferences in "regular expressions" here,
# is explicitly supported by wbdiff.
# They are not in formal sense a regular expressions,
# but they should be very short, simple, most of them
# should also be fast, and are very usefull here, so
# why not.
# Replacments are applied prior to comparision of lines,
# so they are usefull method of discarding common classes
# of small changes.
# They will still be displayed, but in slightly different way.
replacments = {
  "Incrementation": (r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\1\s*\+\s*1\b", r"\1++"),
  "Decrementation": (r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\1\s*-\s*1\b", r"\1--"),
  "Leading whitespace": (r"^\s+", r""),
  "Trailing whitespace": (r"\s+$", r""),
  "Log timestamp": (r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [012][0-9] [012][0-9]:[0-6][0-9]:[0-6][0-9] (\w+(?:\.\w+)*) kernel: \[ *[0-9]+\.[0-9]+\] ", r"\1  kernel:  ")
}

commonalize_diff_compact_delta = False

import difflib

def diff(a, b):
  d = difflib.Differ()
  di = d.compare(a.splitlines(True), b.splitlines(True))
  if commonalize_diff_compact_delta:
    di = filter(lambda x: x[0] != " ", di)
  return "".join(di)

def similarity(a, b):
  return difflib.SequenceMatcher(None, a, b).ratio()

def line_similarity(a, b):
  return similarity(a, b)

def similar(a, b, threshold):
  s = similarity(a, b)
  return s > threshold

leftfilename = sys.argv[1]
left = file(leftfilename).readlines()
rightfilename = sys.argv[2]
right = file(rightfilename).readlines()

import re

compiled = {}
for n, from_to in replacments.iteritems():
  compiled[n] = re.compile(from_to[0]) #, flags=re.IGNORECASE

def repl_(line):
  for n, from_to in replacments.iteritems():
    line = compiled[n].sub(from_to[1], line)
  return line

def repl(org):
  for i, line in iterseq(org):
    org[i] = repl_(line)
  return org

left = repl(left)
right = repl(right)

# compute similarity matrix
leftlen = len(left)
rightlen = len(right)
m = range(leftlen)
for i, a in iterseq(left):
  m[i] = range(rightlen)
  for j, b in iterseq(right):
    #m[i][j] = line_similarity(a, b)
    if a == b:
      m[i][j] = 1.0
    else:
      m[i][j] = 0.0

# use context for similarity measure
m2 = range(leftlen)
for i, a in iterseq(left):
  m2[i] = range(rightlen)
  for j, b in iterseq(right):
    s = 1.0
    kk = 1
    # extend using context, but do no go beyond context_matching limit or last lines
    for k in xrange(context_matching):
      if i+k<leftlen and j+k<rightlen:
        kk += 1
        if m[i+k][j+k] == 0.0:
          s = 0.0
          break
        #s *= m[i+k][j+k]
    #s = s ** (1.0/kk)
# some tweeking to weights
#    if s < 0.90:
#      s = 0.0
#    else:
#      s = (s-0.90)*10.0
#      s = 1.0 - (1.0-s)**2
    m2[i][j] = s

matched_left = [False]*leftlen
matched_right = [False]*rightlen


LL = ""
RR = ""
EE = ""
if line_prefixes:
  LL = "l"
  RR = "r"
  EE = " "

blocks_right = {}

# search for long common subsequences, and extend them.
for j, _b in iterseq(right):
  if matched_right[j]:
    continue
  for i, _a in iterseq(left):
    if matched_left[i]:
      continue
    if m2[i][j] > 0.95:
      matched_left[i] = True
      matched_right[j] = True
      k = 0
      while i+k < leftlen and j+k < rightlen and m[i+k][j+k] > 0.95: # m not m2 !
        matched_left[i+k] = True
        matched_right[j+k] = True
        k += 1
      blocks_right[j] = (i, k)

left_right_matched = 0
left_removed = 0
right_added = 0

def blue(s):
  return ansi.OKBLUE+s+ansi.ENDC
def red(s):
  return ansi.FAIL+s+ansi.ENDC
def green(s):
  return ansi.OKGREEN+s+ansi.ENDC

W=2
if leftlen > 99 or rightlen > 99:
  W = 3
if leftlen > 999 or rightlen > 999:
  W = 4
W += 1 # workaround around IMHO % 3d bug, TODO(baryluk): fix it

WW="%s% "+str(W)+"d"
WL=LL+"% "+str(W)+"d"
WR=RR+"% "+str(W)+"d"
XX=EE+" "*W

# Print common subsequences, intermixing new lines (in natural order), and removed ones (just after end of moved ones)
print red("Removals")+" from left file, "+blue("moves")+" and "+green("additions")+" to right file:"
print red("--- "+leftfilename)
print green("+++ "+rightfilename)

# first print lines removed from left file, before any blocks in right file
for i, a in iterseq(left):
  if not matched_left[i]:
    left_removed += 1
    print (WL+"->"+XX+" "+red("- %s")) % (i+1, a.rstrip())
  else:
    break

# right centric view

for j, _b in iterseq(right):
  if j in blocks_right:
    i, k = blocks_right[j]
    print "-"*(2*W+3) + "\\ l%04d-l%04d -> r%04d-r%04d  (%d lines)" % (i+1, i+k+1, j+1, j+k+1, k)
    was_shortened = False
    for kk in xrange(k):
      left_right_matched += 1
      c = "|"
      if kk < shorten_long_matches/2 or kk>(k-shorten_long_matches/2):
        print (WL+"->"+WR+" "+blue("%s %s")) % (i+kk+1, j+kk+1, c, left[i+kk].rstrip())
      else:
        if was_shortened:
          continue
        print " "+"."*(W-1)+"->"+" "+"."*(W-1)+" "+blue(":")
        print " (%d lines skiped)" % (k-shorten_long_matches+1,)
        print " "+"."*(W-1)+"->"+" "+"."*(W-1)+" "+blue(":")
        was_shortened = True
    print "-"*(2*W+3) + "/"
    i = i+k
    while i < leftlen and not matched_left[i]:
      left_removed += 1
      print (WL+"->"+XX+" "+red("- %s")) % (i+1, left[i].rstrip())
      i += 1
  if not matched_right[j]:
    right_added += 1
    print (XX+"->"+WR+" "+green("+ %s")) % (j+1, _b.rstrip())

if summary_left:
  print red("Removed")+" from left file:"
  for i, _a in iterseq(left):
    if not matched_left[i]:
      if i > 0 and matched_left[i-1]:
        print "-----"
      print (WL+"->"+XX+" "+red("- %s")) % (i+1, _a.rstrip())

if summary_right:
  print green("Added")+" to right file"
  for j, _b in iterseq(right):
    if not matched_right[j]:
      if i > 0 and matched_right[j-1]:
        print "-----"
      print (XX+"->"+WR+" "+green("+ %s")) % (j+1, _b.rstrip())

if summary_stats:
  print
  print ansi.WARNING+"Diff statistics:"
  print "\tInitial context length used:", context_matching
  print "\tNumber of matching (extended) blocks:", len(blocks_right)
  print "\tNumber of lines in matching (extended) blocks:", left_right_matched, sum(map(lambda x: x[1], blocks_right.itervalues()))
  print "\tNumber of lines removed from left file:", left_removed
  print "\tNumber of new lines added to right file:", right_added
  print ("\tWeighted cost (blocks + removed + added): %s"+ansi.ENDC) % (len(blocks_right)-1 + left_removed + right_added,)

