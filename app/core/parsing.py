from pymatgen.io.cif import CifParser
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, module="pymatgen")
# from nglview import show_structure_file


def parse_cif(cif_file):
    """Parse a CIF file and return a pymatgen structure object."""
    parser = CifParser(cif_file)
    structure = parser.get_structures()[0]
    distinct_species = [
        str(x).replace("Element", "") for x in list(set(structure.species))
    ]
    lattice = structure.lattice
    return structure, distinct_species, lattice
