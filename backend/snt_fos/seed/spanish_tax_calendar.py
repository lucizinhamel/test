"""Spanish tax calendar generator.

For a given fiscal year, produce the full set of `TaxObligation` rows that apply
to a given entity profile (SL vs personal book).

Sources cross-checked against the AEAT calendario del contribuyente 2026, Real
Decreto 1624/1992 (Reglamento IVA), Ley 27/2014 (LIS), Ley 35/2006 (LIRPF) and
Real Decreto 1065/2007 (RGAT). Any date that falls on a Saturday / Sunday is
shifted forward to the next Monday per art. 30.5 Ley 39/2015 — national /
regional holidays are NOT yet auto-skipped (TODO before each campaign).

Important constants documented inline so they can be reviewed without leaving
this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional

# --- Constants ----------------------------------------------------------------
# Fiscal thresholds & rates that drive the calendar. Verify each year.

# IVA rates (LIVA art. 90-91)
IVA_GENERAL = Decimal("21")
IVA_REDUCIDO = Decimal("10")
IVA_SUPERREDUCIDO = Decimal("4")

# IRPF retention rates (LIRPF art. 101 + RIRPF)
IRPF_PROFESIONALES = Decimal("15")  # general (art. 95.1 RIRPF)
IRPF_PROFESIONALES_INICIO = Decimal("7")  # first 3 years (art. 95.1 RIRPF)
IRPF_ALQUILERES = Decimal("19")  # urban rentals (art. 100 RIRPF)
IRPF_CAPITAL_MOBILIARIO = Decimal("19")  # art. 90 RIRPF

# IS rates (LIS art. 29)
IS_GENERAL = Decimal("25")
IS_PYME_REDUCIDO = Decimal("23")  # entidades INCN < €1M (since 2023, scaled to 20% by 2027)
IS_NUEVA_CREACION = Decimal("15")  # first profitable + next year (art. 29.1 LIS)

# Modelo 202 percentages (LIS art. 40)
M202_PCT_CUOTA = Decimal("18")  # modalidad a — % of last filed cuota
M202_PCT_BASE_PYME = Decimal("17")  # modalidad b — 5/7 of 25%, rounded down
M202_PCT_BASE_GRANDE = Decimal("24")  # modalidad b for INCN > €10M (19/20 of 25%)

# Thresholds
M347_THRESHOLD = Decimal("3005.06")  # art. 33 RGAT
M720_THRESHOLD = Decimal("50000")  # DA 18 LGT — per block (cuentas / valores / inmuebles)
M232_THRESHOLD_VINCULADAS_SAME = Decimal("250000")  # vinculadas same counterparty
M232_THRESHOLD_VINCULADAS_SPECIFIC = Decimal("100000")  # specific operations
M232_THRESHOLD_PARAISOS = Decimal("0")  # any operation w/ paraíso fiscal triggers
SII_THRESHOLD_INCN = Decimal("6000000")  # mandatory SII — turnover threshold
PATRIMONIO_BASE_EXENTA_MADRID = Decimal("700000")  # base exenta general
PATRIMONIO_VIVIENDA_HABITUAL = Decimal("300000")  # vivienda habitual exempt up to


@dataclass
class ObligationSpec:
    modelo: str
    name_es: str
    name_en: str
    legal_basis: str
    period_kind: str  # quarterly / monthly / annual / triannual
    period_label: str
    period_start: date
    period_end: date
    due_date: date
    direct_debit_due_date: Optional[date]
    payment_kind: str  # informational / withheld / self_assessed / advance_payment
    rate_hint: Optional[str] = None
    threshold_hint: Optional[str] = None
    reserve_pct_hint: Optional[Decimal] = None
    notes: Optional[str] = None
    applies_to: tuple[str, ...] = field(default_factory=lambda: ("sl",))


def _shift_off_weekend(d: date) -> date:
    """Move Sat/Sun to next Monday (art. 30.5 Ley 39/2015)."""
    if d.weekday() == 5:
        return d + timedelta(days=2)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _ddebit(d: date, days_before: int = 5) -> date:
    return _shift_off_weekend(d - timedelta(days=days_before))


def _q_periods(year: int) -> list[tuple[str, date, date]]:
    return [
        (f"{year}-Q1", date(year, 1, 1), date(year, 3, 31)),
        (f"{year}-Q2", date(year, 4, 1), date(year, 6, 30)),
        (f"{year}-Q3", date(year, 7, 1), date(year, 9, 30)),
        (f"{year}-Q4", date(year, 10, 1), date(year, 12, 31)),
    ]


def _month_periods(year: int) -> list[tuple[str, date, date]]:
    out = []
    for m in range(1, 13):
        end_day = (date(year, m % 12 + 1, 1) if m < 12 else date(year + 1, 1, 1)) - timedelta(days=1)
        out.append((f"{year}-{m:02d}", date(year, m, 1), end_day))
    return out


def _q_due_303(year: int, q_idx: int) -> date:
    # Q1 → 20 Apr; Q2 → 20 Jul; Q3 → 20 Oct; Q4 → 30 Jan next year
    if q_idx < 3:
        return _shift_off_weekend(date(year, [4, 7, 10][q_idx], 20))
    return _shift_off_weekend(date(year + 1, 1, 30))


def _q_due_111_115(year: int, q_idx: int) -> date:
    # All quarters → 20th of following month; Q4 → 20 Jan next year
    if q_idx < 3:
        return _shift_off_weekend(date(year, [4, 7, 10][q_idx], 20))
    return _shift_off_weekend(date(year + 1, 1, 20))


def _q_due_130(year: int, q_idx: int) -> date:
    # Same as 303: Q1-Q3 → 20th, Q4 → 30 Jan
    return _q_due_303(year, q_idx)


def _generate_quarterly(
    year: int,
    modelo: str,
    name_es: str,
    name_en: str,
    legal_basis: str,
    payment_kind: str,
    due_fn,
    rate_hint: Optional[str] = None,
    threshold_hint: Optional[str] = None,
    reserve_pct_hint: Optional[Decimal] = None,
    notes: Optional[str] = None,
    applies_to: tuple[str, ...] = ("sl",),
) -> Iterable[ObligationSpec]:
    for i, (label, ps, pe) in enumerate(_q_periods(year)):
        due = due_fn(year, i)
        yield ObligationSpec(
            modelo=modelo,
            name_es=name_es,
            name_en=name_en,
            legal_basis=legal_basis,
            period_kind="quarterly",
            period_label=label,
            period_start=ps,
            period_end=pe,
            due_date=due,
            direct_debit_due_date=_ddebit(due),
            payment_kind=payment_kind,
            rate_hint=rate_hint,
            threshold_hint=threshold_hint,
            reserve_pct_hint=reserve_pct_hint,
            notes=notes,
            applies_to=applies_to,
        )


def calendar_for_fy(year: int) -> list[ObligationSpec]:
    """Full Spanish tax calendar for a fiscal year = calendar year `year`.

    Returns ObligationSpecs not yet bound to an entity. Caller filters by
    `applies_to` based on entity profile (SL / personal).
    """
    out: list[ObligationSpec] = []

    # ---- Modelo 303 — IVA quarterly ----------------------------------------
    out.extend(
        _generate_quarterly(
            year=year,
            modelo="303",
            name_es="Autoliquidación trimestral del IVA",
            name_en="Quarterly VAT self-assessment",
            legal_basis="art. 167.uno LIVA + RD 1624/1992 art. 71",
            payment_kind="self_assessed",
            due_fn=_q_due_303,
            rate_hint=f"{IVA_GENERAL}% / {IVA_REDUCIDO}% / {IVA_SUPERREDUCIDO}% / 0% (intra-EU & exports)",
            reserve_pct_hint=Decimal("100"),
            notes=(
                "Reserve full (IVA repercutido − IVA soportado deducible). "
                "Direct debit cuts off 5 days before deadline."
            ),
            applies_to=("sl",),
        )
    )

    # ---- Modelo 111 — IRPF retentions on professionals & payroll -----------
    out.extend(
        _generate_quarterly(
            year=year,
            modelo="111",
            name_es="Retenciones IRPF — rendimientos del trabajo y profesionales",
            name_en="IRPF withholdings on employment & professional services",
            legal_basis="art. 99-101 LIRPF + art. 76, 95 RIRPF",
            payment_kind="withheld",
            due_fn=_q_due_111_115,
            rate_hint=(
                f"{IRPF_PROFESIONALES}% profesionales (general) / "
                f"{IRPF_PROFESIONALES_INICIO}% inicio actividad (3 primeros años) / "
                "variable nóminas según tablas"
            ),
            reserve_pct_hint=Decimal("100"),
            notes="Pass-through: amounts already withheld from suppliers / employees.",
            applies_to=("sl",),
        )
    )

    # ---- Modelo 115 — IRPF retentions on urban rentals ---------------------
    out.extend(
        _generate_quarterly(
            year=year,
            modelo="115",
            name_es="Retenciones IRPF — arrendamientos urbanos",
            name_en="IRPF withholdings on urban rentals",
            legal_basis="art. 100 RIRPF",
            payment_kind="withheld",
            due_fn=_q_due_111_115,
            rate_hint=f"{IRPF_ALQUILERES}% sobre la base del alquiler (sin IVA)",
            reserve_pct_hint=Decimal("100"),
            notes=(
                "Sólo si la entidad alquila local/oficina a un arrendador persona "
                "física o jurídica sujeto a retención (excluye viviendas)."
            ),
            applies_to=("sl",),
        )
    )

    # ---- Modelo 130 — autónomo IRPF advance payments -----------------------
    out.extend(
        _generate_quarterly(
            year=year,
            modelo="130",
            name_es="IRPF estimación directa — pago fraccionado autónomo",
            name_en="Self-employed IRPF advance payment (direct estimation)",
            legal_basis="art. 109-110 RIRPF",
            payment_kind="advance_payment",
            due_fn=_q_due_130,
            rate_hint="20% del rendimiento neto YTD − pagos fraccionados anteriores − retenciones",
            reserve_pct_hint=Decimal("20"),
            notes="Sólo si la fundadora opera como autónoma; N/A si toda su actividad pasa por SL.",
            applies_to=("autonomo",),
        )
    )

    # ---- Modelo 202 — IS advance payments (Apr / Oct / Dec) ---------------
    for label_suffix, m, label_period_end in [
        ("1P", 4, date(year, 3, 31)),
        ("2P", 10, date(year, 9, 30)),
        ("3P", 12, date(year, 11, 30)),
    ]:
        due = _shift_off_weekend(date(year, m, 20))
        out.append(
            ObligationSpec(
                modelo="202",
                name_es="Pago fraccionado del Impuesto sobre Sociedades",
                name_en="Corporate income tax advance payment",
                legal_basis="art. 40 LIS",
                period_kind="triannual",
                period_label=f"{year}-{label_suffix}",
                period_start=date(year, 1, 1),
                period_end=label_period_end,
                due_date=due,
                direct_debit_due_date=_ddebit(due),
                payment_kind="advance_payment",
                rate_hint=(
                    f"Modalidad a) {M202_PCT_CUOTA}% sobre cuota íntegra del último 200 presentado | "
                    f"Modalidad b) {M202_PCT_BASE_PYME}% sobre base imponible del periodo "
                    f"({M202_PCT_BASE_GRANDE}% si INCN > €10M, mínimo 23% sobre resultado contable)"
                ),
                threshold_hint="Modalidad b) obligatoria si INCN del año anterior > €6.000.000",
                reserve_pct_hint=M202_PCT_BASE_PYME,
                notes=(
                    "Decisión modalidad a vs b se hace en febrero (modelo 036) y vincula todo el año. "
                    "Si modalidad a) y la cuota del 200 fue 0 / negativa, el 202 también es 0 (presentación informativa)."
                ),
                applies_to=("sl",),
            )
        )

    # ---- Modelo 349 — intracomunitarias (monthly default) -----------------
    # Defaulting to monthly per art. 80 RIVA (umbral trimestral: <€50k 4
    # cuatrimestres). Operator can later switch to quarterly per entity.
    for (label, ps, pe) in _month_periods(year):
        m = ps.month
        # Due 20th of following month
        due_year = year + 1 if m == 12 else year
        due_month = 1 if m == 12 else m + 1
        due = _shift_off_weekend(date(due_year, due_month, 20))
        out.append(
            ObligationSpec(
                modelo="349",
                name_es="Declaración recapitulativa de operaciones intracomunitarias",
                name_en="Recapitulative declaration of intra-Community operations",
                legal_basis="art. 78-81 RIVA",
                period_kind="monthly",
                period_label=label,
                period_start=ps,
                period_end=pe,
                due_date=due,
                direct_debit_due_date=None,
                payment_kind="informational",
                threshold_hint=(
                    "Cambia a trimestral si entregas+adquisiciones intracom. < €50.000 "
                    "en el trimestre actual y los 4 anteriores."
                ),
                notes=(
                    "Sólo aplica si hay operaciones con sujetos pasivos de IVA en otro Estado miembro UE. "
                    "Cowfy con Egipto/Qatar = exportación, NO intracom."
                ),
                applies_to=("sl",),
            )
        )

    # ---- Modelo 200 — IS annual --------------------------------------------
    # Fiscal year = calendar year → 1-25 July of following year
    is_due = _shift_off_weekend(date(year + 1, 7, 25))
    out.append(
        ObligationSpec(
            modelo="200",
            name_es="Impuesto sobre Sociedades — declaración anual",
            name_en="Corporate income tax — annual return",
            legal_basis="art. 124 LIS",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=is_due,
            direct_debit_due_date=_ddebit(is_due),
            payment_kind="self_assessed",
            rate_hint=(
                f"{IS_GENERAL}% general / {IS_PYME_REDUCIDO}% PYME (INCN < €1M) / "
                f"{IS_NUEVA_CREACION}% nueva creación (1er ejercicio con BI positiva + siguiente)"
            ),
            reserve_pct_hint=IS_GENERAL,
            notes=(
                "Plazo: 25 días naturales tras los 6 meses posteriores al cierre del ejercicio. "
                "Para ejercicio = año natural → 1-25 julio del año siguiente."
            ),
            applies_to=("sl",),
        )
    )

    # ---- Modelo 232 — operaciones vinculadas / paraísos fiscales -----------
    # 11th month after fiscal year end → November of following year
    m232_due = _shift_off_weekend(date(year + 1, 11, 30))
    out.append(
        ObligationSpec(
            modelo="232",
            name_es="Declaración informativa — operaciones vinculadas y con paraísos fiscales",
            name_en="Informative return — related-party operations & tax havens",
            legal_basis="Orden HFP/816/2017",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m232_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            threshold_hint=(
                f"Vinculadas mismo grupo: > €{M232_THRESHOLD_VINCULADAS_SAME:,} con misma persona/entidad | "
                f"Operaciones específicas: > €{M232_THRESHOLD_VINCULADAS_SPECIFIC:,} | "
                "Paraísos fiscales: cualquier importe"
            ),
            notes=(
                "CRÍTICO para SNT Holdings: management fees y licencias IP entre matriz y "
                "filiales son operaciones vinculadas y deben documentarse (master file / "
                "local file si grupo INCN > €45M)."
            ),
            applies_to=("sl",),
        )
    )

    # ---- Modelo 347 — operaciones con terceros >€3,005.06 -----------------
    m347_due = _shift_off_weekend(date(year + 1, 2, 28 if (year + 1) % 4 != 0 else 29))
    out.append(
        ObligationSpec(
            modelo="347",
            name_es="Declaración anual de operaciones con terceras personas",
            name_en="Annual return of operations with third parties",
            legal_basis="art. 31-35 RGAT (RD 1065/2007)",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m347_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            threshold_hint=f"> €{M347_THRESHOLD} acumulado por contraparte y año",
            notes=(
                "Excluye contrapartes ya incluidas en SII y operaciones intracom. (Modelo 349). "
                "Desglose trimestral obligatorio."
            ),
            applies_to=("sl",),
        )
    )

    # ---- Modelo 390 — IVA anual --------------------------------------------
    m390_due = _shift_off_weekend(date(year + 1, 1, 30))
    out.append(
        ObligationSpec(
            modelo="390",
            name_es="Declaración resumen anual del IVA",
            name_en="Annual VAT summary",
            legal_basis="art. 71.7 RIVA",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m390_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            notes="Resumen de los 4 modelos 303 del año; coincide con el último 303.",
            applies_to=("sl",),
        )
    )

    # ---- Modelo 190 — resumen anual de retenciones (cierra 111) ------------
    m190_due = _shift_off_weekend(date(year + 1, 1, 31))
    out.append(
        ObligationSpec(
            modelo="190",
            name_es="Resumen anual de retenciones e ingresos a cuenta — rendimientos del trabajo y profesionales",
            name_en="Annual summary — IRPF withholdings on employment & professional services",
            legal_basis="art. 108 RIRPF",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m190_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            notes="Cierra el ejercicio fiscal del modelo 111.",
            applies_to=("sl",),
        )
    )

    # ---- Modelo 180 — resumen anual de retenciones (cierra 115) ------------
    out.append(
        ObligationSpec(
            modelo="180",
            name_es="Resumen anual de retenciones — arrendamientos urbanos",
            name_en="Annual summary — IRPF withholdings on urban rentals",
            legal_basis="art. 108 RIRPF",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m190_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            applies_to=("sl",),
        )
    )

    # ---- Modelo 100 — IRPF persona física (annual) -------------------------
    irpf_start = _shift_off_weekend(date(year + 1, 4, 7))
    irpf_end = _shift_off_weekend(date(year + 1, 6, 30))
    irpf_dom_end = _shift_off_weekend(date(year + 1, 6, 25))
    out.append(
        ObligationSpec(
            modelo="100",
            name_es="Declaración del IRPF — Renta",
            name_en="Personal income tax return",
            legal_basis="Ley 35/2006 (LIRPF) + RIRPF",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=irpf_end,
            direct_debit_due_date=irpf_dom_end,
            payment_kind="self_assessed",
            rate_hint=(
                "Rentas del ahorro (dividendos, intereses, ganancias patrimoniales): "
                "TIPO PLANO del tramo donde caiga el total — NO progresivo. "
                "Hasta €6.000 → 19% | €6.000-50.000 → 21% | €50.000-200.000 → 23% | "
                "€200.000-300.000 → 27% | > €300.000 → 28%. "
                "Rentas del trabajo: progresivo estatal + autonómico (Madrid)."
            ),
            notes=(
                f"Campaña Renta {year}: ~7 abr – 30 jun {year + 1}. Domiciliación bancaria "
                f"hasta 25 jun {year + 1}."
            ),
            applies_to=("personal",),
        )
    )

    # ---- Modelo 714 — Patrimonio (annual) ----------------------------------
    out.append(
        ObligationSpec(
            modelo="714",
            name_es="Impuesto sobre el Patrimonio",
            name_en="Wealth tax",
            legal_basis="Ley 19/1991",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=irpf_end,
            direct_debit_due_date=irpf_dom_end,
            payment_kind="self_assessed",
            threshold_hint=(
                f"Obligados: cuota a ingresar > 0 OR (bienes+derechos > €2M) | "
                f"Base exenta general: €{PATRIMONIO_BASE_EXENTA_MADRID:,} | "
                f"Vivienda habitual exenta hasta €{PATRIMONIO_VIVIENDA_HABITUAL:,}"
            ),
            notes=(
                "Madrid: bonificación 100% (cuota a ingresar = 0) PERO sigue siendo declarable "
                "si bienes+derechos > €2M. Coexiste con ITSGF estatal (Impuesto Temporal "
                "de Solidaridad de las Grandes Fortunas) — verificar prórroga año en curso."
            ),
            applies_to=("personal",),
        )
    )

    # ---- Modelo 720 — bienes en el extranjero (annual, Mar) ----------------
    m720_due = _shift_off_weekend(date(year + 1, 3, 31))
    out.append(
        ObligationSpec(
            modelo="720",
            name_es="Declaración de bienes y derechos situados en el extranjero",
            name_en="Foreign assets & rights declaration",
            legal_basis="DA 18 LGT",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=m720_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            threshold_hint=(
                f"Obligación si > €{M720_THRESHOLD:,} en cualquiera de los 3 bloques: "
                "(1) cuentas bancarias | (2) valores/seguros/fondos | (3) inmuebles. "
                "Tras la primera declaración, sólo si el saldo aumenta > €20.000 o se "
                "extinguen titularidades."
            ),
            notes=(
                "Tras STJUE C-788/19 (27-ene-2022) las sanciones desproporcionadas fueron "
                "anuladas; régimen sancionador moderado por Ley 5/2022."
            ),
            applies_to=("personal", "sl"),
        )
    )

    # ---- D-6 — depósito de valores en el extranjero (annual, Jan) ----------
    d6_due = _shift_off_weekend(date(year + 1, 1, 31))
    out.append(
        ObligationSpec(
            modelo="D-6",
            name_es="Declaración titularidad de valores negociables depositados en el extranjero",
            name_en="Securities deposited abroad",
            legal_basis="OM 28-may-2001 + Ley 19/2003",
            period_kind="annual",
            period_label=f"FY{year}",
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            due_date=d6_due,
            direct_debit_due_date=None,
            payment_kind="informational",
            notes=(
                "Aplica a residentes con valores depositados en entidades NO residentes. "
                "Se presenta ante el Registro de Inversiones (Subdirección General de "
                "Comercio Internacional de Servicios e Inversiones), no AEAT."
            ),
            applies_to=("personal", "sl"),
        )
    )

    return out


def calendar_for_personal(year: int) -> list[ObligationSpec]:
    return [o for o in calendar_for_fy(year) if "personal" in o.applies_to]


def calendar_for_sl(year: int, has_intracom: bool = False, is_autonomo: bool = False) -> list[ObligationSpec]:
    items = [o for o in calendar_for_fy(year) if "sl" in o.applies_to or (is_autonomo and "autonomo" in o.applies_to)]
    if not has_intracom:
        items = [o for o in items if o.modelo != "349"]
    return items
