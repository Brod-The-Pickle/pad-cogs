from collections import defaultdict
from typing import Set

from Levenshtein import jaro_winkler

SERIES_TYPE_PRIORITY = {
    "regular": 4,
    "event": 4,
    "seasonal": 3,
    "ghcollab": 2,
    "collab": 1,
    None: 0
}


def calc_ratio(s1, s2):
    return jaro_winkler(s1, s2, .05)


def calc_ratio_prefix(token, full_word):
    if full_word == token:
        return 1
    elif full_word.startswith(token):
        return 1 - len(full_word) / 1000
    return jaro_winkler(token, full_word, .05)


class FindMonster:
    MODIFIER_JW_DISTANCE = .95
    TOKEN_JW_DISTANCE = .8

    def _merge_multi_word_tokens(self, tokens, valid_multi_word_tokens):
        result = []
        s = 0
        multi_word_tokens_sorted = sorted(valid_multi_word_tokens,
                                          key=lambda x: (len(x), len(''.join(x))),
                                          reverse=True)
        for c1, token in enumerate(tokens):
            if s:
                s -= 1
                continue
            for mwt in multi_word_tokens_sorted:
                if len(mwt) > len(tokens) - c1:
                    continue
                for c2, t in enumerate(mwt):
                    if (tokens[c1 + c2] != t and len(t) < 5) or calc_ratio(tokens[c1 + c2], t) < self.TOKEN_JW_DISTANCE:
                        break
                else:
                    s = len(mwt) - 1
                    result.append("".join(mwt))
                    break
            else:
                result.append(token)
        return result

    def _monster_has_token(self, monster, token, monsterscore, monster_mods):
        if len(token) < 6:
            if token in monster_mods:
                monsterscore[monster] += 1
                return True
        else:
            closest = max(jaro_winkler(m, token, .05) for m in monster_mods)
            if closest > self.TOKEN_JW_DISTANCE:
                monsterscore[monster] += closest
                return True
        return False

    def interpret_query(self, raw_query: str, index2) -> (Set[str], Set[str]):
        tokenized_query = raw_query.split()
        tokenized_query = self._merge_multi_word_tokens(tokenized_query, index2.multi_word_tokens)

        modifiers = []
        negative_modifiers = set()
        name = set()
        longmods = [p for p in index2.all_modifiers if len(p) > 8]
        lastmodpos = False

        for i, token in enumerate(tokenized_query[::-1]):
            negated = token.startswith("-")
            token = token.lstrip('-')
            if any(jaro_winkler(m, token) > self.MODIFIER_JW_DISTANCE for m in index2.suffixes):
                if negated:
                    negative_modifiers.add(token)
                else:
                    modifiers.append(token)
            else:
                if i:
                    tokenized_query = tokenized_query[:-i]
                break

        for i, token in enumerate(tokenized_query):
            negated = token.startswith("-")
            token = token.lstrip('-')
            if token in index2.all_modifiers or (
                    any(jaro_winkler(m, token) > self.MODIFIER_JW_DISTANCE for m in longmods)
                    and token not in index2.all_name_tokens
                    and len(token) >= 8):
                if negated:
                    lastmodpos = False
                    negative_modifiers.add(token)
                else:
                    lastmodpos = True
                    modifiers.append(token)
            else:
                name.update(tokenized_query[i:])
                break

        if not name and modifiers and lastmodpos:
            if index2.manual[modifiers[-1]]:
                name.add(modifiers[-1])
                modifiers = modifiers[:-1]

        return set(modifiers), negative_modifiers, name

    def process_name_tokens(self, name_query_tokens, index2):
        monstergen = None
        monsterscore = defaultdict(int)

        for t in name_query_tokens:
            valid = set()
            ms = sorted([nt for nt in index2.all_name_tokens if jaro_winkler(t, nt, .05) > self.TOKEN_JW_DISTANCE],
                        key=lambda nt: jaro_winkler(t, nt, .05), reverse=True)
            ms += [token for token in index2.all_name_tokens if token.startswith(t)]
            if not ms:
                return None, None
            for match in ms:
                for m in index2.manual[match]:
                    if m not in valid:
                        monsterscore[m] += calc_ratio_prefix(t, match) + .001
                        valid.add(m)
                for m in index2.name_tokens[match]:
                    if m not in valid:
                        monsterscore[m] += calc_ratio_prefix(t, match)
                        valid.add(m)
                for m in index2.fluff_tokens[match]:
                    if m not in valid:
                        monsterscore[m] += calc_ratio_prefix(t, match) / 2
                        valid.add(m)

            if monstergen is not None:
                monstergen.intersection_update(valid)
            else:
                monstergen = valid

        return monstergen, monsterscore

    def process_modifiers(self, mod_tokens, neg_mod_tokens, monsterscore, potential_evos, monster_mods):
        for t in mod_tokens:
            potential_evos = {m for m in potential_evos if
                              self._monster_has_token(m, t, monsterscore, monster_mods[m])}
            if not potential_evos:
                return None
        for t in neg_mod_tokens:
            potential_evos = {m for m in potential_evos if
                              not self._monster_has_token(m, t, monsterscore, monster_mods[m])}
            if not potential_evos:
                return None

        return potential_evos

    def get_monster_evos(self, database, monster_gen, monster_score):
        monster_evos = set()
        for m in sorted(monster_gen, key=lambda m: monster_score[m], reverse=True):
            for evo in database.graph.get_alt_monsters(m):
                monster_evos.add(evo)
                if monster_score[evo] < monster_score[m]:
                    monster_score[evo] = monster_score[m] - .003

        return monster_evos


find_monster = FindMonster()
