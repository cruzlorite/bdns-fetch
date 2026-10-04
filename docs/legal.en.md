# Legal notice

## What this project is

`bdns` is a personal, unofficial project. It has no relationship with the Intervención General de la Administración del Estado (IGAE), the body that runs the BDNS, and is not endorsed by it.

The code is distributed under the [MIT license](https://github.com/cruzlorite/bdns/blob/main/LICENSE), which excludes any warranty: you use it at your own risk, and the author is not liable for damages, data loss or misuse.

## Where the data comes from and how you may reuse it

The data comes from the [Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas](https://www.infosubvenciones.es), and reusing it is subject to the [portal's legal notice](https://www.infosubvenciones.es/bdnstrans/GE/es/avisolegal) and its [good practices for the API](https://www.infosubvenciones.es/bdnstrans/estaticos/ayuda/Buenas%20pr%C3%A1cticas%20API%20SNPSAP.pdf). In short, if you reuse it:

- cite the source (for example, "Origen de los datos: Intervención General de la Administración del Estado") and the date of the last update when the data carries it;
- do not change the meaning of the information;
- do not suggest that the IGAE takes part in, sponsors or supports your reuse;
- personal data may only be reused to scrutinise the actions of public officials, or for historical, statistical or scientific purposes, in which case you must dissociate it first and state that you did and who did it.

This summary does not replace the official text or [Law 37/2007 on the reuse of public sector information](https://www.boe.es/eli/es/l/2007/11/16/37/con), which provides for penalties. If in doubt, ask a legal adviser.

<a id="personal-data"></a>
## Personal data

Several endpoints and tables (`concesiones_busqueda`, `ayudasestado_busqueda`, `minimis_busqueda` or `terceros`, among others) hold data on natural persons: the BDNS publishes their full name and hides only part of the tax ID. `bdns-fetch` and `bdns-sync` deliver and store them exactly as the API publishes them, untransformed.

Bear in mind that `bdns-sync`'s history **keeps them even after the portal withdraws them**: awards to natural persons, for instance, are only published during the award year and the next. Whoever downloads the data or runs the target database is responsible for processing it under the GDPR and Spain's LOPDGDD (with a legitimate purpose, a retention period and access control) and the reuse conditions above.

The dataset planned for publication will always be anonymised and aggregated, precisely so that it holds no personal data ([roadmap](roadmap.md#dataset)).

## This site

This site uses no cookies or analytics, and collects no data about its visitors. Fonts are served from the site itself, so loading it makes no requests to third parties either. Your preferences, such as light or dark mode, are kept only in your browser.

The site is hosted on GitHub Pages, and GitHub, like any hosting provider, logs technical access data such as IP addresses for security. Its [privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement) explains it.

## Contact

For questions or problems, open an [issue on GitHub](https://github.com/cruzlorite/bdns/issues). For a vulnerability, follow the [security policy](https://github.com/cruzlorite/bdns/blob/main/SECURITY.md).
