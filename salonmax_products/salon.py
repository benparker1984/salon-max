from __future__ import annotations

from datetime import datetime


def sunbed_rows(
    *,
    ensure_sunbed_tables,
    query_all,
    default_sunbed_label,
    custom_sunbed_name_from_row,
    default_catalogue_image_path,
):
    ensure_sunbed_tables()
    rows = query_all(
        """
        select
            sunbeds.*,
            sites.name as site_name,
            coalesce(sites.is_active, 0) as site_is_active
        from sunbeds
        left join sites on sites.id = sunbeds.site_id
        order by
            case when coalesce(sites.is_active, 0) = 1 then 0 else 1 end,
            sunbeds.room_number,
            case when sunbeds.is_active = 1 then 0 else 1 end,
            sunbeds.updated_at desc,
            sunbeds.id desc
        """
    )
    prepared = []
    seen_beds = set()
    for row in rows:
        row_dict = dict(row)
        bed_number = int(row["room_number"] or 1)
        if bed_number in seen_beds:
            continue
        seen_beds.add(bed_number)
        row_dict["bed_number"] = bed_number
        row_dict["default_label"] = default_sunbed_label(bed_number)
        row_dict["custom_name"] = custom_sunbed_name_from_row(row)
        row_dict["default_catalogue_image_path"] = default_catalogue_image_path(
            row["default_catalogue_image_file"]
        )
        prepared.append(row_dict)
    return prepared


def business_settings_row(*, ensure_business_settings_table, query_one):
    ensure_business_settings_table()
    row = query_one("select * from business_settings where id = 1")
    merged = dict(row)
    merged["business_name"] = row["business_name"] or "Your Salon"
    merged["platform_brand_name"] = "Salon Max"
    return merged


def best_seller_rows(*, query_all, start_text, end_text):
    return query_all(
        """
        select
            description,
            count(*) as sale_count,
            coalesce(sum(quantity), 0) as units_sold,
            coalesce(sum(line_total), 0) as sales_total
        from transaction_lines
        left join transactions on transactions.id = transaction_lines.transaction_id
        where transactions.status = 'completed'
          and datetime(transactions.created_at) >= datetime(?)
          and datetime(transactions.created_at) <= datetime(?)
        group by description
        order by sales_total desc, units_sold desc, sale_count desc
        limit 10
        """,
        (start_text, end_text),
    )


def parse_date_or_default(value: str, fallback_date):
    text = (value or "").strip()
    if not text:
        return fallback_date
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return fallback_date


def transactions_for_day(*, query_all, day_value):
    start_text = f"{day_value.isoformat()} 00:00:00"
    end_text = f"{day_value.isoformat()} 23:59:59"
    return query_all(
        """
        select
            transactions.*,
            customers.first_name,
            customers.last_name,
            sites.name as site_name,
            staff_users.name as staff_name
        from transactions
        left join customers on customers.id = transactions.customer_id
        left join sites on sites.id = transactions.site_id
        left join staff_users on staff_users.id = transactions.staff_user_id
        where datetime(transactions.created_at) >= datetime(?)
          and datetime(transactions.created_at) <= datetime(?)
        order by transactions.id desc
        """,
        (start_text, end_text),
    )
