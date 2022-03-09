## Overview

Simple tool to seed database using YAML files. Run

`devseed --help` for usage.

## Quickstart

By default, devseed attempts to find YAML files under `db/seed` directory.
You can override that with `--seed-dir`.

Assuming you have a file `vehicles.yml` in the seed directory with contents

```yaml
- id: 42
  model: AT-AT
  description: >
    All Terrain Armoured Transport.
    Tends to trip a lot over Rebel harpoon cables.
  legs: 4
- id: 41
  model: AT-ST
  description: >
    All Terrain Scout Transport. More lightweight walker,
    with very little room to spare
  legs: 2
```

and you already have table `vehicles` in your database with
appropriate schema, devseed will find the file and insert entries there.

## Contributing

Clone the repository, install `pre-commit` and ensure `pre-commit run -a` passes
before making the PR.

## TODO

- Convenient install
- Reverse, importing YAML from database dump?
- Consider supporting factory models

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![CI](https://github.com/edvardm/devseed/actions/workflows/ci.yml/badge.svg)](https://github.com/edvardm/devseed/actions/workflows/ci.yml)
