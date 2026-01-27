# Graphingwiki Features Research

Reference material for features to potentially implement in GraphWiki.

## Core MoinMoin Features

- Wiki pages with markup syntax
- Wiki links (`[[PageName]]`)
- Page versioning and history
- Access control lists (ACLs)
- Attachments
- Search
- User accounts

## Graphingwiki Additions

### Metatables

The killer feature. Allows treating wiki pages as structured data:

- Pages can have metadata key-value pairs
- Metatables query and display metadata across pages as tables
- Enables wiki-as-database patterns
- Example: Track projects, assets, contacts with wiki pages, query them with Metatables

### Graph Visualization

- Visualize links between pages
- Visualize metadata relationships
- Interactive graph exploration

### Metadata Syntax

```
<<MetaTable(CategoryProject, ||Project||Status||Owner||)>>
```

Queries all pages in CategoryProject and displays selected metadata as a table.

## Obsidian Inspiration

- Local-first, files on disk
- Fast search
- Graph view of connections
- Clean, modern UI
- Plugin ecosystem
- Backlinks panel

## MVP Features (Phase 1)

- [ ] Wiki pages in plaintext (Markdown)
- [ ] Wiki links with `[[PageName]]` syntax
- [ ] Basic page editing
- [ ] Page listing/navigation

## Future Features

- [ ] Metatables
- [ ] Graph visualization
- [ ] Version history
- [ ] Search
- [ ] User accounts and ACLs
