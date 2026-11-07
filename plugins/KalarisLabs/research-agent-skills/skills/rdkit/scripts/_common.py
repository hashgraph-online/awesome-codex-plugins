#!/usr/bin/env python3
"""Helpers shared by the RDKit command-line scripts in this directory.

Import this module only after RDKit has been confirmed importable.
"""

from pathlib import Path

from rdkit import Chem


def iter_molecules(file_path):
    """Yield (zero-based index, Mol) for each parseable molecule in an SDF/MOL/SMILES file.

    Prints the same error/warning messages the scripts always printed and yields
    nothing when the file is missing or has an unsupported suffix.
    """
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return

    if path.suffix.lower() in ['.sdf', '.mol']:
        suppl = Chem.SDMolSupplier(str(path))
    elif path.suffix.lower() in ['.smi', '.smiles', '.txt']:
        suppl = Chem.SmilesMolSupplier(str(path), titleLine=False)
    else:
        print(f"Error: Unsupported file format: {path.suffix}")
        return

    for idx, mol in enumerate(suppl):
        if mol is None:
            print(f"Warning: Failed to parse molecule {idx+1}")
            continue
        yield idx, mol
