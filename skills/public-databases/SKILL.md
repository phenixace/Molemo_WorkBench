---
name: public-databases
description: Retrieve named compounds from PubChem and protein records from UniProt using fixed official API hosts. Use for source-grounded identifiers, sequences, properties, annotations, and cross-references; do not treat database annotations as new experimental evidence.
---

# Public Databases

Use `database_lookup_pubchem` for a compound name or identifier and `database_lookup_uniprot` for a UniProt accession. Preserve the returned source URL in the answer and distinguish database fields from locally calculated descriptors.

These tools require network access but no user API key. They only contact allow-listed official PubChem and UniProt endpoints.
