# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import copy
import json
import logging
import uuid

_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Standard Odoo Product dashboard
# -------------------------------------------------------------------------

DASHBOARD_XMLID = (
    "spreadsheet_dashboard_sale.spreadsheet_dashboard_product"
)

DASHBOARD_SHEET_NAME = "Dashboard"
DATA_SHEET_NAME = "Data"


# -------------------------------------------------------------------------
# Product dashboard scorecards
# -------------------------------------------------------------------------

SCORECARD_TITLES = (
    "Best Seller",
    "Best Category",
    "Least Seller",
    "Least Category",
)

SCORECARD_WIDTH = 220
SCORECARD_HEIGHT = 108

SCORECARD_POSITIONS = {
    "Best Seller": 0,
    "Best Category": 230,
    "Least Seller": 460,
    "Least Category": 690,
}

# Rank (within the same sorted pivot Best Seller/Category already use)
# treated as the "least" position. Rather than a fixed number (which
# would show "-" until 10 products/categories exist), this is computed
# per-dashboard from how many rows the corresponding pivot's own spill
# actually populated: COUNTA on the pivot's already-spilled name
# column counts only the non-blank rows, i.e. the true last rank,
# whatever that currently is. Products and categories are counted
# separately since they come from different pivots (1 and 2) with
# spills landing in different columns (A and E respectively - see
# PRODUCT_NAME_COLUMN and CATEGORY_NAME_COLUMN).


# -------------------------------------------------------------------------
# Best Selling Products table
# -------------------------------------------------------------------------

# A47 is the clickable "Best Selling Products" title link, NOT the table
# header - PIVOT(1, 10, FALSE, FALSE) actually spills starting at A48,
# with A48:C48 as the pivot's own header row ("Product"/"Units"/
# "Revenue") and A49:C58 as the 10 data rows. Confirmed against the
# base file's own table range definition (A48:C58). An earlier version
# of this file used 47/48/57 here, one row too high throughout - this
# misplaced the "Avg % of Revenue" header (landed next to the section
# title instead of above the data) and silently divided the first data
# row against the pivot's own header text instead of real revenue.
PRODUCT_TABLE_HEADER_ROW = 48
PRODUCT_TABLE_FIRST_ROW = 49
PRODUCT_TABLE_LAST_ROW = 58

PRODUCT_NAME_COLUMN = "A"
PRODUCT_REVENUE_COLUMN = "C"
PRODUCT_PERCENTAGE_COLUMN = "D"

# E48 = PIVOT(2, 10, FALSE, FALSE), the "Best Selling Categories" data
# table view (separate from the visual carousel figure) - same header/
# data row split as the product table above, spilling into E48:G58.
CATEGORY_NAME_COLUMN = "E"
CATEGORY_REVENUE_COLUMN = "G"
CATEGORY_PERCENTAGE_COLUMN = "H"


# =========================================================================
# POST INIT HOOK
# =========================================================================

def _post_init_hook(env):
    """
    Enhance the standard Odoo Product spreadsheet dashboard.

    Features:

    1. Keep the four Product scorecards correctly positioned.
    2. Add Avg % of Revenue to the Best Selling Products section.
    3. Do not modify the existing Product/Category pivots.
    4. Make Best Seller, Best Category, Least Seller, and Least Category
       clickable to the standard Sales Analysis reporting menu.
    5. Make the operation safe to execute multiple times.
    """

    _logger.info(
        "=================================================="
    )
    _logger.info(
        "Product Dashboard Enhancement Hook Started"
    )
    _logger.info(
        "=================================================="
    )

    # -------------------------------------------------------------
    # Find standard Product dashboard
    # -------------------------------------------------------------

    dashboard = env.ref(
        DASHBOARD_XMLID,
        raise_if_not_found=False,
    )

    if not dashboard:
        _logger.warning(
            "Product dashboard not found: %s",
            DASHBOARD_XMLID,
        )
        return

    if not dashboard.spreadsheet_binary_data:
        _logger.warning(
            "Product dashboard has no spreadsheet data."
        )
        return

    # -------------------------------------------------------------
    # Decode spreadsheet JSON
    # -------------------------------------------------------------

    try:
        data = json.loads(
            base64.b64decode(
                dashboard.spreadsheet_binary_data
            ).decode("utf-8")
        )
    except Exception:
        _logger.exception(
            "Could not decode Product dashboard spreadsheet data."
        )
        return

    # -------------------------------------------------------------
    # Find Dashboard sheet
    # -------------------------------------------------------------

    dashboard_sheet = _get_sheet(
        data,
        DASHBOARD_SHEET_NAME,
    )

    if dashboard_sheet is None:
        _logger.warning(
            "Dashboard sheet '%s' was not found.",
            DASHBOARD_SHEET_NAME,
        )
        return

    data_sheet = _get_sheet(
        data,
        DATA_SHEET_NAME,
    )

    if data_sheet is None:
        _logger.warning(
            "Data sheet '%s' was not found.",
            DATA_SHEET_NAME,
        )
        return

    # -------------------------------------------------------------
    # Fix scorecards
    # -------------------------------------------------------------

    _fix_scorecards(dashboard_sheet, data_sheet, data)

    # -------------------------------------------------------------
    # Add % of Revenue to Product and Category tables
    # -------------------------------------------------------------

    _add_revenue_percentages(
        dashboard_sheet,
    )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    dashboard.write({
        "spreadsheet_binary_data": base64.b64encode(
            json.dumps(
                data,
                ensure_ascii=False,
            ).encode("utf-8")
        ),
    })

    env.cr.commit()

    _logger.info(
        "Product Dashboard Enhancement Hook Completed."
    )


# =========================================================================
# SHEET HELPER
# =========================================================================

def _get_sheet(data, name):
    """
    Return a spreadsheet sheet by name.
    """

    for sheet in data.get("sheets", []):
        if sheet.get("name") == name:
            return sheet

    return None


# =========================================================================
# SCORECARD LAYOUT
# =========================================================================

def _fix_scorecards(dashboard_sheet, data_sheet, data):
    """
    Ensure all four Product scorecards exist, then keep them in one
    horizontal row.

    The base Odoo dashboard only ships "Best Seller" and "Best
    Category" (see Data!B2:D3, which use PIVOT.HEADER/PIVOT.VALUE
    with rank 1 to read the top-ranked product/category from the
    already-sorted pivots). "Least Seller" and "Least Category" do
    not exist in the base file and must be created here, using the
    same rank-based formulas but pointed at whichever rank is
    genuinely last (computed dynamically - see _add_least_data_rows)
    instead of rank 1.
    """

    figures = dashboard_sheet.setdefault(
        "figures",
        [],
    )

    cards = {}

    # -------------------------------------------------------------
    # Locate existing scorecards
    # -------------------------------------------------------------

    for figure in figures:

        if (
            figure.get("tag") != "chart"
            or figure.get("data", {}).get("type")
            != "scorecard"
        ):
            continue

        title = (
            figure.get("data", {})
            .get("title", {})
            .get("text")
        )

        if title in SCORECARD_TITLES:
            cards[title] = figure

    # -------------------------------------------------------------
    # Create any missing scorecards (Least Seller / Least Category)
    # -------------------------------------------------------------
    #
    # IMPORTANT:
    # Do NOT build Least Seller from a manually guessed scorecard JSON
    # when the standard Best Seller card already exists.
    #
    # Odoo stores the "Link to Odoo menu" configuration as part of the
    # chart/figure definition. The exact location/shape can vary between
    # Odoo spreadsheet builds. Cloning the native Best Seller figure first
    # guarantees that all native metadata is retained.
    #
    # We then replace only the fields that are specific to Least Seller:
    # title, value formula, baseline formula, and chart/figure IDs.
    # -------------------------------------------------------------

    missing = sorted(
        set(SCORECARD_TITLES)
        - set(cards.keys())
    )

    if missing:
        _add_least_data_rows(data_sheet)

        for title in missing:
            if title == "Least Seller" and "Best Seller" in cards:
                cards[title] = _clone_scorecard_with_least_data(
                    cards["Best Seller"],
                    title="Least Seller",
                    data_row=4,
                )
            elif title == "Least Category" and "Best Category" in cards:
                cards[title] = _clone_scorecard_with_least_data(
                    cards["Best Category"],
                    title="Least Category",
                    data_row=5,
                )
            else:
                cards[title] = _build_least_scorecard(title)

            figures.append(cards[title])

        _logger.info(
            "Created missing scorecards: %s",
            missing,
        )

    # -------------------------------------------------------------
    # Repair Least Seller navigation every time the hook runs
    # -------------------------------------------------------------
    #
    # If Least Seller was created by an older version of this module, it
    # may already exist but lack the native Odoo menu-link configuration.
    # Re-clone the complete Best Seller figure and preserve the Least Seller
    # formulas/content. This is more reliable than guessing the internal
    # link-property name.
    # -------------------------------------------------------------

    if "Best Seller" in cards and "Least Seller" in cards:
        _sync_scorecard_from_source(
            cards["Best Seller"],
            cards["Least Seller"],
            title="Least Seller",
            data_row=4,
        )
        _logger.info(
            "Least Seller is cloned from native Best Seller figure; "
            "all native chart/link metadata has been preserved."
        )
        _logger.info(
            "Least Seller scorecard navigation synchronized from "
            "Best Seller."
        )

        # ---------------------------------------------------------
        # Register the KPI cards in Odoo's chartOdooMenusReferences.
        #
        # The destination requested here is the standard Sales Analysis
        # reporting menu. In the user's Odoo 19 database this menu opens
        # the Sales Analysis report, where the Graph view shown in the
        # screenshot is available.
        #
        # The relation is stored at spreadsheet level, not inside the
        # scorecard's data dictionary. Therefore every KPI that should
        # be clickable must have its own figure-id entry here.
        # ---------------------------------------------------------
        chart_menu_refs = data.setdefault(
            "chartOdooMenusReferences",
            {},
        )

        sales_analysis_menu = "sale.menu_reporting_sales"

        for card_title in SCORECARD_TITLES:
            card_figure = cards.get(card_title)
            if not card_figure:
                continue

            card_id = card_figure.get("id")
            if not card_id:
                continue

            chart_menu_refs[card_id] = sales_analysis_menu

            _logger.info(
                "%s KPI navigation registered: %s -> %s",
                card_title,
                card_id,
                sales_analysis_menu,
            )

        # Keep the target figure ID registered as a spreadsheet figure ID
        # when Odoo's JSON contains the uniqueFigureIds collection.
        unique_figure_ids = data.get("uniqueFigureIds")

        if isinstance(unique_figure_ids, list) and least_seller_id:
            if least_seller_id not in unique_figure_ids:
                unique_figure_ids.append(least_seller_id)

    # -------------------------------------------------------------
    # Position cards
    # -------------------------------------------------------------

    for title, x in SCORECARD_POSITIONS.items():

        figure = cards[title]

        figure["width"] = SCORECARD_WIDTH
        figure["height"] = SCORECARD_HEIGHT

        figure.setdefault(
            "offset",
            {},
        )

        figure["offset"]["x"] = x
        figure["offset"]["y"] = 12

    _logger.info(
        "Four Product scorecards positioned successfully."
    )


def _clone_scorecard_with_least_data(source_figure, title, data_row):
    """
    Clone a native Odoo scorecard and change only its Least-* data.

    This is used when the Least Seller/Category card does not yet exist.
    Cloning the native card preserves every native chart property, including
    the Odoo menu-link configuration.
    """
    cloned = copy.deepcopy(source_figure)

    # Every spreadsheet figure/chart needs its own unique IDs.
    cloned["id"] = str(uuid.uuid4())

    data = cloned.setdefault("data", {})
    data["chartId"] = cloned["id"]
    data.setdefault("title", {})
    data["title"]["text"] = title

    data["baseline"] = f"Data!C{data_row}"
    data["keyValue"] = f"Data!B{data_row}"

    return cloned


def _sync_scorecard_from_source(source_figure, target_figure, title, data_row):
    """
    Synchronize an existing custom scorecard with the native source
    scorecard while preserving the target's own identity and Least-* data.

    The complete source figure is copied first. This is intentional:
    Odoo's internal chart-link representation is not hard-coded here.
    Whatever native navigation metadata Best Seller has is therefore
    transferred exactly to Least Seller.

    Then the target-specific fields are restored.
    """
    target_id = target_figure.get("id") or str(uuid.uuid4())

    target_data = target_figure.get("data", {})
    target_chart_id = target_data.get("chartId") or target_id

    cloned = copy.deepcopy(source_figure)

    # Keep Least Seller's own identity.
    cloned["id"] = target_id
    cloned["width"] = target_figure.get("width", cloned.get("width"))
    cloned["height"] = target_figure.get("height", cloned.get("height"))
    cloned["offset"] = copy.deepcopy(target_figure.get("offset", cloned.get("offset", {})))
    cloned["col"] = target_figure.get("col", cloned.get("col", 0))
    cloned["row"] = target_figure.get("row", cloned.get("row", 0))

    data = cloned.setdefault("data", {})
    data["chartId"] = target_chart_id
    data.setdefault("title", {})
    data["title"]["text"] = title

    # Least Seller uses Data!B4/C4; Least Category uses Data!B5/C5.
    data["baseline"] = f"Data!C{data_row}"
    data["keyValue"] = f"Data!B{data_row}"

    # Keep the target's visual title if it had one, otherwise the source
    # styling is retained automatically.
    if isinstance(target_data.get("title"), dict):
        for key in ("color", "bold", "italic", "fontSize"):
            if key in target_data["title"]:
                data["title"][key] = target_data["title"][key]

    target_figure.clear()
    target_figure.update(cloned)




def _add_least_data_rows(data_sheet):
    """
    Add Data sheet rows 4-5 for Least Seller / Least Category,
    mirroring the base module's own rows 2-3 (Best Seller/Category)
    but reading from the LAST populated rank instead of rank 1.

    The rank is computed dynamically as COUNTA() over the
    corresponding pivot's own already-spilled name column on the
    Dashboard sheet (A49:A58 for products, E49:E58 for categories) -
    this equals however many real rows currently exist, adapting
    automatically as products/categories are added or removed, rather
    than a fixed number that would show "-" until 10 exist.

    IFERROR below still guards the edge case of zero rows (an empty
    store), where COUNTA returns 0 and PIVOT.HEADER/PIVOT.VALUE with
    rank 0 would error.
    """

    cells = data_sheet.setdefault("cells", {})

    product_rank = (
        f"COUNTA({DASHBOARD_SHEET_NAME}!"
        f"${PRODUCT_NAME_COLUMN}${PRODUCT_TABLE_FIRST_ROW}:"
        f"${PRODUCT_NAME_COLUMN}${PRODUCT_TABLE_LAST_ROW})"
    )
    category_rank = (
        f"COUNTA({DASHBOARD_SHEET_NAME}!"
        f"${CATEGORY_NAME_COLUMN}${PRODUCT_TABLE_FIRST_ROW}:"
        f"${CATEGORY_NAME_COLUMN}${PRODUCT_TABLE_LAST_ROW})"
    )

    cells["A4"] = '=_t("Least selling product")'
    cells["B4"] = (
        f'=IFERROR(PIVOT.HEADER(1,"#product_id",{product_rank}), "-")'
    )
    cells["C4"] = (
        f'=IFERROR(PIVOT.VALUE(1,"product_uom_qty","#product_id",{product_rank}), 0)'
    )
    cells["D4"] = (
        f'=IFERROR(FORMAT.LARGE.NUMBER('
        f'PIVOT.VALUE(1,"price_subtotal","#product_id",{product_rank})), 0)'
    )

    cells["A5"] = '=_t("Least selling category")'
    cells["B5"] = (
        f'=IFERROR(PIVOT.HEADER(2,"#categ_id",{category_rank}), "-")'
    )
    cells["C5"] = (
        f'=IFERROR(PIVOT.VALUE(2,"product_uom_qty","#categ_id",{category_rank}), 0)'
    )
    cells["D5"] = (
        f'=IFERROR(FORMAT.LARGE.NUMBER('
        f'PIVOT.VALUE(2,"price_subtotal","#categ_id",{category_rank})), 0)'
    )


def _build_least_scorecard(title):
    """
    Build a scorecard figure for "Least Seller" or "Least Category",
    matching the structure/style of the base module's Best
    Seller/Category cards (baselineMode "text", baseline shows units
    sold, keyValue shows the product/category name).
    """

    row = 4 if title == "Least Seller" else 5
    card_id = str(uuid.uuid4())

    return {
        "id": card_id,
        "width": SCORECARD_WIDTH,
        "height": SCORECARD_HEIGHT,
        "tag": "chart",
        "data": {
            "baselineColorDown": "#DC6965",
            "baselineColorUp": "#00A04A",
            "baselineMode": "text",
            "title": {
                "text": title,
                "color": "#434343",
                "bold": True,
            },
            "type": "scorecard",
            "background": "#FEF2F2",
            "baseline": f"Data!C{row}",
            "baselineDescr": {"text": "sold"},
            "keyValue": f"Data!B{row}",
            "humanize": False,
            "chartId": card_id,
        },
        "offset": {"x": 0, "y": 12},
        "col": 0,
        "row": 0,
    }


# =========================================================================
# % OF REVENUE - PRODUCTS AND CATEGORIES
# =========================================================================

def _add_revenue_percentages(dashboard_sheet):
    """
    Add a live ``% of Revenue`` column to both dashboard tables.

    Product table:
        A48:D58 -> Product / Units / Revenue / % of Revenue

    Category table:
        E48:H58 -> Category / Units / Revenue / % of Revenue

    The percentage formulas deliberately use the corresponding Odoo pivot's
    TOTAL revenue (PIVOT.VALUE without a group/rank filter) as the denominator.
    This is important because the visible table is a Top-10 spill: summing only
    the visible rows can produce an incorrect percentage when there are more
    than ten products/categories.  Using the pivot total also keeps the value
    live when sales data changes.

    ``TEXT(..., "0.0%")`` is used to keep the display consistent with the
    existing Product dashboard instead of showing raw decimal values such as
    0.92222798.
    """

    cells = dashboard_sheet.setdefault(
        "cells",
        {}
    )

    # -------------------------------------------------------------
    # Table coordinates
    # -------------------------------------------------------------

    product_name_col = PRODUCT_NAME_COLUMN
    product_rev_col = PRODUCT_REVENUE_COLUMN
    product_pct_col = PRODUCT_PERCENTAGE_COLUMN

    category_name_col = CATEGORY_NAME_COLUMN
    category_rev_col = CATEGORY_REVENUE_COLUMN
    category_pct_col = CATEGORY_PERCENTAGE_COLUMN

    first = PRODUCT_TABLE_FIRST_ROW
    last = PRODUCT_TABLE_LAST_ROW

    # -------------------------------------------------------------
    # Headers
    # -------------------------------------------------------------

    cells[f"{product_pct_col}{PRODUCT_TABLE_HEADER_ROW}"] = (
        '=_t("% of Revenue")'
    )
    cells[f"{category_pct_col}{PRODUCT_TABLE_HEADER_ROW}"] = (
        '=_t("% of Revenue")'
    )

    # -------------------------------------------------------------
    # Product percentages
    # -------------------------------------------------------------

    # Pivot 1 is the Best Selling Products pivot.  Do NOT calculate the
    # denominator from C49:C58 because that is only the visible Top-10 rows.
    product_total_formula = (
        '=IFERROR(PIVOT.VALUE(1,"price_subtotal"),0)'
    )

    for row in range(first, last + 1):
        cells[f"{product_pct_col}{row}"] = (
            f'=IF({product_name_col}{row}="", "", '
            f'IFERROR(TEXT({product_rev_col}{row}/'
            f'({product_total_formula[1:]}), "0.0%"), ""))'
        )

    # -------------------------------------------------------------
    # Category percentages
    # -------------------------------------------------------------

    # Pivot 2 is the Best Selling Categories pivot.  Use its total revenue
    # rather than SUM(G49:G58), so the percentage always represents the
    # category's share of the complete sales revenue and stays correct when
    # the underlying sales data changes.
    category_total_formula = (
        '=IFERROR(PIVOT.VALUE(2,"price_subtotal"),0)'
    )

    for row in range(first, last + 1):
        cells[f"{category_pct_col}{row}"] = (
            f'=IF({category_name_col}{row}="", "", '
            f'IFERROR(TEXT({category_rev_col}{row}/'
            f'({category_total_formula[1:]}), "0.0%"), ""))'
        )

    # -------------------------------------------------------------
    # Resize A-D so the "Avg % of Revenue" header/values have real
    # room, then position the carousel with a genuine gap after
    # column D - not the near-zero overlap used in an earlier version
    # of this function.
    #
    # The carousel's own title ("Best Selling Categories") renders at
    # fontSize 21, bold - much larger than the small pivot header text
    # (e.g. "Category") it sits over inside the carousel box. The
    # earlier ~1px overlap was sized for that small pivot text and
    # left the much bigger title crowding directly against "Avg % of
    # Revenue" with no breathing room. This version gives the title a
    # real CAROUSEL_TITLE_GAP-px gap instead, which does shift the
    # whole categories block slightly right of Odoo's own original
    # position - an accepted, deliberate trade-off for readability.
    # -------------------------------------------------------------

    cols = dashboard_sheet.setdefault(
        "cols",
        {}
    )

    cols["0"] = {"size": 210}  # A: product name
    cols["1"] = {"size": 85}   # B: units
    cols["2"] = {"size": 95}   # C: revenue
    cols["3"] = {"size": 130}  # D: product % of revenue

    # Category table uses the existing E:G pivot spill and H for the
    # calculated percentage column.  Keep H wide enough for the header and
    # formatted percentages.
    cols["4"] = {"size": 190}  # E: category name
    cols["5"] = {"size": 85}   # F: units
    cols["6"] = {"size": 105}  # G: revenue
    cols["7"] = {"size": 130}  # H: category % of revenue

    new_col_d_left_edge = (
        cols["0"]["size"] + cols["1"]["size"] + cols["2"]["size"]
    )
    new_col_d_right_edge = new_col_d_left_edge + cols["3"]["size"]

    # -------------------------------------------------------------
    # Position the Best Selling Categories carousel.
    #
    # The Top 10 table is rendered inside the same carousel as the
    # Treemap. Moving the carousel slightly left makes the Category,
    # Units and Revenue columns sit farther left and removes the
    # excessive empty space between the product table and category
    # table.
    #
    # Keep a small gap after column D so the two dashboard sections
    # do not overlap.
    # -------------------------------------------------------------
    CAROUSEL_TITLE_GAP = 15
    TOP10_LEFT_SHIFT = 20

    correct_carousel_abs_x = (
        new_col_d_right_edge
        + CAROUSEL_TITLE_GAP
        - TOP10_LEFT_SHIFT
    )

    for fig in dashboard_sheet.get("figures", []):
        if fig.get("tag") == "carousel":
            fig.setdefault("offset", {})
            fig["offset"]["x"] = (
                correct_carousel_abs_x - new_col_d_left_edge
            )

    # -------------------------------------------------------------
    # Keep dashboard column count unchanged
    # -------------------------------------------------------------

    if dashboard_sheet.get("colNumber", 0) < 8:
        dashboard_sheet["colNumber"] = 8

    _logger.info(
        "% of Revenue added to Best Selling Products and Best Selling Categories."
    )