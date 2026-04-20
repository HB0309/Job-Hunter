"""
Description-based skill matching for job prescreening.

Extracts years-of-experience requirements, entry-level signals, and technical
keywords from raw job descriptions, then scores them against the user's profile.

Returns a DescriptionVerdict that drives Stage 2 of the prescreen pipeline:
  - 'auto_reject'  — clearly wrong (too senior, wrong domain)
  - 'score'        — strong match, send to Claude scoring queue
  - 'review'       — ambiguous, flag for manual check
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

# ── Strip HTML ────────────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_RE = re.compile(r"&[a-z#0-9]+;")


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = _TAG_RE.sub(" ", text or "")
    text = _ENTITY_RE.sub(lambda m: html.unescape(m.group()), text)
    return re.sub(r"\s+", " ", text).strip().lower()


# ── Years-of-experience extraction ───────────────────────────────────────────

# Matches: "5+ years", "5-7 years", "minimum 5 years", "at least 5 years",
#          "5 years of experience", "five years"
_YOE_PATTERNS = [
    r"(\d+)\+?\s*(?:to\s*\d+)?\s*years?\s+(?:of\s+)?(?:professional\s+)?(?:software\s+)?(?:engineering\s+)?(?:work\s+)?experience",
    r"(\d+)\+\s*years?",
    r"minimum\s+(?:of\s+)?(\d+)\s+years?",
    r"at\s+least\s+(\d+)\s+years?",
    r"(\d+)\s*-\s*\d+\s+years?\s+(?:of\s+)?experience",
    r"(\d+)\s+years?\s+(?:of\s+)?(?:relevant|related|hands.on|professional)\s+experience",
]

_WORD_TO_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def extract_max_yoe(text: str) -> int | None:
    """Return the maximum years-of-experience found, or None.

    Uses max (not min) because job descriptions often have a low HR baseline
    ("1+ years relevant experience") followed by the real requirement
    ("5+ years of professional experience"). The max is the binding constraint.
    """
    text = _strip_html(text)
    # Replace written numbers
    for word, num in _WORD_TO_NUM.items():
        text = re.sub(rf"\b{word}\b", str(num), text)

    found = []
    for pat in _YOE_PATTERNS:
        for m in re.finditer(pat, text):
            try:
                found.append(int(m.group(1)))
            except (IndexError, ValueError):
                pass

    # Filter out noise (0 or unrealistically high numbers)
    valid = [y for y in found if 1 <= y <= 15]
    return max(valid) if valid else None


# ── Entry-level signals in description ───────────────────────────────────────

_ENTRY_LEVEL_DESC_PATTERNS = [
    r"\bnew\s+grad\b", r"\bnewgrad\b", r"\bnew\s+college\s+graduate\b",
    r"\brecent\s+grad(?:uate)?\b", r"\bfresh\s+grad(?:uate)?\b",
    r"\bentry.level\b", r"\bentry\s+level\b",
    r"\bearly.career\b", r"\bearly\s+career\b",
    r"\bcampus\s+hire\b", r"\bcampus\s+recruit\b",
    r"\bdesigned\s+for\s+grad",
    r"\b0[-–]\s*[12]\s+years?\b",              # 0-1 years, 0-2 years
    r"\b0\+\s*years?\b",
    r"\bno\s+professional\s+experience\s+required\b",
    r"\binternship.*(?:count|qualify|acceptable|considered)\b",
    r"\bacademic.*(?:project|experience|background).*(?:count|qualify|acceptable|considered)\b",
    r"\b(?:internship|co.op|academic)\s+experience\s+(?:is\s+)?(?:accepted|ok|acceptable|sufficient)\b",
    r"\b[123]\s+months?\s+of\s+(?:work\s+or\s+academic|experience)\b",
]


def has_entry_level_signal(text: str) -> bool:
    text = _strip_html(text)
    return any(re.search(p, text) for p in _ENTRY_LEVEL_DESC_PATTERNS)


# ── Security clearance detection ─────────────────────────────────────────────
# Any of these → auto-reject (user cannot meet clearance requirements as new grad).

_CLEARANCE_PATTERNS = [
    r"\bts/sci\b", r"\btop\s+secret\b", r"\bts\s*sci\b",
    r"\bsci\s+(?:eligible|required|clearance)\b",
    r"\bactive\s+(?:secret|ts|clearance)\b",
    # "Active US Security clearance" — words between active and clearance
    r"\bactive\s+(?:\w+\s+){0,3}security\s+clearance\b",
    r"\bsecret\s+clearance\b",
    r"\bdod\s+clearance\b", r"\bdod\s+secret\b",
    r"\bmust\s+(?:have|hold|possess)\s+(?:an?\s+)?(?:active\s+)?(?:security\s+)?clearance\b",
    r"\b(?<!not\s)(?<!no\s)requires?\s+(?:an?\s+)?(?:active\s+)?(?:security\s+)?clearance\b",
    r"\bability\s+to\s+obtain\s+(?:and\s+maintain\s+)?(?:a\s+)?(?:us\s+)?(?:security\s+)?clearance\b",
    # "willingness to obtain" / "eligibility to obtain" / "eligibility and willingness to obtain"
    r"\b(?:willingness|eligibility)\s+(?:and\s+\w+\s+)?to\s+obtain\s+(?:a\s+)?(?:us\s+)?(?:security\s+)?clearance\b",
    r"\bwilling\s+to\s+obtain\s+(?:a\s+)?(?:us\s+)?(?:security\s+)?clearance\b",
    r"(?<!no\s)(?<!not\s)\bclearance\s+(?:is\s+)?(?:required|needed|mandatory|preferred)\b",
    r"(?<!no\s)(?<!not\s)\bsecurity\s+clearance\s+(?:is\s+)?(?:required|needed|mandatory|preferred)\b",
    r"\bpolygraph\b",
    r"\bci\s+poly\b", r"\bfull\s+scope\s+poly\b", r"\bfs\s+poly\b",
    r"\bpublic\s+trust\s+(?:clearance|investigation)\b",
    r"\bsensitive\s+compartmented\s+information\b",
    r"\bclearance\s+eligible\b",
    r"\beligible\s+for\s+(?:a\s+)?(?:us\s+)?(?:security\s+)?clearance\b",
]


# Phrases that explicitly say clearance is NOT required — cancel any positive match.
_CLEARANCE_NEGATIONS = re.compile(
    r"\bno\s+(?:security\s+)?clearance\s+(?:is\s+)?(?:required|needed|necessary)\b"
    r"|\b(?:does?\s+not|don'?t)\s+require\s+(?:a\s+)?(?:security\s+)?clearance\b"
    r"|\bclearance\s+(?:is\s+)?not\s+required\b",
    re.IGNORECASE,
)


def has_clearance_requirement(text: str) -> bool:
    """Return True if the description mentions any security clearance requirement."""
    text = _strip_html(text)
    if _CLEARANCE_NEGATIONS.search(text):
        return False
    return any(re.search(p, text) for p in _CLEARANCE_PATTERNS)


# ── Domain mismatch detection ─────────────────────────────────────────────────
# Jobs in these domains are almost certainly a mismatch with the user's SWE/security profile.

_WRONG_DOMAIN_SIGNALS = [
    # Semiconductor / hardware fabrication
    r"\bfpga\b", r"\bverilog\b", r"\bvhdl\b", r"\basic\b(?!\s+understanding)",
    r"\bwafer\b", r"\bsemiconductor\s+fab\b", r"\betch\s+process\b",
    r"\bcvd\b", r"\bpvd\b", r"\blithograph\b", r"\bmetrology\b",
    r"\bsoc\s+design\b", r"\bcpu\s+design\b", r"\bcircuit\s+design\b",
    r"\brtl\s+design\b", r"\bip\s+design\b", r"\bchip\s+design\b",
    r"\bsilicon\s+photonics\b", r"\bpackaging\s+integration\b",
    r"\bfoundry\s+(?:automation|process|module)\b",
    r"\bfab\s+automation\b", r"\bfab\s+(?:engineer|module|process)\b",
    r"\bprocess\s+integration\b(?!.*software)",
    r"\bdiffusion\s+process\b",
    # Enterprise legacy / niche
    r"\bcobol\b", r"\babap\b", r"\bsap\s+(?:hana|erp|s\/4)\b",
    r"\bas\/400\b", r"\bpowerbuilder\b", r"\bfortran\b",
    # Hardware/embedded only (no SWE angle)
    r"\bpcb\s+design\b", r"\bschematic\b(?!.*software)", r"\bfirmware\s+engineer\b",
    r"\bembedded\s+c\b(?!.*linux)", r"\bmicrocontroller\b(?!.*python)",
    # Field/facilities
    r"\bdata\s+center\s+(?:technician|facilities|critical\s+facilities)\b",
    r"\bfacilities\s+engineer\b",
    r"\bmechanical\s+engineer\b(?!.*software)",
    r"\belectrical\s+engineer\b(?!.*software)",
]

# If the description has ANY of these, it's a hard domain reject
_DOMAIN_OVERRIDE_SIGNALS = [
    # These cancel domain mismatch if present (the job might still have SWE elements)
    r"\bsoftware\s+engineer\b", r"\bbackend\b", r"\bfull.?stack\b",
    r"\bsecurity\s+engineer\b", r"\bplatform\s+engineer\b",
    r"\bdevops\b", r"\bsre\b", r"\bcloud\s+(?:engineer|platform)\b",
    r"\bml\s+(?:engineer|platform|pipeline)\b",
    r"\bdata\s+engineer\b",
]


def is_wrong_domain(text: str) -> bool:
    text = _strip_html(text)
    wrong_hits = sum(1 for p in _WRONG_DOMAIN_SIGNALS if re.search(p, text))
    if wrong_hits < 2:
        return False
    # If the job also has clear SWE/security signals, don't reject
    has_override = any(re.search(p, text) for p in _DOMAIN_OVERRIDE_SIGNALS)
    return not has_override


# ── Skill extraction + profile matching ──────────────────────────────────────

# Skills the user has (from PROFILE_MATCH.md)
PROFILE_SKILLS: dict[str, list[str]] = {
    # Languages
    "python":        [r"\bpython\b", r"\bdjango\b", r"\bfastapi\b", r"\bflask\b"],
    "bash/shell":    [r"\bbash\b", r"\bshell\s+scripting\b", r"\bpowershell\b"],
    "sql":           [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bsqlite\b"],
    "java":          [r"\bjava\b(?!\s*script)"],
    "c/c++":         [r"\bc\+\+\b", r"\bc\/c\+\+\b", r"\bclang\b(?!.*tool)"],
    "javascript":    [r"\bjavascript\b", r"\bnode\.?js\b", r"\btypescript\b"],
    # Security
    "siem":          [r"\bsiem\b", r"\bsplunk\b", r"\bwazuh\b", r"\belastic\s*siem\b", r"\bqradar\b", r"\bsentinel\b"],
    "soc":           [r"\bsoc\s+analyst\b", r"\bblue\s+team\b", r"\bthreat\s+detection\b", r"\bincident\s+response\b"],
    "ids/ips":       [r"\bids\b", r"\bips\b", r"\bintrusion\s+detection\b", r"\bintrusion\s+prevention\b", r"\bsnort\b", r"\bsuricata\b"],
    "pentest tools": [r"\bkali\b", r"\bmetasploit\b", r"\bnessus\b", r"\bwireshark\b", r"\bnmap\b", r"\bburp\s*suite\b"],
    "vuln mgmt":     [r"\bvulnerability\s+(?:management|scanning|assessment)\b", r"\bcve\b", r"\bcvss\b", r"\bpatch\s+management\b"],
    "frameworks":    [r"\bmitre\s+att&?ck\b", r"\bnist\s+(?:csf|800)\b", r"\biso\s*27001\b", r"\bsoc\s*2\b", r"\bhipaa\b", r"\bgdpr\b", r"\bpci.?dss\b"],
    "appsec":        [r"\bapplication\s+security\b", r"\bappsec\b", r"\bowasp\b", r"\bsast\b", r"\bdast\b", r"\bpentest\b", r"\bpenetration\s+test\b"],
    "security/infra": [r"\bcybersecurity\b", r"\bcyber\s+security\b", r"\bsecurity\s+engineer\b", r"\bsecurity\s+analyst\b", r"\bcompliance\b(?!.*sales)", r"\bthreat\b", r"\bvulnerabilit\b"],
    # Infra
    "linux":         [r"\blinux\b", r"\bunix\b", r"\bubuntu\b", r"\bdebian\b", r"\brhel\b", r"\bcentos\b"],
    "docker":        [r"\bdocker\b", r"\bcontainer\b"],
    "kubernetes":    [r"\bkubernetes\b", r"\bk8s\b", r"\bhelmchart\b"],
    "git/cicd":      [r"\bgit\b(?!\w)", r"\bgithub\s+actions\b", r"\bci/?cd\b", r"\bjenkins\b", r"\bgitlab\s+ci\b"],
    "cloud":         [r"\baws\b", r"\bazure\b", r"\bgcp\b", r"\bcloud\s+(?:platform|infra|engineer)\b"],
    # Data / streaming
    "kafka":         [r"\bkafka\b"],
    "databases":     [r"\bpostgresql\b", r"\bmongodb\b", r"\bredis\b", r"\bdynamodb\b", r"\bdatabase\b"],
    "ml/data":       [r"\bscikit.learn\b", r"\bpandas\b", r"\bnumpy\b", r"\bml\s+pipeline\b", r"\bmachine\s+learning\b(?!.*10\s*years)"],
    # Networking
    "networking":    [r"\btcp/ip\b", r"\bdns\b", r"\bhttp\b", r"\btls\b", r"\bvpn\b", r"\bfirewall\b", r"\bnetwork\s+security\b"],
}

# Skills that would be a stretch or mismatch (user doesn't have)
MISMATCH_SKILLS: dict[str, str] = {
    r"\bswift\b":          "Swift/iOS",
    r"\bkotlin\b":         "Kotlin/Android",
    r"\bruntime\.net\b|\bc#\b|\b\.net\b": ".NET/C#",
    r"\bruby\s+on\s+rails\b|\bruby\b": "Ruby",
    r"\bphp\b(?!\s*://)":  "PHP",
    r"\bscala\b":          "Scala",
    r"\brust\b(?!\s+belt)": "Rust",
    r"\bgo\b(?:lang)?\b":  "Go",
    r"\bangular\b|\breact\s+native\b|\bvue\.?js\b": "Frontend framework (React/Angular/Vue)",
}


def extract_matched_skills(text: str) -> list[str]:
    """Return list of user's skill categories found in job description."""
    text = _strip_html(text)
    matched = []
    for skill_name, patterns in PROFILE_SKILLS.items():
        if any(re.search(p, text) for p in patterns):
            matched.append(skill_name)
    return matched


def extract_required_unknown_skills(text: str) -> list[str]:
    """Return list of skills clearly required but not in user's profile."""
    text = _strip_html(text)
    unknowns = []
    for pattern, label in MISMATCH_SKILLS.items():
        if re.search(pattern, text):
            unknowns.append(label)
    return unknowns


# ── Main verdict ──────────────────────────────────────────────────────────────

@dataclass
class DescriptionVerdict:
    verdict: str                        # 'auto_reject' | 'score' | 'review'
    reason: str                         # human-readable explanation
    yoe_required: int | None = None
    entry_level_in_desc: bool = False
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    domain_mismatch: bool = False
    skill_match_ratio: float = 0.0      # matched / (matched + missing)


# Tuning constants
MAX_YOE_WITHOUT_ENTRY_SIGNAL = 3   # if description says 4+ years AND no entry-level signal → reject
MIN_SKILL_MATCH_FOR_AUTO_SCORE = 2  # need at least N matching skill categories to auto-send to scoring


def analyze_description(description: str) -> DescriptionVerdict:
    """
    Full description analysis pipeline.

    Returns a DescriptionVerdict indicating what to do with the job:
      auto_reject — clear rejection signal
      score       — good match, send to Claude scoring queue
      review      — ambiguous, flag for manual check
    """
    if not description or not description.strip():
        # No description available — can't make a call, send to review
        return DescriptionVerdict(
            verdict="review",
            reason="No description available — cannot assess",
        )

    yoe = extract_max_yoe(description)
    entry_signal = has_entry_level_signal(description)
    clearance = has_clearance_requirement(description)
    domain_bad = is_wrong_domain(description)
    matched = extract_matched_skills(description)
    missing = extract_required_unknown_skills(description)

    total_signals = len(matched) + len(missing)
    ratio = len(matched) / total_signals if total_signals > 0 else 0.0

    # ── Hard rejects ──────────────────────────────────────────────────────────

    if clearance:
        return DescriptionVerdict(
            verdict="auto_reject",
            reason="Security clearance required",
            yoe_required=yoe,
            entry_level_in_desc=entry_signal,
            matched_skills=matched,
            missing_skills=missing,
            skill_match_ratio=ratio,
        )

    if domain_bad:
        return DescriptionVerdict(
            verdict="auto_reject",
            reason=f"Wrong domain (hardware/semiconductor/legacy stack)",
            yoe_required=yoe,
            entry_level_in_desc=entry_signal,
            matched_skills=matched,
            missing_skills=missing,
            domain_mismatch=True,
            skill_match_ratio=ratio,
        )

    if yoe is not None and yoe > MAX_YOE_WITHOUT_ENTRY_SIGNAL and not entry_signal:
        return DescriptionVerdict(
            verdict="auto_reject",
            reason=f"Requires {yoe}+ years with no entry-level override",
            yoe_required=yoe,
            entry_level_in_desc=entry_signal,
            matched_skills=matched,
            missing_skills=missing,
            skill_match_ratio=ratio,
        )

    # ── Auto-score (strong match) ─────────────────────────────────────────────

    if entry_signal and len(matched) >= MIN_SKILL_MATCH_FOR_AUTO_SCORE:
        return DescriptionVerdict(
            verdict="score",
            reason=f"Entry-level signal in description + {len(matched)} profile skill matches",
            yoe_required=yoe,
            entry_level_in_desc=True,
            matched_skills=matched,
            missing_skills=missing,
            skill_match_ratio=ratio,
        )

    if not entry_signal and yoe is None and len(matched) >= MIN_SKILL_MATCH_FOR_AUTO_SCORE + 1:
        # No YOE stated, good skill overlap → probably worth scoring
        return DescriptionVerdict(
            verdict="score",
            reason=f"No YOE requirement stated, {len(matched)} profile skill matches",
            yoe_required=None,
            entry_level_in_desc=False,
            matched_skills=matched,
            missing_skills=missing,
            skill_match_ratio=ratio,
        )

    # ── Review (ambiguous) ────────────────────────────────────────────────────

    parts = []
    if entry_signal:
        parts.append("entry-level signal")
    if yoe is not None:
        parts.append(f"{yoe}+ years required")
    if matched:
        parts.append(f"{len(matched)} skill matches: {', '.join(matched[:4])}")
    if not matched:
        parts.append("no profile skill overlap detected")

    return DescriptionVerdict(
        verdict="review",
        reason="; ".join(parts) if parts else "ambiguous",
        yoe_required=yoe,
        entry_level_in_desc=entry_signal,
        matched_skills=matched,
        missing_skills=missing,
        skill_match_ratio=ratio,
    )
