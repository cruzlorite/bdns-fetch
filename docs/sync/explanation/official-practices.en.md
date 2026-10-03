# Official good practices

The design follows the official ["Buenas prácticas API SNPSAP"](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf) document:

- **10 requests per second per IP limit**, which `bdns-fetch` respects by spacing requests at 9.5 per second, with no bursts.
- **Maximum page size** (10,000 records per call), and always **all pages**, which is what `bdns-fetch` does by default. A response cut to a single page goes unnoticed (caught live: `grandesbeneficiarios_busqueda` once returned 10,000 of 142,260 rows), which is why `bdns-fetch` warns when it leaves pages out.
- **Daily/weekly/monthly/annual cadence by registration date**, as the document recommends.
- **The `terceros` endpoint is not used**: the document itself flags it as redundant.
- **Reconciliation to detect removals**: grants are withdrawn from the BDNS 4 calendar years after being awarded. Full-catalog syncs detect removals by comparing against the entire current state; for the large incremental endpoints, where that comparison is not viable, a registration-date-scoped comparison is used instead (see [window-scoped deletion detection](sync-behavior.md#windowed-deletions)).
