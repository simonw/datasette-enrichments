from datasette import Response, NotFound
from datasette.utils import path_with_added_args, MultiParams
import urllib.parse


async def enrichment_view(datasette, request):
    from . import get_enrichments

    database = request.url_vars["database"]
    table = request.url_vars["table"]
    slug = request.url_vars["enrichment"]

    enrichments = await get_enrichments(datasette)
    enrichment = enrichments.get(slug)
    if enrichment is None:
        raise NotFound("Enrichment not found")

    query_string = request.query_string
    # Parse query string
    bits = urllib.parse.parse_qsl(query_string)
    # Remove _sort
    bits = [bit for bit in bits if bit[0] != "_sort"]
    # Add extras
    bits.extend(
        [("_extra", "human_description_en"), ("_extra", "count"), ("_extra", "columns")]
    )
    # re-encode
    query_string = urllib.parse.urlencode(bits)
    stuff = (
        await datasette.client.get(
            datasette.urls.table(database, table, "json") + "?" + query_string
        )
    ).json()

    # If an enrichment is selected, use that UI

    if request.method == "POST":
        return await enrich_data_post(datasette, request, enrichment, stuff)

    form = (await enrichment.get_config_form(datasette.get_database(database), table))()

    return Response.html(
        await datasette.render_template(
            ["enrichment-{}.html".format(enrichment.slug), "enrichment.html"],
            {
                "database": database,
                "table": table,
                "stuff": stuff,
                "enrichment": enrichment,
                "enrichment_form": form,
            },
            request,
        )
    )


async def enrichment_picker(datasette, request):
    from . import get_enrichments

    database = request.url_vars["database"]
    table = request.url_vars["table"]

    enrichments = await get_enrichments(datasette)

    query_string = request.query_string
    # Parse query string
    bits = urllib.parse.parse_qsl(query_string)
    # Remove _sort
    bits = [bit for bit in bits if bit[0] != "_sort"]
    # Add extras
    bits.extend(
        [("_extra", "human_description_en"), ("_extra", "count"), ("_extra", "columns")]
    )
    # re-encode
    query_string = urllib.parse.urlencode(bits)
    stuff = (
        await datasette.client.get(
            datasette.urls.table(database, table, "json") + "?" + query_string
        )
    ).json()

    enrichments_and_paths = []
    for enrichment in enrichments.values():
        enrichments_and_paths.append(
            {
                "enrichment": enrichment,
                "path": path_with_added_args(
                    request=request,
                    args={"_enrichment": enrichment.slug, "_sort": None},
                    path="{}/{}".format(request.path, enrichment.slug),
                ),
            }
        )

    return Response.html(
        await datasette.render_template(
            "enrichment_picker.html",
            {
                "database": database,
                "table": table,
                "stuff": stuff,
                "enrichments_and_paths": enrichments_and_paths,
            },
            request,
        )
    )


COLUMN_PREFIX = "column."


async def enrich_data_post(datasette, request, enrichment, stuff):
    db = datasette.get_database(request.url_vars["database"])
    table = request.url_vars["table"]

    # Initialize any necessary tables
    await enrichment.initialize(db, table, {})

    # Enqueue the enrichment to be run
    filters = []
    for key in request.args:
        if key not in ("_enrichment", "_sort"):
            for value in request.args.getlist(key):
                filters.append((key, value))
    filter_querystring = urllib.parse.urlencode(filters)

    # Roll our own form parsing because .post_vars() eliminates duplicate names
    body = await request.post_body()
    post_vars = MultiParams(urllib.parse.parse_qs(body.decode("utf-8")))

    Form = await enrichment.get_config_form(db, table)

    form = Form(post_vars)
    if not form.validate():
        return Response.html(
            await datasette.render_template(
                "enrich_data.html",
                {
                    "database": db.name,
                    "table": table,
                    "stuff": stuff,
                    "enrichments": [
                        dict(
                            enrichment,
                            path=path_with_added_args(
                                request, {"_enrichment": enrichment.slug}
                            ),
                        )
                        for enrichment in enrichments.values()
                    ],
                    "enrichment": enrichment,
                    "enrichment_form": form,
                },
                request,
            )
        )

    copy = post_vars._data.copy()
    copy.pop("csrftoken", None)

    await enrichment.enqueue(
        datasette,
        db,
        table,
        filter_querystring,
        copy,
        request.actor.get("id") if request.actor else None,
    )

    # Set message and redirect to table
    datasette.add_message(
        request,
        "Enrichment started: {} for {} row{}".format(
            enrichment.name, stuff["count"], "s" if stuff["count"] != 1 else ""
        ),
        datasette.INFO,
    )
    return Response.redirect(datasette.urls.table(db.name, table))
