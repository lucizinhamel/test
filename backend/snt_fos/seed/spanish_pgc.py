"""Spanish Plan General Contable (PGC) seed — Real Decreto 1514/2007.

Curated subset of the most-used accounts for a tech/services SL holding.
The full PGC has 9 grupos and ~600 accounts; we seed ~90 here. Founder can
add custom sub-accounts per entity later (the schema allows it).

Each tuple is (code, name_es, name_en, nature, iva_default_pct).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# (code, name_es, name_en, nature, iva_default_pct or None)
PGC_ACCOUNTS: list[tuple[str, str, str, str, Optional[Decimal]]] = [
    # === Grupo 1 — Financiación básica =====================================
    ("100", "Capital social", "Share capital", "credit", None),
    ("112", "Reserva legal", "Legal reserve", "credit", None),
    ("113", "Reservas voluntarias", "Voluntary reserves", "credit", None),
    ("118", "Aportaciones de socios o propietarios", "Shareholder contributions", "credit", None),
    ("121", "Resultados negativos de ejercicios anteriores", "Carried-forward losses", "debit", None),
    ("129", "Resultado del ejercicio", "Profit / loss for the year", "credit", None),
    ("170", "Deudas a largo plazo con entidades de crédito", "Long-term bank debt", "credit", None),
    ("171", "Deudas a largo plazo", "Long-term debt — other", "credit", None),

    # === Grupo 2 — Activo no corriente =====================================
    ("200", "Investigación", "Research", "debit", None),
    ("201", "Desarrollo", "Development", "debit", None),
    ("203", "Propiedad industrial", "Industrial property / patents", "debit", None),
    ("206", "Aplicaciones informáticas", "Software / capitalized software", "debit", None),
    ("210", "Terrenos y bienes naturales", "Land", "debit", None),
    ("211", "Construcciones", "Buildings", "debit", None),
    ("213", "Maquinaria", "Machinery", "debit", None),
    ("215", "Otras instalaciones", "Other installations", "debit", None),
    ("216", "Mobiliario", "Furniture & fittings", "debit", None),
    ("217", "Equipos para procesos de información", "IT equipment", "debit", None),
    ("218", "Elementos de transporte", "Vehicles", "debit", None),
    ("280", "Amortización acumulada del inmovilizado intangible", "Accumulated amortization — intangibles", "credit", None),
    ("281", "Amortización acumulada del inmovilizado material", "Accumulated depreciation — tangibles", "credit", None),

    # === Grupo 3 — Existencias =============================================
    ("300", "Mercaderías", "Inventory — merchandise", "debit", None),
    ("310", "Materias primas", "Raw materials", "debit", None),

    # === Grupo 4 — Acreedores y deudores ===================================
    ("400", "Proveedores", "Suppliers (trade payables)", "credit", None),
    ("410", "Acreedores por prestaciones de servicios", "Service creditors", "credit", None),
    ("430", "Clientes", "Customers (trade receivables)", "debit", None),
    ("431", "Clientes, efectos comerciales a cobrar", "Notes receivable from customers", "debit", None),
    ("436", "Clientes de dudoso cobro", "Doubtful customer accounts", "debit", None),
    ("440", "Deudores", "Other debtors", "debit", None),
    ("465", "Remuneraciones pendientes de pago", "Payroll payable", "credit", None),
    # 470 H.P. Deudora
    ("4700", "H.P. deudora por IVA", "Tax authority — VAT receivable", "debit", None),
    ("4708", "H.P. deudora por subvenciones concedidas", "Tax authority — subsidies receivable", "debit", None),
    ("4709", "H.P. deudora por devolución de impuestos", "Tax authority — tax refunds receivable", "debit", None),
    ("471", "Organismos de la Seguridad Social, deudores", "Social Security receivable", "debit", None),
    ("472", "H.P. IVA soportado", "VAT input (paid)", "debit", None),
    ("473", "H.P. retenciones y pagos a cuenta", "Withholdings & advance payments receivable", "debit", None),
    # 475 H.P. Acreedora
    ("4750", "H.P. acreedora por IVA", "Tax authority — VAT payable", "credit", None),
    ("4751", "H.P. acreedora por retenciones practicadas", "Tax authority — IRPF withholdings payable (M111)", "credit", None),
    ("4752", "H.P. acreedora por Impuesto sobre Sociedades", "Tax authority — corporate tax payable", "credit", None),
    ("4758", "H.P. acreedora por subvenciones a reintegrar", "Tax authority — subsidies refundable", "credit", None),
    ("476", "Organismos de la Seguridad Social, acreedores", "Social Security payable", "credit", None),
    ("477", "H.P. IVA repercutido", "VAT output (charged)", "credit", None),

    # === Grupo 5 — Cuentas financieras =====================================
    ("520", "Deudas a corto plazo con entidades de crédito", "Short-term bank debt", "credit", None),
    ("523", "Proveedores de inmovilizado a corto plazo", "Short-term fixed-asset suppliers", "credit", None),
    ("555", "Partidas pendientes de aplicación", "Pending application", "debit", None),
    ("570", "Caja, euros", "Cash on hand — EUR", "debit", None),
    ("572", "Bancos e instituciones de crédito c/c, euros", "Bank current account — EUR", "debit", None),
    ("573", "Bancos e instituciones de crédito c/c, moneda extranjera", "Bank current account — FX", "debit", None),

    # === Grupo 6 — Compras y gastos ========================================
    ("600", "Compras de mercaderías", "Cost of goods sold", "debit", Decimal("21")),
    ("602", "Compras de otros aprovisionamientos", "Other supplies purchased", "debit", Decimal("21")),
    ("607", "Trabajos realizados por otras empresas", "Subcontracting", "debit", Decimal("21")),
    ("621", "Arrendamientos y cánones", "Rentals & royalties", "debit", Decimal("21")),
    ("622", "Reparaciones y conservación", "Repairs & maintenance", "debit", Decimal("21")),
    ("623", "Servicios de profesionales independientes", "Independent professional services", "debit", Decimal("21")),
    ("624", "Transportes", "Transport", "debit", Decimal("21")),
    ("625", "Primas de seguros", "Insurance", "debit", None),
    ("626", "Servicios bancarios y similares", "Bank fees", "debit", None),
    ("627", "Publicidad, propaganda y relaciones públicas", "Advertising, marketing & PR", "debit", Decimal("21")),
    ("628", "Suministros", "Utilities (electricity, water, internet)", "debit", Decimal("21")),
    ("629", "Otros servicios", "Other services", "debit", Decimal("21")),
    ("630", "Impuesto sobre beneficios", "Corporate income tax (P&L charge)", "debit", None),
    ("631", "Otros tributos", "Other taxes", "debit", None),
    ("640", "Sueldos y salarios", "Salaries & wages", "debit", None),
    ("642", "Seguridad Social a cargo de la empresa", "Employer Social Security", "debit", None),
    ("649", "Otros gastos sociales", "Other staff costs", "debit", None),
    ("662", "Intereses de deudas", "Interest expense", "debit", None),
    ("668", "Diferencias negativas de cambio", "FX loss", "debit", None),
    ("669", "Otros gastos financieros", "Other finance costs", "debit", None),
    ("678", "Gastos excepcionales", "Exceptional expenses", "debit", None),
    ("680", "Amortización del inmovilizado intangible", "Amortization — intangible assets", "debit", None),
    ("681", "Amortización del inmovilizado material", "Depreciation — tangible assets", "debit", None),
    ("694", "Pérdidas por deterioro de créditos comerciales", "Bad-debt provision", "debit", None),

    # === Grupo 7 — Ventas e ingresos =======================================
    ("700", "Ventas de mercaderías", "Sales — goods", "credit", Decimal("21")),
    ("705", "Prestaciones de servicios", "Sales — services", "credit", Decimal("21")),
    ("706", "Descuentos sobre ventas por pronto pago", "Early-payment discounts on sales", "debit", None),
    ("708", "Devoluciones de ventas y operaciones similares", "Sales returns", "debit", None),
    ("709", "Rappels sobre ventas", "Volume rebates on sales", "debit", None),
    ("752", "Ingresos por arrendamientos", "Rental income", "credit", Decimal("21")),
    ("759", "Ingresos por servicios diversos", "Other service income", "credit", Decimal("21")),
    ("762", "Ingresos de créditos", "Interest income", "credit", None),
    ("768", "Diferencias positivas de cambio", "FX gain", "credit", None),
    ("769", "Otros ingresos financieros", "Other financial income", "credit", None),
    ("778", "Ingresos excepcionales", "Exceptional income", "credit", None),
]


# Personal book — simplified non-PGC categorical CoA.
PERSONAL_ACCOUNTS: list[tuple[str, str, str, str]] = [
    # group_code, code, name_es, name_en, nature
    ("PERSONAL_ASSET", "P-100", "Caja personal", "Personal cash", "debit"),
    ("PERSONAL_ASSET", "P-110", "Banco — cuenta principal", "Bank — primary account", "debit"),
    ("PERSONAL_ASSET", "P-120", "Banco — Revolut personal", "Bank — Revolut personal", "debit"),
    ("PERSONAL_ASSET", "P-130", "Inversiones (broker)", "Brokerage holdings", "debit"),
    ("PERSONAL_ASSET", "P-140", "Inmuebles", "Real estate", "debit"),
    ("PERSONAL_ASSET", "P-150", "Vehículos", "Vehicles", "debit"),
    ("PERSONAL_LIABILITY", "P-200", "Hipoteca", "Mortgage", "credit"),
    ("PERSONAL_LIABILITY", "P-210", "Otros préstamos", "Other loans", "credit"),
    ("PERSONAL_INCOME", "P-700", "Salario (SNT/Cowfy)", "Salary income", "credit"),
    ("PERSONAL_INCOME", "P-710", "Dividendos", "Dividend income", "credit"),
    ("PERSONAL_INCOME", "P-720", "Ganancias patrimoniales", "Capital gains", "credit"),
    ("PERSONAL_INCOME", "P-790", "Otros ingresos", "Other income", "credit"),
    ("PERSONAL_EXPENSE", "P-800", "Vivienda", "Housing", "debit"),
    ("PERSONAL_EXPENSE", "P-805", "Suministros del hogar", "Utilities — home", "debit"),
    ("PERSONAL_EXPENSE", "P-810", "Transporte", "Transport", "debit"),
    ("PERSONAL_EXPENSE", "P-815", "Alimentación", "Food & groceries", "debit"),
    ("PERSONAL_EXPENSE", "P-820", "Restaurantes", "Restaurants", "debit"),
    ("PERSONAL_EXPENSE", "P-825", "Fitness y bienestar", "Fitness & wellness", "debit"),
    ("PERSONAL_EXPENSE", "P-830", "Educación", "Education (Harvard, courses)", "debit"),
    ("PERSONAL_EXPENSE", "P-835", "Aviación (PPL)", "Aviation training", "debit"),
    ("PERSONAL_EXPENSE", "P-840", "Belleza y cuidado personal", "Beauty & skincare", "debit"),
    ("PERSONAL_EXPENSE", "P-845", "Viajes", "Travel", "debit"),
    ("PERSONAL_EXPENSE", "P-850", "Regalos", "Gifts", "debit"),
    ("PERSONAL_EXPENSE", "P-855", "Suscripciones", "Subscriptions", "debit"),
    ("PERSONAL_EXPENSE", "P-860", "Salud", "Health & medical", "debit"),
    ("PERSONAL_EXPENSE", "P-870", "Fotografía y equipo", "Photography & gear", "debit"),
    ("PERSONAL_EXPENSE", "P-880", "Impuestos personales", "Personal taxes", "debit"),
    ("PERSONAL_EXPENSE", "P-890", "Otros gastos", "Other expenses", "debit"),
    ("PERSONAL_INVESTMENT", "P-900", "Aportaciones a inversión", "Investment contributions", "debit"),
    ("PERSONAL_TRANSFER", "P-950", "Transferencias internas", "Internal transfers", "debit"),
]


def pgc_for_sl() -> list[dict]:
    rows = []
    for i, (code, es, en, nature, iva) in enumerate(PGC_ACCOUNTS):
        rows.append(
            dict(
                code=code,
                name_es=es,
                name_en=en,
                group_code=code[0],
                nature=nature,
                iva_rate_default=iva,
                is_postable=True,
                sort_order=i,
            )
        )
    return rows


def coa_for_personal() -> list[dict]:
    rows = []
    for i, (group, code, es, en, nature) in enumerate(PERSONAL_ACCOUNTS):
        rows.append(
            dict(
                code=code,
                name_es=es,
                name_en=en,
                group_code=group,
                nature=nature,
                iva_rate_default=None,
                is_postable=True,
                sort_order=i,
            )
        )
    return rows
