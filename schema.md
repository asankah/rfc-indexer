# IRIs

## Nodes

* `rfc:doc/<number>` : A specific RFC `<number>`. E.g. RFC 3987 is
    `rfc:doc/3987`.

* `rfc:doc/<number>/<section ID>` : A section in an RFC. E.g. RFC 3987 section
    2.2 is `rfc:doc/3987/2.2`.

* `rfc:category/<category>` : An RFC category. E.g. category "Standards Track"
    is `rfc:category/standards-track`. Lowercase with spaces translated to `-`.

* `rfc:rulename/<name>` : A ABNF rulename. E.g. `rfc:rulename/ihost`.

* `rfc:rule/<number>/<rulename>` : Production for `rulename` in document `number`.
    Each document is expected to only have one definition per rulename.

## Predicates

* `rfc:text-is` : The contents of the thing. From a `rule` to an `xsd:string`.

* `rfc:definition-is` : From a `rulename` to a `rule`.

* `rfc:defined-in` : From a `rule` to a `section` or a `doc`.

* `rfc:contained-in` : From a `section` to a `doc`.

* `rfc:updates` : From a `doc` to an older `doc`.

* `rfc:updated-by` : From an old `doc` to a newser `doc`.

* `rfc:obsoletes` : From a `doc` to an older `doc`.

* `rfc:obsoleted-by` : from an old `doc` to a `doc`.

* `rfc:normative-reference` : from a `doc` to another `doc`.

* `rfc:informative-reference` : From a `doc` to another `doc`.

* `rfc:references` : From a `doc` or a `section` to another `doc`.

* `rfc:referenced-by` : From a `doc` to a `section` or another `doc`.

