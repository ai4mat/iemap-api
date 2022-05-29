from pymatgen.io.cif import CifParser
from pymatgen.io.pwscf import PWInput, PWOutput
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, module="pymatgen")
# from nglview import show_structure_file


def parse_cif(cif_file):
    """Parse a CIF file and return a pymatgen structure object."""
    parser = CifParser(cif_file)
    structure = parser.get_structures()[0]
    # distinct_species = [
    #     str(x).replace("Element", "") for x in list(set(structure.species))
    # ]
    lattice = structure.lattice
    elements = structure.symbol_set
    # composition = structure.composition
    formula = structure.formula
    return formula, elements, lattice


if __name__ == "__main__":

    import os

    cif_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../../example.cif"
    )
    cif_data = parse_cif(cif_file)
    print(cif_data)

# import os

# fp_out = os.path.join(
#     os.path.dirname(os.path.realpath(__file__)), "../../uploaded/aiida.out"
# )

# fp_in = os.path.join(
#     os.path.dirname(os.path.realpath(__file__)), "../../uploaded/aiida.in"
# )
# with open(fp_in) as f:
#     contents = f.read()
# try:
#     aiida_out = PWOutput(fp_out)
#     print(aiida_out)
#     aiida_in = PWInput.from_file(fp_in)
# except Exception as e:
#     print(e)
#     print("Error parsing PWSCF input file.")
