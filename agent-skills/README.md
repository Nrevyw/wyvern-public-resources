# Agent Skills

Portable [skills](https://code.claude.com/docs/en/skills) that teach AI coding agents
how to work with Wyvern hyperspectral data. A skill is a folder with a `SKILL.md`
(instructions + when to use them) plus optional reference files and scripts — the
agent loads it on demand and immediately "knows" Wyvern's data formats, catalog
structure, band configurations, and common pitfalls.

## Available skills

| Skill | What it covers |
| --- | --- |
| [`working-with-wyvern-data`](working-with-wyvern-data/) | STAC discovery of Open Data scenes, correct uint16→reflectance scaling & NoData masking, wavelength→band resolution for both VNIR configurations, spectral indices, and spectral analysis (ACE/MTMF detection, RX anomaly detection, spectral libraries) |

## Installation

**Claude Code** — copy the skill folder into your project or user skills directory:

```bash
# project-level (shared with your team via the repo)
cp -r working-with-wyvern-data /path/to/your/project/.claude/skills/

# or user-level (available in all your sessions)
cp -r working-with-wyvern-data ~/.claude/skills/
```

**Other agent frameworks** — `SKILL.md` is plain markdown with YAML frontmatter; use
it as a system-prompt addition or context file. The bundled
`scripts/wyvern_stac.py` is standard-library Python and runs anywhere.

## Contributing

Improvements and new skills are welcome — see [CONTRIBUTING.md](../CONTRIBUTING.md).
Please keep skills concise (the agent's context window is shared), verify code
against live Open Data scenes, and prefer per-scene STAC metadata over hardcoded
constants.
