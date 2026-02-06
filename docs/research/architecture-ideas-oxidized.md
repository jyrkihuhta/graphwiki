my-wiki/
├── pyproject.toml        # Maturin config
├── Cargo.toml            # Rust config
├── src/                  # RUST CODE
│   ├── lib.rs            # PyO3 Entry point
│   ├── parser.rs         # Fast Markdown parsing
│   └── graph.rs          # Petgraph logic
└── python_app/           # PYTHON CODE
    ├── main.py           # FastAPI app
    └── api/              # Routes
