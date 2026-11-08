import pytest

from materia_incerta.mask import (
    PLACEHOLDER,
    MaskingError,
    NameLexicon,
    assert_masked,
    find_leaks,
    lexicon_for_name,
    mask,
)
from materia_incerta.schemas import Candidate, DmmPlant, HistoricalName
from materia_incerta.score import ResponseCache, score_comparisons


def test_masks_binomial_genus_and_epithet():
    lex = NameLexicon.from_terms(["Fibigia clypeata"])
    out = mask("Fibigia clypeata is like other Fibigia; F. clypeata pods.", lex)
    assert "Fibigia" not in out and "clypeata" not in out
    # The full binomial is one span; the lone genus and epithet are two more.
    assert out == f"{PLACEHOLDER} is like other {PLACEHOLDER}; F. {PLACEHOLDER} pods."


def test_case_and_diacritics_are_ignored():
    lex = NameLexicon.from_terms(["ἄλυσσον"])
    for text in ("ἄλυσσον", "ΑΛΥΣΣΟΝ", "αλυσσον"):
        assert find_leaks(f"the {text} grows", lex), text
    assert mask("τὸ ἄλυσσον φύεται", lex) == f"τὸ {PLACEHOLDER} φύεται"


def test_transliteration_variants_and_latinised_forms():
    lex = NameLexicon.from_terms(["khamaimelon", "aristolokhia"])
    for leak in ("Chamaemelum", "chamaimelon", "KHAMAIMELON", "Aristolochia", "aristolochic acids"):
        assert find_leaks(f"text {leak} text", lex), leak


def test_synonyms_and_common_names_are_masked():
    lex = NameLexicon.from_terms(["Matricaria chamomilla", "Matricaria recutita", "chamomile"])
    out = mask("Matricaria recutita, also called chamomile, resembles M. chamomilla.", lex)
    assert find_leaks(out, lex) == []
    for word in ("Matricaria", "recutita", "chamomile", "chamomilla"):
        assert word not in out


def test_ordinary_words_survive():
    lex = NameLexicon.from_terms(["Ruta graveolens", "rue"])
    assert mask("leaves rounded, flowers yellow, true to type", lex) == "leaves rounded, flowers yellow, true to type"


def test_assert_masked_raises_on_any_leak():
    lex = NameLexicon.from_terms(["Conium maculatum"])
    with pytest.raises(MaskingError):
        assert_masked("stem spotted like Conium", lex)
    assert_masked("stem spotted, purple", lex)


def test_lexicon_pools_every_candidate_of_a_name():
    name = HistoricalName(lemma_tag="n", greek_name="ἄλυσσον", transliteration="alysson", dmm_ids=("d1", "d2"))
    plants = [DmmPlant(dmm_id="d1", chapter="3.91", names=("alysson",)), DmmPlant(dmm_id="d2", chapter="x")]
    cands = [
        Candidate(candidate_key="a", lemma_tag="n", dmm_id="d1", source_name="Fibigia clypeata",
                  accepted_name="Fibigia clypeata", accepted_genus="Fibigia", synonyms=("Farsetia clypeata",)),
        Candidate(candidate_key="b", lemma_tag="n", dmm_id="d2", source_name="Scutellaria galericulata"),
        Candidate(candidate_key="c", lemma_tag="other", dmm_id="d9", source_name="Ruta graveolens"),
    ]
    lex = lexicon_for_name(name, plants, cands)
    text = "Fibigia, Farsetia clypeata, Scutellaria galericulata, Alyssum, alysson"
    assert find_leaks(mask(text, lex), lex) == []
    assert all(w not in mask(text, lex) for w in ("Fibigia", "Farsetia", "Scutellaria", "Alyssum"))
    # A different name's candidate is not in this lexicon.
    assert find_leaks("Ruta graveolens", lex) == []


class RecordingClient:
    model = "recorder"

    def __init__(self):
        self.prompts = []

    def complete_json(self, prompt, schema):
        self.prompts.append(prompt)
        return '{"match_class": "absent", "reason": "recorded"}'


def test_no_name_reaches_a_prompt(demo_tables, tmp_path):
    """Every prompt for every demo comparison is free of every name, synonym
    and transliteration for the plant and all its candidates."""
    names = demo_tables["historical_names"]
    plants = demo_tables["dmm_plants"]
    cands = demo_tables["candidates"]
    comps = demo_tables["feature_comparisons"]
    client = RecordingClient()
    score_comparisons(comps, names, plants, cands, ResponseCache(tmp_path), model=client.model, client=client)
    assert len(client.prompts) == len(comps)

    by_lemma = {n.lemma_tag: n for n in names}
    cand_lemma = {c.candidate_key: c.lemma_tag for c in cands}
    for comp, prompt in zip(comps, client.prompts):
        lex = lexicon_for_name(by_lemma[cand_lemma[comp.candidate_key]], plants, cands)
        body = prompt.split("Ancient description:")[1].split("Answer with JSON")[0]
        assert find_leaks(body, lex) == [], comp.comparison_id
        name = by_lemma[cand_lemma[comp.candidate_key]]
        for term in [name.greek_name, name.transliteration] + [
            t for c in cands if c.lemma_tag == name.lemma_tag
            for t in (c.source_name, c.accepted_name or "", *c.synonyms)
        ]:
            for word in term.split():
                assert word.lower() not in body.lower(), (comp.comparison_id, word)
