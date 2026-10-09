"""Правила контроля комплектности и сроков.

Тесты работают на выдуманных фактах, без базы и без сети: domain-слой
специально написан так, чтобы ничего не знать про SQLAlchemy. Поэтому
весь файл отрабатывает за доли секунды.

«Сегодня» всегда передаём явно. Тест, который берёт настоящую текущую
дату, однажды падает в полночь или перестаёт что-либо проверять.
"""
from datetime import date, timedelta

import pytest

from app.domain import compliance as rules
from app.domain import documents as docs

TODAY = date(2026, 10, 9)


def station(**kw) -> rules.StationFacts:
    base = dict(id=1, code="ASKO-01", name="Тестовая", status="operating")
    base.update(kw)
    return rules.StationFacts(**base)


def doc(code: str, valid_until: date | None = None) -> rules.DocumentFacts:
    return rules.DocumentFacts(
        id=1, doc_type=code, title=docs.doc_title(code), valid_until=valid_until
    )


def full_set(status: str = "operating", **overrides) -> tuple[rules.DocumentFacts, ...]:
    """Полный комплект обязательных документов для стадии."""
    return tuple(
        doc(code, overrides.get(code)) for code in docs.required_for(status)
    )


# ── Комплектность ────────────────────────────────────────────────────────────
def test_работающая_площадка_без_документов_даёт_замечание_на_каждый():
    result = rules.evaluate_station(station(), TODAY)

    required = docs.required_for("operating")
    assert len(result.alerts) == len(required)
    assert {a.code for a in result.alerts} == set(required)
    assert all(a.kind == "missing_doc" for a in result.alerts)


def test_на_строгой_стадии_пропуск_это_просрочка_а_не_предупреждение():
    result = rules.evaluate_station(station(status="operating"), TODAY)
    assert {a.level for a in result.alerts} == {"overdue"}


def test_на_ранней_стадии_тот_же_пропуск_мягче():
    """Площадка в планах ещё не обязана иметь бумаги на руках."""
    result = rules.evaluate_station(station(status="planned"), TODAY)
    assert {a.level for a in result.alerts} == {"warning"}


def test_закрытая_площадка_ничего_не_требует():
    result = rules.evaluate_station(station(status="closed"), TODAY)
    assert result.alerts == []


def test_полный_комплект_без_сроков_не_даёт_замечаний():
    result = rules.evaluate_station(station(documents=full_set()), TODAY)
    assert result.alerts == []


def test_один_документ_закрывает_своё_требование():
    """Отбор актуальных редакций делает сервисный слой: сюда приходят
    только те, у кого is_current=True. Домен считает все полученные
    документы действующими."""
    one = doc("land_lease")
    result = rules.evaluate_station(station(status="planned", documents=(one,)), TODAY)
    assert result.alerts == []


# ── Сроки действия ───────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "days_left, expected",
    [
        (-1, "overdue"),   # вчера истёк
        (0, "warning"),    # истекает сегодня
        (30, "warning"),   # ровно на границе
        (31, "soon"),      # уже следующая ступень
        (90, "soon"),      # верхняя граница
        (91, None),        # слишком далеко, молчим
    ],
)
def test_границы_порогов(days_left, expected):
    assert rules.level_for_days(days_left) == expected


def test_истёкший_документ_попадает_в_замечания():
    docs_set = full_set(land_lease=TODAY - timedelta(days=5))
    result = rules.evaluate_station(station(documents=docs_set), TODAY)

    assert len(result.alerts) == 1
    alert = result.alerts[0]
    assert alert.kind == "doc_expiry"
    assert alert.level == "overdue"
    assert alert.days == -5


def test_документ_истекающий_через_десять_дней_это_предупреждение():
    docs_set = full_set(tech_spec=TODAY + timedelta(days=10))
    result = rules.evaluate_station(station(documents=docs_set), TODAY)

    assert [a.level for a in result.alerts] == ["warning"]
    assert result.alerts[0].days == 10


def test_далёкий_срок_не_беспокоит():
    docs_set = full_set(land_lease=TODAY + timedelta(days=200))
    result = rules.evaluate_station(station(documents=docs_set), TODAY)
    assert result.alerts == []


# ── Оборудование ─────────────────────────────────────────────────────────────
def charger(**kw) -> rules.ChargerFacts:
    base = dict(id=1, label="ЭЗС-1", status="working", serial="SN1")
    base.update(kw)
    return rules.ChargerFacts(**base)


def test_истёкшая_гарантия():
    ch = charger(warranty_until=TODAY - timedelta(days=3))
    result = rules.evaluate_station(station(documents=full_set(), chargers=(ch,)), TODAY)

    warranty = [a for a in result.alerts if a.kind == "warranty"]
    assert len(warranty) == 1
    assert warranty[0].level == "overdue"
    assert warranty[0].days == -3


def test_то_считается_от_последнего_обслуживания():
    ch = charger(
        installed_at=date(2020, 1, 1),      # давно, но не важно
        last_service_at=TODAY - timedelta(days=400),
        service_interval_months=12,
    )
    result = rules.evaluate_station(station(documents=full_set(), chargers=(ch,)), TODAY)

    service = [a for a in result.alerts if a.kind == "service"]
    assert len(service) == 1
    assert service[0].level == "overdue"


def test_без_последнего_то_отсчёт_идёт_от_установки():
    ch = charger(installed_at=TODAY - timedelta(days=400), service_interval_months=12)
    result = rules.evaluate_station(station(documents=full_set(), chargers=(ch,)), TODAY)
    assert any(a.kind == "service" for a in result.alerts)


def test_планируемая_зарядка_не_требует_то():
    """Оборудование, которое ещё не стоит на площадке, обслуживать нечего."""
    ch = charger(
        status="planned",
        installed_at=TODAY - timedelta(days=400),
        service_interval_months=12,
    )
    result = rules.evaluate_station(station(documents=full_set(), chargers=(ch,)), TODAY)
    assert not any(a.kind == "service" for a in result.alerts)


# ── Сортировка и чек-лист ────────────────────────────────────────────────────
def test_замечания_идут_от_срочных_к_дальним():
    docs_set = full_set(
        land_lease=TODAY - timedelta(days=5),    # overdue
        tech_spec=TODAY + timedelta(days=10),    # warning
        power_supply=TODAY + timedelta(days=60),  # soon
    )
    result = rules.evaluate_station(station(documents=docs_set), TODAY)
    assert [a.level for a in result.alerts] == ["overdue", "warning", "soon"]


def test_чек_лист_покрывает_все_типы_документов():
    result = rules.evaluate_station(station(documents=full_set()), TODAY)
    assert len(result.checklist) == len(docs.DOC_TYPES)
    assert {r.code for r in result.checklist} == {d.code for d in docs.DOC_TYPES}


def test_в_чек_листе_видно_что_обязательно_а_что_нет():
    result = rules.evaluate_station(station(status="planned"), TODAY)
    by_code = {r.code: r for r in result.checklist}

    assert by_code["land_lease"].required is True
    assert by_code["insurance"].required is False


def test_add_months_переживает_конец_месяца():
    """31 января плюс месяц — не 31 февраля."""
    assert rules.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert rules.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # високосный
    assert rules.add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)
