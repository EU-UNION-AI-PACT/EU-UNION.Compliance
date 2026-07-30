"""Idempotent seed for the PNIA Memorial & Honorary Registry.

Seeds a small, source-checked set of DECEASED state founders (from the archive
"Verstorbene Schlüsselpersonen, Friedhöfe und Teams der staatlichen Grundwerte")
as MEMORIAL_BOARD plaques, plus one LIVING HONORARY_PLACE for the concept
initiator with an explicit self-consent record.

Historical public figures are used for the memorials — DSGVO Erwägungsgrund 27
places deceased persons outside GDPR scope, yet the registry still applies the
full security envelope (PII encryption, audit trail) out of respect and
Zero-Trust principle.
"""
from __future__ import annotations

from database import get_db
from services import pnia_registry as reg

_MEMORIALS = [
    {
        "seed_key": "ardsinba",
        "pii": {
            "given_name": "Wladislaw",
            "family_name": "Ardsinba",
            "birth_place": "Suchumi, Abchasien",
            "death_date": "2018-03-11",
            "nationality": "Abchasien",
        },
        "plaque": {
            "display_name": "Wladislaw Ardsinba",
            "role": "1. Präsident Abchasiens",
            "institution": "Oberster Sowjet / Verfassungskommission Abchasiens (1994)",
            "resting_place": "Neuer Friedhof von Suchumi, Abchasien",
            "tribute_text": (
                "In stillem Gedenken an Wladislaw Ardsinba, den ersten Präsidenten "
                "Abchasiens, der maßgeblich an der Verfassungsgebung seines Landes "
                "mitwirkte. Sein Wirken bleibt Teil der staatlichen Grundwerte."
            ),
        },
    },
    {
        "seed_key": "amanullah",
        "pii": {
            "given_name": "Amanullah",
            "family_name": "Khan",
            "birth_place": "Paghman, Afghanistan",
            "death_date": "1960-04-25",
            "nationality": "Afghanistan",
        },
        "plaque": {
            "display_name": "König Amanullah Khan",
            "role": "König von Afghanistan, Verfassungsgeber der ersten afghanischen Verfassung",
            "institution": "Reformteam / Hofberater (Verfassung 1923)",
            "resting_place": "Amanullah-Mausoleum, Kabul, Afghanistan",
            "tribute_text": (
                "Zum ehrenden Andenken an König Amanullah Khan, der Afghanistan seine "
                "erste Verfassung gab. Sein Reformwerk wird im Herzen des Registers "
                "weitergetragen."
            ),
        },
    },
    {
        "seed_key": "nasser",
        "pii": {
            "given_name": "Gamal Abdel",
            "family_name": "Nasser",
            "birth_place": "Alexandria, Ägypten",
            "death_date": "1970-09-28",
            "nationality": "Ägypten",
        },
        "plaque": {
            "display_name": "Gamal Abdel Nasser",
            "role": "Präsident, Begründer des republikanischen Ägyptens",
            "institution": "Freier Offiziersrat / Verfassungskommission 1956",
            "resting_place": "Gamal-Abdel-Nasser-Moschee / Mausoleum, El-Qobbah, Kairo",
            "tribute_text": (
                "In Gedenken an Gamal Abdel Nasser, dessen Wirken die republikanische "
                "Ordnung Ägyptens prägte. Sein Andenken bleibt gewahrt."
            ),
        },
    },
    {
        "seed_key": "qemali",
        "pii": {
            "given_name": "Ismail",
            "family_name": "Qemali",
            "birth_place": "Vlorë, Osmanisches Reich",
            "death_date": "1919-01-24",
            "nationality": "Albanien",
        },
        "plaque": {
            "display_name": "Ismail Qemali",
            "role": "Gründer der Republik Albanien, Verfasser der Unabhängigkeitserklärung",
            "institution": "Nationale Versammlung von Vlorë (1912/13)",
            "resting_place": "Denkmal / Tumulus von Ismail Qemali, Vlorë, Albanien",
            "tribute_text": (
                "Zum ehrenvollen Andenken an Ismail Qemali, Gründer der Republik "
                "Albanien und Verfasser ihrer Unabhängigkeitserklärung."
            ),
        },
    },
    {
        "seed_key": "benbella",
        "pii": {
            "given_name": "Ahmed",
            "family_name": "Ben Bella",
            "birth_place": "Maghnia, Algerien",
            "death_date": "2012-04-11",
            "nationality": "Algerien",
        },
        "plaque": {
            "display_name": "Ahmed Ben Bella",
            "role": "1. Präsident Algeriens",
            "institution": "Front de Libération Nationale (FLN)",
            "resting_place": "El-Alia-Friedhof, Algier, Algerien",
            "tribute_text": (
                "In stillem Gedenken an Ahmed Ben Bella, den ersten Präsidenten "
                "Algeriens. Sein Beitrag zur Staatsgründung bleibt in Ehren."
            ),
        },
    },
    {
        "seed_key": "durrani",
        "pii": {
            "given_name": "Ahmad Schah",
            "family_name": "Durrani",
            "birth_place": "Herat / Multan",
            "death_date": "1772-10-16",
            "nationality": "Afghanistan",
        },
        "plaque": {
            "display_name": "Ahmad Schah Durrani",
            "role": "Gründer des Durrani-Reiches und Begründer des modernen Afghanistan",
            "institution": "Loya Jirga (Stammesrat), 1747",
            "resting_place": "Mausoleum von Ahmad Schah Durrani, Kandahar, Afghanistan",
            "tribute_text": (
                "Zum ehrenden Andenken an Ahmad Schah Durrani, Begründer des modernen "
                "Afghanistan. Sein Vermächtnis wird respektvoll bewahrt."
            ),
        },
    },
    {
        "seed_key": "nkrumah",
        "pii": {"given_name": "Kwame", "family_name": "Nkrumah", "birth_place": "Nkroful, Gold Coast", "death_date": "1972-04-27", "nationality": "Ghana"},
        "plaque": {
            "display_name": "Kwame Nkrumah",
            "role": "1. Premierminister & Präsident Ghanas, „Vater der Nation“",
            "institution": "Convention People’s Party (CPP) / Verfassungskommission 1957/1960",
            "resting_place": "Kwame-Nkrumah-Mausoleum, Accra, Ghana",
            "tribute_text": "In ehrendem Gedenken an Kwame Nkrumah, den ersten Staatschef Ghanas und Wegbereiter afrikanischer Selbstbestimmung.",
        },
    },
    {
        "seed_key": "kenyatta",
        "pii": {"given_name": "Jomo", "family_name": "Kenyatta", "birth_place": "Gatundu, Britisch-Ostafrika", "death_date": "1978-08-22", "nationality": "Kenia"},
        "plaque": {
            "display_name": "Jomo Kenyatta",
            "role": "1. Präsident Kenias, „Vater der Nation“",
            "institution": "KANU / Verfassungskonferenz 1963",
            "resting_place": "Jomo Kenyatta Mausoleum, Nairobi, Kenia",
            "tribute_text": "Zum Andenken an Jomo Kenyatta, den ersten Präsidenten Kenias und Mitgestalter seiner Verfassung.",
        },
    },
    {
        "seed_key": "bengurion",
        "pii": {"given_name": "David", "family_name": "Ben-Gurion", "birth_place": "Płońsk", "death_date": "1973-12-01", "nationality": "Israel"},
        "plaque": {
            "display_name": "David Ben-Gurion",
            "role": "1. Premierminister & Staatsgründer Israels",
            "institution": "Provisorische Regierung / Grundgesetz 1948",
            "resting_place": "Ben-Gurion-Grab, Sde Boker, Negev, Israel",
            "tribute_text": "In stillem Gedenken an David Ben-Gurion, Gründervater des Staates Israel.",
        },
    },
    {
        "seed_key": "gandhi",
        "pii": {"given_name": "Mahatma", "family_name": "Gandhi", "birth_place": "Porbandar, Indien", "death_date": "1948-01-30", "nationality": "Indien"},
        "plaque": {
            "display_name": "Mahatma Gandhi",
            "role": "Unabhängigkeitsführer Indiens, „Vater der Nation“",
            "institution": "Indischer Nationalkongress / Verfassunggebende Versammlung 1946–50",
            "resting_place": "Raj Ghat, Neu-Delhi, Indien (Einäscherungsstätte)",
            "tribute_text": "Zum ehrenvollen Andenken an Mahatma Gandhi, dessen gewaltfreies Wirken Indien in die Unabhängigkeit führte.",
        },
    },
    {
        "seed_key": "ambedkar",
        "pii": {"given_name": "B. R.", "family_name": "Ambedkar", "birth_place": "Mhow, Indien", "death_date": "1956-12-06", "nationality": "Indien"},
        "plaque": {
            "display_name": "B. R. Ambedkar",
            "role": "Architekt der indischen Verfassung",
            "institution": "Verfassunggebende Versammlung Indiens",
            "resting_place": "Chaitya Bhoomi, Mumbai, Indien",
            "tribute_text": "In Ehren an B. R. Ambedkar, den Chefarchitekten der indischen Verfassung und Verfechter der Gleichheit.",
        },
    },
    {
        "seed_key": "sukarno",
        "pii": {"given_name": "Sukarno", "family_name": "", "birth_place": "Surabaya, Indonesien", "death_date": "1970-06-21", "nationality": "Indonesien"},
        "plaque": {
            "display_name": "Sukarno",
            "role": "1. Präsident & Begründer Indonesiens",
            "institution": "PNI / BPUPKI / PPKI / Verfassung 1945",
            "resting_place": "Sukarno-Mausoleum, Blitar, Ost-Java, Indonesien",
            "tribute_text": "Zum Andenken an Sukarno, den Gründungspräsidenten der Republik Indonesien.",
        },
    },
    {
        "seed_key": "jinnah",
        "pii": {"given_name": "Muhammad Ali", "family_name": "Jinnah", "birth_place": "Karachi, Britisch-Indien", "death_date": "1948-09-11", "nationality": "Pakistan"},
        "plaque": {
            "display_name": "Muhammad Ali Jinnah",
            "role": "Begründer Pakistans, „Quaid-e-Azam“",
            "institution": "Muslim League / Verfassunggebende Versammlung 1947",
            "resting_place": "Mazar-e-Quaid, Karachi, Pakistan",
            "tribute_text": "In ehrendem Gedenken an Muhammad Ali Jinnah, den Gründervater Pakistans.",
        },
    },
    {
        "seed_key": "ataturk",
        "pii": {"given_name": "Mustafa Kemal", "family_name": "Atatürk", "birth_place": "Thessaloniki", "death_date": "1938-11-10", "nationality": "Türkei"},
        "plaque": {
            "display_name": "Mustafa Kemal Atatürk",
            "role": "Begründer der Republik Türkei",
            "institution": "CHP / Verfassung 1924",
            "resting_place": "Anıtkabir, Ankara, Türkei",
            "tribute_text": "Zum ehrenvollen Andenken an Mustafa Kemal Atatürk, Gründer der modernen Republik Türkei.",
        },
    },
    {
        "seed_key": "bolivar",
        "pii": {"given_name": "Simón", "family_name": "Bolívar", "birth_place": "Caracas, Venezuela", "death_date": "1830-12-17", "nationality": "Venezuela / Bolivien"},
        "plaque": {
            "display_name": "Simón Bolívar",
            "role": "Befreier Südamerikas, Präsident",
            "institution": "Konstituierender Kongress von Bolivien (1825)",
            "resting_place": "Nationalpantheon von Venezuela, Caracas",
            "tribute_text": "In Ehren an Simón Bolívar, den Befreier weiter Teile Südamerikas.",
        },
    },
    {
        "seed_key": "mandela",
        "pii": {"given_name": "Nelson", "family_name": "Mandela", "birth_place": "Mvezo", "death_date": "2013-12-05", "nationality": "Südafrika"},
        "plaque": {
            "display_name": "Nelson Mandela",
            "role": "1. demokratisch gewählter Präsident Südafrikas",
            "institution": "ANC / Verfassungsverhandlungen 1993–96",
            "resting_place": "Qunu, Südafrika (Begräbnisstätte)",
            "tribute_text": "Zum ehrenvollen Andenken an Nelson Mandela, Symbol der Versöhnung und Vater des demokratischen Südafrika.",
        },
    },
    # === Weitere historische Schlüsselpersonen aus den Workspace-Archiven ===
    {
        "seed_key": "adenauer",
        "pii": {"given_name": "Konrad", "family_name": "Adenauer", "birth_place": "Köln, Deutschland", "death_date": "1967-04-19", "nationality": "Deutschland"},
        "plaque": {
            "display_name": "Konrad Adenauer",
            "role": "1. Bundeskanzler der Bundesrepublik Deutschland",
            "institution": "Parlamentarischer Rat (1948–49)",
            "resting_place": "Waldfriedhof Rhöndorf, Bad Honnef, Deutschland",
            "tribute_text": "In ehrendem Gedenken an Konrad Adenauer, den ersten Bundeskanzler und Mitgestalter des Grundgesetzes.",
        },
    },
    {
        "seed_key": "heuss",
        "pii": {"given_name": "Theodor", "family_name": "Heuss", "birth_place": "Brackenheim, Deutschland", "death_date": "1963-12-12", "nationality": "Deutschland"},
        "plaque": {
            "display_name": "Theodor Heuss",
            "role": "1. Bundespräsident der Bundesrepublik Deutschland",
            "institution": "Parlamentarischer Rat (1948–49)",
            "resting_place": "Waldfriedhof Stuttgart, Deutschland",
            "tribute_text": "Zum Andenken an Theodor Heuss, den ersten Bundespräsidenten und Verfassungsgeber des Grundgesetzes.",
        },
    },
    {
        "seed_key": "degaulle",
        "pii": {"given_name": "Charles", "family_name": "de Gaulle", "birth_place": "Lille, Frankreich", "death_date": "1970-11-09", "nationality": "Frankreich"},
        "plaque": {
            "display_name": "Charles de Gaulle",
            "role": "Begründer der V. Republik, 1. Präsident",
            "institution": "Comité Consultatif Constitutionnel / Verfassungsrat (1958)",
            "resting_place": "Friedhof von Colombey-les-Deux-Églises, Frankreich",
            "tribute_text": "In ehrendem Gedenken an Charles de Gaulle, Begründer der Fünften Republik Frankreich.",
        },
    },
    {
        "seed_key": "sunyatsen",
        "pii": {"given_name": "Sun", "family_name": "Yat-sen", "birth_place": "Cuiheng, Guangdong, China", "death_date": "1925-03-12", "nationality": "China / Taiwan"},
        "plaque": {
            "display_name": "Sun Yat-sen",
            "role": "Gründer der Republik China",
            "institution": "Tongmenghui / Provisorische Regierung Nanjing (1912)",
            "resting_place": "Sun-Yat-sen-Mausoleum, Nanjing, China",
            "tribute_text": "Zum ehrenvollen Andenken an Sun Yat-sen, den Gründer der Republik China.",
        },
    },
    {
        "seed_key": "chiangkaishek",
        "pii": {"given_name": "Chiang", "family_name": "Kai-shek", "birth_place": "Fenghua, Zhejiang, China", "death_date": "1975-04-05", "nationality": "Taiwan"},
        "plaque": {
            "display_name": "Chiang Kai-shek",
            "role": "Präsident der Republik China auf Taiwan",
            "institution": "Kuomintang (KMT) / Nationalversammlung (Verfassung 1947)",
            "resting_place": "Cihu-Mausoleum, Taoyuan, Taiwan",
            "tribute_text": "In Gedenken an Chiang Kai-shek, Präsident der Republik China und Mitgestalter der Verfassung von 1947.",
        },
    },
    {
        "seed_key": "mao",
        "pii": {"given_name": "Mao", "family_name": "Zedong", "birth_place": "Shaoshan, Hunan, China", "death_date": "1976-09-09", "nationality": "China"},
        "plaque": {
            "display_name": "Mao Zedong",
            "role": "Vorsitzender der KPCh, Gründer der VR China",
            "institution": "Kommunistische Partei Chinas (KPCh) / Politbüro",
            "resting_place": "Mausoleum Mao Zedong, Tian'anmen-Platz, Peking",
            "tribute_text": "Zum historischen Andenken an Mao Zedong, Gründer der Volksrepublik China.",
        },
    },
    {
        "seed_key": "mannerheim",
        "pii": {"given_name": "Carl Gustaf Emil", "family_name": "Mannerheim", "birth_place": "Villnäs (Askainen), Finnland", "death_date": "1951-01-27", "nationality": "Finnland"},
        "plaque": {
            "display_name": "Carl Gustaf Emil Mannerheim",
            "role": "Regent, Marschall, 6. Präsident Finnlands",
            "institution": "Senat / Verfassungsgebende Versammlung 1919",
            "resting_place": "Hietaniemi-Friedhof, Helsinki, Finnland",
            "tribute_text": "In ehrendem Gedenken an Carl Gustaf Emil Mannerheim, Regent und Mitgestalter der finnischen Verfassung.",
        },
    },
    {
        "seed_key": "stahlberg",
        "pii": {"given_name": "Kaarlo Juho", "family_name": "Ståhlberg", "birth_place": "Suomussalmi, Finnland", "death_date": "1952-09-22", "nationality": "Finnland"},
        "plaque": {
            "display_name": "Kaarlo Juho Ståhlberg",
            "role": "1. Präsident Finnlands",
            "institution": "Verfassungsgebende Versammlung 1919",
            "resting_place": "Hietaniemi-Friedhof, Helsinki, Finnland",
            "tribute_text": "Zum Andenken an Kaarlo Juho Ståhlberg, den ersten Präsidenten Finnlands und Architekten seiner Verfassung.",
        },
    },
    {
        "seed_key": " washington",
        "pii": {"given_name": "George", "family_name": "Washington", "birth_place": "Westmoreland, Virginia, USA", "death_date": "1799-12-14", "nationality": "Vereinigte Staaten"},
        "plaque": {
            "display_name": "George Washington",
            "role": "1. Präsident der Vereinigten Staaten",
            "institution": "Constitutional Convention (1787)",
            "resting_place": "Mount Vernon, Virginia, USA",
            "tribute_text": "In ehrendem Andenken an George Washington, den ersten Präsidenten und Mitbegründer der amerikanischen Verfassung.",
        },
    },
    {
        "seed_key": "madison",
        "pii": {"given_name": "James", "family_name": "Madison", "birth_place": "Port Conway, Virginia, USA", "death_date": "1836-06-28", "nationality": "Vereinigte Staaten"},
        "plaque": {
            "display_name": "James Madison",
            "role": "„Vater der Verfassung“, 4. Präsident der USA",
            "institution": "Constitutional Convention (1787)",
            "resting_place": "Montpelier, Virginia, USA",
            "tribute_text": "Zum ehrenvollen Andenken an James Madison, den Vater der amerikanischen Verfassung.",
        },
    },
    {
        "seed_key": "nehru",
        "pii": {"given_name": "Jawaharlal", "family_name": "Nehru", "birth_place": "Allahabad, Indien", "death_date": "1964-05-27", "nationality": "Indien"},
        "plaque": {
            "display_name": "Jawaharlal Nehru",
            "role": "1. Premierminister Indiens",
            "institution": "Verfassunggebende Versammlung Indiens (1946–50)",
            "resting_place": "Shanti Vana, Neu-Delhi, Indien",
            "tribute_text": "In ehrendem Gedenken an Jawaharlal Nehru, den ersten Premierminister Indiens und Mitgestalter seiner Verfassung.",
        },
    },
    {
        "seed_key": "tito",
        "pii": {"given_name": "Josip Broz", "family_name": "Tito", "birth_place": "Kumrovec, Kroatien-Slawonien", "death_date": "1980-05-04", "nationality": "Jugoslawien"},
        "plaque": {
            "display_name": "Josip Broz Tito",
            "role": "Präsident Jugoslawiens",
            "institution": "Verfassung 1946 / 1974",
            "resting_place": "Haus der Blumen, Belgrad, Serbien",
            "tribute_text": "Zum historischen Andenken an Josip Broz Tito, Präsident des ehemaligen Jugoslawien.",
        },
    },
    {
        "seed_key": "havel",
        "pii": {"given_name": "Václav", "family_name": "Havel", "birth_place": "Prag, Tschechoslowakei", "death_date": "2011-12-18", "nationality": "Tschechien"},
        "plaque": {
            "display_name": "Václav Havel",
            "role": "1. Präsident der Tschechischen Republik",
            "institution": "Verfassung 1992",
            "resting_place": "Vinohrady-Friedhof, Prag, Tschechien",
            "tribute_text": "In ehrendem Gedenken an Václav Havel, Dissidenten und ersten Präsidenten der Tschechischen Republik.",
        },
    },
    {
        "seed_key": "kravchuk",
        "pii": {"given_name": "Leonid", "family_name": "Kravchuk", "birth_place": "Welykyj Schytyn, Ukraine", "death_date": "2022-05-03", "nationality": "Ukraine"},
        "plaque": {
            "display_name": "Leonid Kravchuk",
            "role": "1. Präsident der Ukraine",
            "institution": "Verfassung 1996",
            "resting_place": "Baikowe-Friedhof, Kiew, Ukraine",
            "tribute_text": "Zum Andenken an Leonid Kravchuk, den ersten Präsidenten der unabhängigen Ukraine.",
        },
    },
    {
        "seed_key": "yeltsin",
        "pii": {"given_name": "Boris", "family_name": "Jelzin", "birth_place": "Butka, Russland", "death_date": "2007-04-23", "nationality": "Russland"},
        "plaque": {
            "display_name": "Boris Jelzin",
            "role": "1. Präsident der Russischen Föderation",
            "institution": "Verfassung 1993",
            "resting_place": "Nowodewitschi-Friedhof, Moskau, Russland",
            "tribute_text": "In historischem Andenken an Boris Jelzin, den ersten Präsidenten der Russischen Föderation.",
        },
    },
]

_HONORARY = {
    "seed_key": "initiator",
    "pii": {
        "given_name": "Daniel",
        "family_name": "Pohl",
        "nationality": "Deutschland",
        "role": "Initiator & Urheber",
    },
    "plaque": {
        "display_name": "Daniel Pohl",
        "role": "Initiator & Urheber des PNIA-Konzepts",
        "institution": "EU-UNION Framework / HNOSS",
        "resting_place": "",
        "tribute_text": (
            "Ehrenplatz für den Initiator und Urheber des PNIA-Konzepts. In "
            "Anerkennung der Konzeption des Gedenk- und Ehrenregisters sowie des "
            "zugrunde liegenden Compliance-Rahmens. Alle Urheber- und Registerrechte "
            "verbleiben beim Initiator."
        ),
    },
}


async def _seed_entry(entry: dict, status: str, ptype: str, consent_basis: str) -> bool:
    db = get_db()
    existing = await db[reg.COL_PLAQUE].find_one({"seed_key": entry["seed_key"]})
    if existing:
        return False

    system_id = reg.make_system_id()
    individual_id = reg.uid()
    now = reg.now_iso()
    encrypted = reg.encrypt_pii(entry["pii"], system_id)
    await db[reg.COL_IND].insert_one(
        {
            "id": individual_id,
            "system_id": system_id,
            "status": status,
            "encrypted_data_record": encrypted,
            "erased": False,
            "created_at": now,
            "updated_at": now,
        }
    )
    # consent / representative verification record
    await db[reg.COL_CONSENT].insert_one(
        {
            "id": reg.uid(),
            "individual_id": individual_id,
            "status": "GRANTED",
            "basis": consent_basis,
            "consent_document_hash": reg.sha256_hex(
                f"{entry['seed_key']}:{consent_basis}"
            ),
            "representative": "Historisches Archiv / staatliche Quellen"
            if status == "DECEASED"
            else "Selbst-Zustimmung (Initiator)",
            "signed_at": now,
            "revoked_at": None,
            "created_at": now,
        }
    )
    p = entry["plaque"]
    await db[reg.COL_PLAQUE].insert_one(
        {
            "id": reg.uid(),
            "seed_key": entry["seed_key"],
            "individual_id": individual_id,
            "type": ptype,
            "is_active": True,
            "locked": status == "DECEASED",
            "content_payload": {
                "display_name": p["display_name"],
                "role": p.get("role", ""),
                "institution": p.get("institution", ""),
                "resting_place": p.get("resting_place", ""),
                "tribute_text": p.get("tribute_text", ""),
                "epitaph": p.get("epitaph", ""),
            },
            "ai_generated_content": False,
            "risk_classification": reg.RISK_MINIMAL,
            "created_at": now,
            "updated_at": now,
        }
    )
    return True


async def seed_pnia() -> int:
    seeded = 0
    for entry in _MEMORIALS:
        if await _seed_entry(
            entry,
            status="DECEASED",
            ptype="MEMORIAL_BOARD",
            consent_basis="postmortem_representative_verification",
        ):
            seeded += 1
    if await _seed_entry(
        _HONORARY,
        status="LIVING",
        ptype="HONORARY_PLACE",
        consent_basis="explicit_self_consent (DSGVO Art. 6(1)(a))",
    ):
        seeded += 1
    return seeded
