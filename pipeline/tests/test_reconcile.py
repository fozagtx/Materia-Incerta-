from materia_incerta.reconcile import WcvpIndex, normalise_name, reconcile
from materia_incerta.schemas import Candidate

HEADER = "plant_name_id|ipni_id|taxon_rank|taxon_status|family|genus|species|taxon_name|taxon_authors|accepted_plant_name_id"
ROWS = [
    "1||Species|Accepted|Apiaceae|Conium|maculatum|Conium maculatum|L.|1",
    "2||Species|Synonym|Apiaceae|Cicuta|maculata|Cicuta maculata|Lam.|1",
    "3||Species|Accepted|X|Homonymus|dubius|Homonymus dubius|A|3",
    "4||Species|Accepted|X|Homonymus|dubius|Homonymus dubius|B|4",
    "5||Species|Unplaced|X|Lostia|nulla|Lostia nulla|C|",
    "6||Species|Accepted|Y|Farflung|remota|Farflung remota|D|6",
]
DIST_HEADER = "plant_locality_id|plant_name_id|continent_code_l1|continent|region_code_l2|region|area_code_l3|area|introduced|extinct|location_doubtful"
DIST = [
    "a|1|1|Europe|13|SE Europe|GRC|Greece|0|0|0",
    "b|6|8|S America|84|Brazil|BZL|Brazil|0|0|0",
    "c|6|3|Asia|34|W Asia|TUR|Turkey|1|0|0",  # introduced: not native
]


def _index(tmp_path):
    names = tmp_path / "names.csv"
    names.write_text("\n".join([HEADER, *ROWS]) + "\n")
    dist = tmp_path / "dist.csv"
    dist.write_text("\n".join([DIST_HEADER, *DIST]) + "\n")
    return WcvpIndex.load(names, dist)


def _cand(key, name):
    return Candidate(candidate_key=key, lemma_tag="n", dmm_id="d", source_name=name)


def test_normalise_name():
    assert normalise_name("  Mentha ×  piperita ") == "mentha piperita"


def test_accepted_synonym_missing_ambiguous_and_unplaced(tmp_path):
    idx = _index(tmp_path)
    out = {c.candidate_key: c for c in reconcile(
        [
            _cand("acc", "Conium maculatum"),
            _cand("syn", "Cicuta maculata"),
            _cand("missing", "Nonexistens planta"),
            _cand("ambiguous", "Homonymus dubius"),
            _cand("unplaced", "Lostia nulla"),
        ],
        idx,
    )}
    assert out["acc"].wcvp_id == "1" and out["acc"].reconcile_note is None
    assert out["syn"].wcvp_id == "1" and "synonymy" in out["syn"].reconcile_note
    assert out["acc"].synonyms == ("Cicuta maculata",)
    for key in ("missing", "ambiguous", "unplaced"):
        assert out[key].wcvp_id is None and out[key].reconcile_note


def test_range_flag_and_hazard(tmp_path):
    idx = _index(tmp_path)
    out = {c.candidate_key: c for c in reconcile(
        [_cand("conium", "Conium maculatum"), _cand("far", "Farflung remota")], idx
    )}
    assert out["conium"].in_east_med is True
    assert out["conium"].hazard and "toxic" in out["conium"].hazard.lower()
    assert out["far"].in_east_med is False  # only introduced in Turkey
    assert out["far"].hazard is None


def test_manual_match_wins(tmp_path):
    idx = _index(tmp_path)
    [c] = reconcile([_cand("amb", "Homonymus dubius")], idx, manual={"amb": "4"})
    assert c.wcvp_id == "4" and c.reconcile_note == "manual match"
