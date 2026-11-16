"""Conservative finite-state auxiliary chains and a small sourced pattern set.

No suffix-only tense guesses: participles must resolve to a known verb.
Every chain is consumed once, including uncertain chains.
"""

from .morphology import is_form, candidates
from .text import fragment

BE = {"am", "is", "are", "was", "were", "be", "been", "being"}
HAVE = {"have", "has", "had"}
MODALS = {"can", "could", "may", "might", "must", "shall", "should", "will", "would"}
SKIP = {"not", "never", "already", "just", "still", "always", "really", "ever", "probably", "certainly", "also", "recently", "yet"}
ADJECTIVAL = {"annoying", "disappointing", "exciting", "interesting", "boring", "surprising", "amazing", "confusing", "frightening", "tiring", "worrying", "pleasing", "satisfying"}
ADJECTIVAL.update({"charming", "alarming", "astonishing", "appalling", "depressing", "disturbing",
                   "embarrassing", "entertaining", "fascinating", "inspiring", "overwhelming",
                   "relaxing", "shocking", "thrilling", "upsetting"})
OBJECTS = {"me", "you", "him", "her", "it", "us", "them", "someone", "something", "everybody", "everyone"}
DETERMINERS = {"the", "a", "an", "my", "your", "his", "her", "our", "their", "some"}
CLAUSE_STOPS = {"and", "but", "or", "because", "if", "that", "when", "although", "while"}


def next_content(tokens, index: int, sentence: int) -> int:
    while index < len(tokens) and tokens[index].sentence == sentence and tokens[index].word in SKIP:
        index += 1
    return index


def valid(tokens, index: int, sentence: int) -> bool:
    return index < len(tokens) and tokens[index].sentence == sentence


def has_direct_object(tokens, index, lexicon):
    following = index + 1
    if not valid(tokens, following, tokens[index].sentence):
        return False
    word = tokens[following].word
    if word in OBJECTS:
        return True
    if word in DETERMINERS:
        following += 1
    if not valid(tokens, following, tokens[index].sentence):
        return False
    return any(lexicon.has_pos(item["lemma"], "noun") for item in candidates(tokens[following].word, lexicon))


def predicate_kind(tokens, index: int, lexicon) -> tuple[str, bool]:
    word = tokens[index].word
    if is_form(word, "gerund", lexicon):
        if word not in ADJECTIVAL:
            return "progressive", False
        after = index + 1
        if has_direct_object(tokens, index, lexicon):
            return "progressive", False
        if not valid(tokens, after, tokens[index].sentence) or tokens[after].word in CLAUSE_STOPS:
            return "adjective", False
        return "adjective", True
    if is_form(word, "past_participle", lexicon):
        ambiguous = lexicon.has_pos(word, "adjective")
        after = index + 1
        if valid(tokens, after, tokens[index].sentence) and tokens[after].word == "by":
            ambiguous = False
        return "passive", ambiguous
    return "predicate", False


def first_auxiliary(tokens, start, lexicon):
    first = tokens[start].word
    if first == "'d" and start + 1 < len(tokens):
        following = next_content(tokens, start + 1, tokens[start].sentence)
        if valid(tokens, following, tokens[start].sentence) and is_form(tokens[following].word, "past_participle", lexicon) and not lexicon.has_pos(tokens[following].word, "verb"):
            first = "had"
    return first


def semi_modal(tokens, start, first, lexicon):
    sentence = tokens[start].sentence
    cursor = next_content(tokens, start + 1, sentence)
    if not valid(tokens, cursor, sentence):
        return None
    if first in BE and tokens[cursor].word == "going":
        cursor = next_content(tokens, cursor + 1, sentence)
        rule = "going_to"
    elif first in HAVE:
        rule = "have_to"
    else:
        return None
    verb_index = next_content(tokens, cursor + 1, sentence)
    if not valid(tokens, verb_index, sentence) or tokens[cursor].word != "to":
        return None
    if not lexicon.has_pos(tokens[verb_index].word, "verb"):
        return None
    return {"end": verb_index, "rule": rule, "ambiguous": False,
            "auxiliary_chain": True, "predicative_adjective": False}


def modal_modifier(tokens, cursor, sentence, first):
    if not valid(tokens, cursor, sentence) or first not in {"may", "might"}:
        return cursor, None
    if first == "may" and tokens[cursor].word == "well":
        return next_content(tokens, cursor + 1, sentence), "may_well"
    following = cursor + 1
    if valid(tokens, following, sentence) and tokens[cursor].word == "as" and tokens[following].word == "well":
        return next_content(tokens, following + 1, sentence), first + "_as_well"
    return cursor, None


def read_auxiliaries(tokens, start, first):
    sentence = tokens[start].sentence
    cursor = next_content(tokens, start + 1, sentence)
    cursor, modifier = modal_modifier(tokens, cursor, sentence, first)
    modal = first in MODALS
    perfect = first in HAVE
    progressive = False
    copular = first in BE
    if valid(tokens, cursor, sentence) and modal and tokens[cursor].word == "have":
        perfect = True
        cursor = next_content(tokens, cursor + 1, sentence)
    expected_be = "been" if perfect else "be"
    if valid(tokens, cursor, sentence) and (modal or perfect) and tokens[cursor].word == expected_be:
        copular = True
        cursor = next_content(tokens, cursor + 1, sentence)
    if valid(tokens, cursor, sentence) and copular and tokens[cursor].word == "being":
        progressive = True
        cursor = next_content(tokens, cursor + 1, sentence)
    return cursor, perfect, progressive, copular, modifier


def chain_name(first, perfect, progressive, passive, kind):
    if first in MODALS:
        prefix = "future" if first in {"will", "shall"} else "modal"
    else:
        prefix = "past" if first in {"had", "was", "were", "did"} else "present"
    rule = prefix
    if perfect:
        rule += "_perfect"
    if progressive:
        rule += "_continuous"
    if passive:
        rule += "_passive"
    if kind == "adjective":
        rule = prefix + ("_perfect" if perfect else "") + "_copular"
    if first in MODALS and prefix == "modal" and not (perfect or progressive or passive):
        rule = "modal_" + first
    return rule


def lexical_verb(word, lexicon):
    return any(lexicon.has_pos(item["lemma"], "verb") for item in candidates(word, lexicon))


def parse_chain(tokens, start: int, lexicon) -> dict | None:
    first = first_auxiliary(tokens, start, lexicon)
    if first not in BE | HAVE | MODALS | {"do", "does", "did"}:
        return None
    special = semi_modal(tokens, start, first, lexicon)
    if special:
        return special
    cursor, perfect, progressive, copular, modifier = read_auxiliaries(tokens, start, first)
    if not valid(tokens, cursor, tokens[start].sentence):
        return {"end": cursor - 1, "rule": None, "ambiguous": True}
    word = tokens[cursor].word
    kind, ambiguous = predicate_kind(tokens, cursor, lexicon)
    if not copular and perfect and not is_form(word, "past_participle", lexicon):
        return None  # lexical have: "I have a dog"
    if not copular and not perfect and not lexical_verb(word, lexicon):
        return None
    progressive = progressive or (copular and kind == "progressive")
    passive = copular and kind == "passive"
    if copular and kind == "predicate":
        ambiguous = word.endswith(("ing", "ed"))
    rule = chain_name(first, perfect, progressive, passive, kind if copular else "verb")
    return {"end": cursor, "rule": modifier or rule, "ambiguous": ambiguous,
            "chain_structure": rule,
            "predicative_adjective": kind == "adjective", "auxiliary_chain": True}


def sourced_match(text, tokens, indices, name, lexicon, ambiguous=False, **extra):
    source = lexicon.grammar_rules.get(name)
    if source is None:
        return {**fragment(text, tokens, indices), "rule": name, "level": None,
                "ambiguous": True, "sources": [], **extra}
    return {**fragment(text, tokens, indices), "rule": name, **source,
            "ambiguous": ambiguous, **extra}


def find_grammar(text, tokens, lexicon) -> list[dict]:
    matches = []
    consumed = set()
    for start in range(len(tokens)):
        if start in consumed:
            continue
        infinitive = (tokens[start].word == "to" and valid(tokens, start + 1, tokens[start].sentence)
                      and tokens[start + 1].word == "have")
        chain = parse_chain(tokens, start + 1 if infinitive else start, lexicon)
        if chain is None:
            continue
        indices = list(range(start, chain.pop("end") + 1))
        consumed.update(indices)
        name = chain.pop("rule") or "unresolved_auxiliary_chain"
        if infinitive:
            name = "perfect_infinitive" if name == "present_perfect" else "unresolved_perfect_infinitive"
        if any(tokens[index].word == "not" for index in indices) and name + "_negative" in lexicon.grammar_rules:
            name += "_negative"
        ambiguous = chain.pop("ambiguous")
        matches.append(sourced_match(text, tokens, indices, name, lexicon, ambiguous, **chain))
    matches.extend(find_clause_patterns(text, tokens, lexicon))
    return sorted(matches, key=lambda match: match["token_indices"][0])


def find_clause_patterns(text, tokens, lexicon) -> list[dict]:
    matches = []
    inversion = {"never", "seldom", "rarely", "hardly", "scarcely"}
    for index, token in enumerate(tokens):
        first_in_sentence = index == 0 or tokens[index - 1].sentence != token.sentence
        if first_in_sentence and token.word in inversion:
            end = index + 1
            if valid(tokens, end + 1, token.sentence) and tokens[end].word in HAVE | BE | MODALS | {"do", "does", "did"}:
                matches.append(sourced_match(text, tokens, list(range(index, end + 2)), "negative_inversion", lexicon))
        if token.word != "if":
            continue
        end = index + 1
        while valid(tokens, end, token.sentence) and end - index <= 35:
            end += 1
        window = [t.word for t in tokens[index:end]]
        if "had" in window and "would" in window and "have" in window:
            # Exact clause attachment is unresolved without a syntax parser.
            matches.append(sourced_match(text, tokens, list(range(index, end)), "third_conditional", lexicon, True))
    return matches
