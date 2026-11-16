# Dictionary attribution

The software includes normalized terms, CEFR labels and morphological forms
from the following sources. Their data terms remain separate from the code.
No dictionary definitions, example sentences, translations or audio are bundled.

CEFR-J Wordlist Version 1.5 and CEFR-J Grammar Profile Version 20180315:
compiled by Yukio Tono, Tokyo University of Foreign Studies.
Copyright Tono Laboratory at TUFS. Research and commercial use is permitted
with appropriate citation according to the upstream terms:
https://github.com/openlanguageprofiles/olp-en-cefrj
Original project: http://www.cefr-j.org/

Octanove Vocabulary Profile C1/C2 Version 1.0: Octanove Labs.
Original and normalized Octanove data are licensed under Creative Commons
Attribution-ShareAlike 4.0 International:
https://creativecommons.org/licenses/by-sa/4.0/
Source: https://github.com/openlanguageprofiles/olp-en-cefrj
Changes: lowercase normalization, spelling-alternative expansion,
hyphen/underscore normalization, source and POS annotation, JSON serialization.

OpenJam: https://github.com/amirj4m/openjam
Upstream MIT license and attribution:
https://github.com/amirj4m/openjam/blob/main/LICENSE
https://github.com/amirj4m/openjam/blob/main/ATTRIBUTION.md
Changes: retain lemma, POS and level; mark automatically assigned levels;
join word forms through word_id; serialize as compressed JSON.

CEFR Mega Dataset: https://github.com/kamronsaparbaev/cefr-dataset
Changes: retain Word and CEFR only, normalize terms, flag automatic estimates.

Pearson Global Scale of English Teacher Toolkit:
https://www.english.com/gse/teacher-toolkit/user/lo
Changes: retain expressions, CEFR, POS and item identifiers; collapse CEFR
sublevels to bands; normalize terms; derive bounded object-slot templates.

Cambridge Dictionary: three phrase/level facts and links, without definitions:
https://dictionary.cambridge.org/dictionary/learner-english/turn-out
https://dictionary.cambridge.org/dictionary/english/turn-down?topic=refusing-and-rejecting
https://dictionary.cambridge.org/dictionary/essential-british-english/give-up-something

Optional Kaikki/Wiktextract imports are not included in this snapshot.
https://kaikki.org/dictionary/rawdata.html
Their upstream data terms apply when importing a local dump.

The raw-source URL and SHA-256 for each bundled data input are recorded in
cefr_analyzer/data/manifest.json. Per-record provenance remains in the lexicon.
