# Index Library
This directory contains files relevant to Wyvern's Hyperspectral Index Library. Currently, the extent of this library
is a single `json` file containing all of our indices. This may grow in the future

## Why Another Index Library?
It can be difficult to sift through the endless list of hyperspectral and multispectral indices to find ones that
are relevant/have matching bands to our satellites. We want folks who are interested in using our data to be able
to instantly find relevant indices to apply to our hyperspectral images.

Having our own index library simplifies this, and allows us to continually expand and update the library as more
resources, papers, and indices come out.

## How do I use this?
Right now, this file will be used as the input data for our Knowledge Centre. Please go to
[knowledge.wyvern.space/hyperspectral_library](https://knowledge.wyvern.space/hyperspectral_library) to access
and search these indices. (Note we are in the process of releasing a new version of the Knowledge Centre. This
page currently does not exist)

## How to Contribute
We welcome all contributions from the community! Feel free to create a PR, adding your indices to the
`wyvern_index_library.json`, with some additional information within the PR:
- Relevant bands. Please use [our product guide](https://guide.wyvern.space/data-product-guide/product-specifications/spectral-bands)
for more information on our bands
- Relevant papers and resources to include with the index. (We will only include indices that have relevant
scientific papers attached to them)

### JSON Schema
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "$defs": {
        "hsiBand": {
            "description": "Represents a single HSI band including band parameters (FWHM, etc). Used to link back to equations.",
            "type": "object",
            "properties": {
                "band_index": {
                    "description": "Index of band in geotiff/file. Starts from 1",
                    "type": "integer"
                },
                "cwl_nm": {
                    "description": "Centre wavelength of band in nanometres",
                    "type": "integer"
                },
                "fwhm_nm": {
                    "description": "Full-width-half-max (FWHM) of band. I.e. bandwidth.",
                    "type": "number"
                },
                "approximate_match": {
                    "description": "If true, it only matches the required band in the equation approximately (i.e. over 5nm away from band).",
                    "type": "boolean"
                }
            }
        }
    },
    "title": "Wyvern Index Library Item",
    "description": "An item in the Wyvern hyperspectral index library",
    "type": "object",
    "properties": {
        "name": {
            "description": "Name of the hyperspectral index",
            "type": "string"
        },
        "description": {
            "description": "Rich text description of the hyperspectral index, including relevant caveats/notes. Add as much colour as possible here!",
            "type": "string"
        },
        "categories": {
            "description": "Array of categories. These should be high level like: vegetation, water, geology, etc.",
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "uniqueItems": true
        },
        "keywords": {
            "description": "Array of keywords. These should be focused like: chlorophyll, stress, iron, broadband, normalized difference, etc",
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "uniqueItems": true
        },
        "equation": {
            "description": "Simple text equation for the HSI index",
            "type": "string"
        },
        "latex_equation": {
            "description": "LaTEX/KaTEX compatible equation for rich rendering",
            "type": "string"
        },
        "band_mappings": {
            "description": "Band mapping objects for each compatible satellite",
            "type": "object",
            "properties": {
                "Dragonette-001": {
                    "description": "Band mapping for Dragonette-001",
                    "type": "object",
                    "propertyNames": {
                        "pattern": ".*"
                    },
                    "additionalProperties": {
                        "$ref": "#/$defs/hsiBand"
                    }
                },
                "Dragonette-2/3/4": {
                    "description": "Band mapping for Dragonette-002/3/4/+. These satellites have the same band set.",
                    "type": "object",
                    "propertyNames": {
                        "pattern": ".*"
                    },
                    "additionalProperties": {
                        "$ref": "#/$defs/hsiBand"
                    }
                }
            }
        },
        "compatible_satellites": {
            "description": "Array of compatible satellites.",
            "type": "array",
            "items": {
                "type": "string"
            },
            "minItems": 1,
            "uniqueItems": true
        },
        "approximate_match": {
            "description": "Boolean, True if one or more bands in the index are off by over 5nm",
            "type": "boolean"
        },
        "citations": {
            "description": "An array of matching citations/links to resources",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "paper": {
                        "description": "Name of publication or link",
                        "type": "string"
                    },
                    "authors": {
                        "description": "Authors of the paper and/or publication",
                        "type": ["string", "null"]
                    },
                    "doi": {
                        "description": "DOI (Digital Object Identifier) used to generate URLs back to the paper",
                        "type": ["string", "null"]
                    },
                    "link": {
                        "description": "URL for a link. Will render seperately from the DOI",
                        "type": ["string", "null"]
                    }
                }
            }
        }
    },
    "required": [
        "name",
        "description",
        "categories",
        "keywords",
        "equation",
        "latex_equation",
        "band_mappings",
        "compatible_satellites",
        "approximate_match",
        "citations"
    ]
}
```