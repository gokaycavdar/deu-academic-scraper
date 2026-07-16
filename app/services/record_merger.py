from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import replace
from typing import Iterable

from app.services.avesis.normalizer import NormalizedRecord


DOI_MATCH_RECORD_TYPES = {
    "article",
    "conference_paper",
}


def merge_source_records(
    avesis_records: Iterable[NormalizedRecord],
    yok_records: Iterable[NormalizedRecord],
) -> list[NormalizedRecord]:
    """
    Aynı akademisyen ve kayıt türündeki kesin AVESİS/YÖK Akademik
    eşleşmelerini birleştirir.

    Önce Makale ve Bildiriler için DOI üzerinden eşleştirme yapılır.
    DOI ile eşleşmeyen kayıtlar daha sonra normalize başlık üzerinden
    değerlendirilir. Belirsiz eşleşmeler veri kaybını önlemek için
    ayrı bırakılır.
    """
    avesis_list = list(avesis_records)
    yok_list = list(yok_records)

    matches = _match_unique_dois(
        avesis_records=avesis_list,
        yok_records=yok_list,
    )

    matched_avesis_indexes = set(matches)
    matched_yok_indexes = set(matches.values())

    avesis_title_groups = _group_record_indexes(avesis_list)
    yok_title_groups = _group_record_indexes(yok_list)

    for group_key, all_avesis_indexes in (
        avesis_title_groups.items()
    ):
        all_yok_indexes = yok_title_groups.get(group_key, [])

        avesis_indexes = [
            index
            for index in all_avesis_indexes
            if index not in matched_avesis_indexes
        ]
        yok_indexes = [
            index
            for index in all_yok_indexes
            if index not in matched_yok_indexes
        ]

        if not avesis_indexes or not yok_indexes:
            continue

        title_matches = _match_group(
            avesis_records=avesis_list,
            yok_records=yok_list,
            avesis_indexes=avesis_indexes,
            yok_indexes=yok_indexes,
        )

        matches.update(title_matches)
        matched_avesis_indexes.update(title_matches)
        matched_yok_indexes.update(title_matches.values())

    merged_records: list[NormalizedRecord] = []

    for avesis_index, avesis_record in enumerate(avesis_list):
        yok_index = matches.get(avesis_index)

        if yok_index is None:
            merged_records.append(avesis_record)
            continue

        merged_records.append(
            _merge_pair(
                avesis_record,
                yok_list[yok_index],
            )
        )

    merged_records.extend(
        record
        for index, record in enumerate(yok_list)
        if index not in matched_yok_indexes
    )

    return merged_records


def _match_unique_dois(
    *,
    avesis_records: list[NormalizedRecord],
    yok_records: list[NormalizedRecord],
) -> dict[int, int]:
    """
    Başlık farkından bağımsız olarak, her iki kaynakta da yalnızca
    birer kez görünen aynı DOI'li Makale/Bildiri kayıtlarını eşleştirir.
    """
    avesis_doi_groups = _group_doi_indexes(avesis_records)
    yok_doi_groups = _group_doi_indexes(yok_records)

    matches: dict[int, int] = {}

    for group_key, avesis_indexes in avesis_doi_groups.items():
        yok_indexes = yok_doi_groups.get(group_key, [])

        if len(avesis_indexes) != 1 or len(yok_indexes) != 1:
            continue

        matches[avesis_indexes[0]] = yok_indexes[0]

    return matches


def _group_doi_indexes(
    records: list[NormalizedRecord],
) -> dict[tuple[str, str, str], list[int]]:
    groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)

    for index, record in enumerate(records):
        if record.record_type not in DOI_MATCH_RECORD_TYPES:
            continue

        doi = _normalized_doi(record.data.get("doi"))

        if doi is None:
            continue

        group_key = (
            record.academician_id,
            record.record_type,
            doi,
        )
        groups[group_key].append(index)

    return groups


def _group_record_indexes(
    records: list[NormalizedRecord],
) -> dict[tuple[str, str, str], list[int]]:
    groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)

    for index, record in enumerate(records):
        title_key = _canonical_text(record.title)

        if not title_key:
            continue

        group_key = (
            record.academician_id,
            record.record_type,
            title_key,
        )
        groups[group_key].append(index)

    return groups


def _match_group(
    *,
    avesis_records: list[NormalizedRecord],
    yok_records: list[NormalizedRecord],
    avesis_indexes: list[int],
    yok_indexes: list[int],
) -> dict[int, int]:
    if len(avesis_indexes) == 1 and len(yok_indexes) == 1:
        avesis_index = avesis_indexes[0]
        yok_index = yok_indexes[0]

        if _matches_single_title_pair(
            avesis_records[avesis_index],
            yok_records[yok_index],
        ):
            return {avesis_index: yok_index}

        return {}

    proposals: dict[int, int] = {}

    for avesis_index in avesis_indexes:
        avesis_record = avesis_records[avesis_index]

        candidates = [
            yok_index
            for yok_index in yok_indexes
            if _matches_discriminator(
                avesis_record,
                yok_records[yok_index],
            )
        ]

        if len(candidates) == 1:
            proposals[avesis_index] = candidates[0]

    proposed_yok_counts = Counter(proposals.values())

    return {
        avesis_index: yok_index
        for avesis_index, yok_index in proposals.items()
        if proposed_yok_counts[yok_index] == 1
    }


def _matches_single_title_pair(
    avesis_record: NormalizedRecord,
    yok_record: NormalizedRecord,
) -> bool:
    """
    Başlık grubu tekilse eşleşmeye izin verir. Ancak iki kaynakta da
    DOI var ve DOI değerleri farklıysa kayıtlar ayrı bırakılır.
    """
    avesis_doi = _normalized_doi(
        avesis_record.data.get("doi")
    )
    yok_doi = _normalized_doi(
        yok_record.data.get("doi")
    )

    if avesis_doi and yok_doi:
        return avesis_doi == yok_doi

    return True


def _matches_discriminator(
    avesis_record: NormalizedRecord,
    yok_record: NormalizedRecord,
) -> bool:
    avesis_doi = _normalized_doi(
        avesis_record.data.get("doi")
    )
    yok_doi = _normalized_doi(
        yok_record.data.get("doi")
    )

    if avesis_doi and yok_doi:
        return avesis_doi == yok_doi

    if (
        avesis_record.year is None
        or yok_record.year is None
        or avesis_record.year != yok_record.year
    ):
        return False

    avesis_authors = _author_signature(
        avesis_record.contributor_names
    )
    yok_authors = _author_signature(
        yok_record.contributor_names
    )

    return bool(avesis_authors and yok_authors) and (
        avesis_authors == yok_authors
    )


def _merge_pair(
    avesis_record: NormalizedRecord,
    yok_record: NormalizedRecord,
) -> NormalizedRecord:
    merged_data = dict(avesis_record.data)

    for field_name, yok_value in yok_record.data.items():
        avesis_value = merged_data.get(field_name)

        if _is_blank(avesis_value) and not _is_blank(yok_value):
            merged_data[field_name] = yok_value

    return replace(
        avesis_record,
        contributor_names=(
            avesis_record.contributor_names
            or yok_record.contributor_names
        ),
        contributor_text=(
            avesis_record.contributor_text
            or yok_record.contributor_text
        ),
        citation_text=(
            avesis_record.citation_text
            or yok_record.citation_text
        ),
        year=avesis_record.year or yok_record.year,
        data=merged_data,
        source_names=_merge_source_names(
            avesis_record.source_names,
            yok_record.source_names,
        ),
    )


def _merge_source_names(
    first: tuple[str, ...],
    second: tuple[str, ...],
) -> tuple[str, ...]:
    names: list[str] = []

    for source_name in (*first, *second):
        if source_name not in names:
            names.append(source_name)

    return tuple(names)


def _normalized_doi(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    value = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^doi\s*:\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.casefold().strip() or None


def _author_signature(value: str) -> frozenset[str]:
    surnames: set[str] = set()

    for author in re.split(r"[,;]", value):
        tokens = _canonical_text(author).split()

        if not tokens:
            continue

        surname = max(
            enumerate(tokens),
            key=lambda item: (len(item[1]), item[0]),
        )[1]

        if len(surname) > 1:
            surnames.add(surname)

    return frozenset(surnames)


def _canonical_text(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = normalized.replace("ı", "i")

    return " ".join(
        re.findall(r"[a-z0-9]+", normalized)
    )


def _is_blank(value: object) -> bool:
    return value is None or (
        isinstance(value, str) and not value.strip()
    )