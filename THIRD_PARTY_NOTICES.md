# Third-Party Notices

Korean Vocab Extractor is licensed under the MIT License except for third-party
components and data identified below. Those materials remain under their
respective licenses and are not relicensed by the project's MIT License.

## Kengdic bundled dictionary data

`backend/dictionary/bundled_dict.json` is derived from Kengdic, the
Korean/English dictionary database created by Joe Speigle and maintained at:

https://github.com/garfieldnate/kengdic

Kengdic states that its data is dual-licensed: users may choose the Mozilla
Public License 2.0 (MPL-2.0) or the GNU Lesser General Public License version
2.0 or later (LGPL-2.0+).

This project distributes its Kengdic-derived bundled dictionary under the
MPL-2.0 option. The corresponding source-form data is the committed
`backend/dictionary/bundled_dict.json`; it can be regenerated from upstream
Kengdic data with `scripts/build_bundled_dict.py`.

The MPL-2.0 text is included at `LICENSES/MPL-2.0.txt`.

## kiwipiepy / Kiwi / kiwipiepy_model

Packaged builds include `kiwipiepy`, the Kiwi Korean morphological analyzer,
and `kiwipiepy_model`. Upstream licenses these under the Apache License 2.0
and provides a NOTICE covering Kiwi model-data attribution and bundled
third-party components.

Upstream project:

https://github.com/bab2min/kiwipiepy

The Apache-2.0 license text is included at `LICENSES/Apache-2.0.txt`.
The upstream attribution notice is included at
`LICENSES/kiwipiepy-NOTICE.txt`.

## Other dependencies

Python and JavaScript dependencies listed in `backend/requirements.txt` and
`frontend/package.json` remain under their own upstream licenses. Installing
or redistributing those dependencies does not relicense them under this
project's MIT License.
