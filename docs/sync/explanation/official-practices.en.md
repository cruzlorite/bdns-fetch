# Official good practices

The design follows the official ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) document:

- **10 requests per second per IP limit**, enforced by `bdns-fetch`.
- **Maximum page size** (10,000 records per call), and always **all pages**: bdns-fetch's `num_pages` parameter defaults to 1, silently truncating any response larger than one page (caught live: `grandesbeneficiarios_busqueda` returned 10,000 of 142,260 rows). The `generic.all_pages` wrapper forces `num_pages=0` on every paginated method, detected by signature.
- **Daily/weekly/monthly/annual cadence by registration date**, as the document recommends.
- **The `terceros` endpoint is not used**: the document itself flags it as redundant.
- **Reconciliation to detect removals**: grants are withdrawn from the BDNS 4 calendar years after being awarded. Full-catalog syncs detect removals by comparing against the entire current state; for the large incremental endpoints, where that comparison is not viable, a registration-date-scoped comparison is used instead (see [window-scoped deletion detection](bdns-api-behavior.md#windowed-deletions)).
