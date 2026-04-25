"""
Rule-based text compression inspired by caveman-compression.
Strips predictable grammar while keeping facts, names, numbers, constraints.
Achieves ~15-30% token reduction with no external model required.
"""

import re

# Articles and determiners
_ARTICLES = re.compile(
    r"\b(a|an|the)\b\s*",
    re.IGNORECASE,
)

# Auxiliary / copula verbs (only where clearly redundant)
_AUX = re.compile(
    r"\b(is being|are being|was being|were being|has been|have been|had been)\b",
    re.IGNORECASE,
)

# "is/are/was/were" before adjective/noun (passive helper)
_COPULA = re.compile(
    r"\b(is|are|was|were|be|been|being)\b\s+",
    re.IGNORECASE,
)

# Filler adverbs and hedge phrases
_FILLERS = re.compile(
    r"\b(very|quite|basically|essentially|simply|just|really|literally|"
    r"certainly|obviously|clearly|actually|generally|typically|"
    r"in order to|so as to|due to the fact that|in the event that|"
    r"it is important to note that|it should be noted that|"
    r"please note that|as a result of|in spite of the fact that)\b\s*",
    re.IGNORECASE,
)

# Connective phrases that add no information
_CONNECTIVES = re.compile(
    r"\b(therefore|thus|hence|however|moreover|furthermore|additionally|"
    r"nevertheless|nonetheless|consequently|accordingly|subsequently|"
    r"in addition|on the other hand|as a consequence|as previously mentioned|"
    r"as stated above|as mentioned earlier)\b[,]?\s*",
    re.IGNORECASE,
)

# Redundant phrase contractions
_CONTRACTIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bis able to\b", re.IGNORECASE), "can"),
    (re.compile(r"\bwill be able to\b", re.IGNORECASE), "will"),
    (re.compile(r"\bin order to\b", re.IGNORECASE), "to"),
    (re.compile(r"\bdue to\b", re.IGNORECASE), "from"),
    (re.compile(r"\bprior to\b", re.IGNORECASE), "before"),
    (re.compile(r"\bsubsequent to\b", re.IGNORECASE), "after"),
    (re.compile(r"\bwith regard to\b", re.IGNORECASE), "about"),
    (re.compile(r"\bwith respect to\b", re.IGNORECASE), "for"),
    (re.compile(r"\bfor the purpose of\b", re.IGNORECASE), "for"),
    (re.compile(r"\bin the case of\b", re.IGNORECASE), "for"),
    (re.compile(r"\bmake use of\b", re.IGNORECASE), "use"),
    (re.compile(r"\btake into account\b", re.IGNORECASE), "consider"),
    (re.compile(r"\bprovide support for\b", re.IGNORECASE), "support"),
    (re.compile(r"\bimplement support for\b", re.IGNORECASE), "add"),
    (re.compile(r"\bneed to\b", re.IGNORECASE), "must"),
    (re.compile(r"\bshould be able to\b", re.IGNORECASE), "should"),
    (re.compile(r"\bwe want to\b", re.IGNORECASE), ""),
    (re.compile(r"\bwe need to\b", re.IGNORECASE), ""),
    (re.compile(r"\bi want to\b", re.IGNORECASE), ""),
    (re.compile(r"\bi need to\b", re.IGNORECASE), ""),
]

# Clean up multiple spaces / leading commas after removal
_MULTI_SPACE = re.compile(r"  +")
_LEADING_COMMA = re.compile(r"^\s*,\s*")
_TRAILING_COMMA = re.compile(r",\s*\.")


def compress(text: str, aggressive: bool = False) -> str:
    """
    Compress text by removing predictable grammar elements.
    Set aggressive=True to also strip copula verbs and more connectives.
    """
    result = text

    # Apply phrase contractions first (order matters)
    for pattern, replacement in _CONTRACTIONS:
        result = pattern.sub(replacement + " ", result)

    # Remove filler adverbs and hedge phrases
    result = _FILLERS.sub("", result)

    # Remove connectives
    result = _CONNECTIVES.sub("", result)

    if aggressive:
        result = _AUX.sub("", result)
        result = _COPULA.sub("", result)

    # Remove articles last (after other removals to avoid double-spaces)
    result = _ARTICLES.sub("", result)

    # Cleanup
    result = _MULTI_SPACE.sub(" ", result)
    result = _LEADING_COMMA.sub("", result)
    result = _TRAILING_COMMA.sub(".", result)

    # Fix sentence-start capitalization lost by removal
    result = re.sub(r"(?<=\. )([a-z])", lambda m: m.group(1).upper(), result)
    result = result.strip()

    return result


def compression_ratio(original: str, compressed: str) -> float:
    orig_tokens = len(original.split())
    comp_tokens = len(compressed.split())
    if orig_tokens == 0:
        return 0.0
    return round((1 - comp_tokens / orig_tokens) * 100, 1)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (GPT/Claude average)."""
    return max(1, len(text) // 4)
