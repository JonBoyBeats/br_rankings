"""Each arm's live version on a DraftKings CBB slate, from analysis/cbb/dk/arm_versions.json (2026-11-25): the one
definition the night record (cbb_daily.py, ver_* columns) and the scorecard (dk_eval.py scorecard) read.

Arms: projection, ownership, field (the simulated field), cut (cut settings), fill (fill profile), late_swap. A version
holds from its date on, or with first_slate from that draft group on its first day (DraftKings numbers a day's draft
groups in start order)."""
import json, os

ARM_VERSIONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk", "arm_versions.json")
ARMS = ("projection", "ownership", "field", "cut", "fill", "late_swap")


def load(path=ARM_VERSIONS):
    return json.load(open(path, encoding="utf-8"))["arms"]


def live(v, date, group):
    """Whether version v holds on the slate (date, draft group)."""
    if date != v["from"]:
        return date > v["from"]
    return not v.get("first_slate") or int(group) >= int(v["first_slate"])


def version(arm, date, group, arms=None):
    """(version, the one before it) for the arm on that slate; (None, None) before its first."""
    hist = (arms or load())[arm]
    on = [k for k, v in enumerate(hist) if live(v, date, str(group))]
    if not on:
        return None, None
    k = on[-1]
    return hist[k], (hist[k - 1] if k else None)


def tags(date, group, arms=None):
    """{ver_<arm>: tag} for a night record row."""
    arms = arms or load()
    return {"ver_" + a: (version(a, date, group, arms)[0] or {}).get("tag", "") for a in ARMS}
