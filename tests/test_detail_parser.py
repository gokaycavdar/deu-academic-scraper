from app.services.avesis.detail_parser import parse_detail_page


def test_parses_avesis_detail_page_fields() -> None:
    html = """
    <div class="container bg-white mb-xl">
        <h1 class="mb-none">
            Introducing AES and ECDSA to BLE Communication
        </h1>

        <p>
            <a class="authorsRichText">ŞEKER Ö.</a>,
            <a class="authorsRichText">Çabuk U. C.</a>,
            <a class="authorsRichText">DALKILIÇ G.</a>
        </p>

        <p class="mb-xlg">
            IEEE Wireless Communications Letters,
            cilt.15, ss.765-769, 2026 (SCI-Expanded, Scopus)
        </p>

        <ul>
            <li class="list-group-item">
                <div>
                    <strong>Yayın Türü:</strong>
                </div>
                <span class="mr-sm">Makale / Tam Makale</span>
            </li>

            <li class="list-group-item">
                <div>
                    <strong>Cilt numarası:</strong>
                </div>
                <span class="mr-sm">15</span>
            </li>

            <li class="list-group-item">
                <div>
                    <strong>Doi Numarası:</strong>
                </div>
                <span class="mr-sm">10.1109/lwc.2025.3643497</span>
            </li>
        </ul>
    </div>
    """

    record = parse_detail_page(html)

    assert record.title == (
        "Introducing AES and ECDSA to BLE Communication"
    )
    assert record.contributor_names == (
        "ŞEKER Ö.",
        "Çabuk U. C.",
        "DALKILIÇ G.",
    )
    assert record.citation_text == (
        "IEEE Wireless Communications Letters, "
        "cilt.15, ss.765-769, 2026 (SCI-Expanded, Scopus)"
    )
    assert record.fields == {
        "Yayın Türü": "Makale / Tam Makale",
        "Cilt numarası": "15",
        "Doi Numarası": "10.1109/lwc.2025.3643497",
    }