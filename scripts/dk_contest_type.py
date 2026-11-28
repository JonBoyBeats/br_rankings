"""The one contest-type definition (2026-11-28, the operator via the coordinator): the DK page's contest profile,
mirrored exactly from dk.html profileAuto (and ticketTables, which marks a qualifier / satellite with prizes as a
ticket). Everything that assigns a contest type imports this; nothing restates the rule.

  profile(name, size, prizes=0)  the page's profile: flagship / lab / main / qualifier
      flagship   Pull Up Jumper; by size, 100-799 entries (the High Five, a late add)
      lab        Dime Time
      main       And-One, Quarter Jukebox; by size, 800+ entries
      qualifier  a qualifier / satellite (ticket); by size, under 100 entries
  contest_type(name, size, prizes=0)  the three-way type the grading reports: the profile, with lab counted as main
      (the page fills Dime Time Max ROI, as a main)

size is the contest's size as the page reads it (the lobby's c.size, its maximum entries)."""
import re


def profile(name, size, prizes=0):
    nm, n = name or "", int(size or 0)
    if re.search(r"pull up jumper", nm, re.I):
        return "flagship"
    if re.search(r"dime time", nm, re.I):
        return "lab"
    if re.search(r"and-one|quarter jukebox", nm, re.I):
        return "main"
    if re.search(r"qualifier|satellite", nm, re.I):      # c.ticket (prizes > 0 and this name) is a subset of it
        return "qualifier"
    return "qualifier" if n < 100 else "flagship" if n < 800 else "main"


def contest_type(name, size, prizes=0):
    p = profile(name, size, prizes)
    return "main" if p == "lab" else p
