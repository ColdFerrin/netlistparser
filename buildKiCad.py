from netlist import *
import os
from kiutils.schematic import Schematic
from kiutils.libraries import LibTable
from kiutils.symbol import SymbolLib, Symbol
from kiutils.items.schitems import SchematicSymbol
from kiutils.items.common import Position
import re
import math
import uuid


MM_MIN_DIST = 1.27
DIST_TO_SKIP = 150.0 * MM_MIN_DIST

parts_in_schematic = {}

def find_component_in_lib(entry_name: str, library_contents, library_name) -> Symbol:
    active_lib_symbols = library_contents[library_name].symbols

    active_lib_symbols_by_entry_name = {}

    for active_lib_symbol in active_lib_symbols:

        active_lib_symbols_by_entry_name[active_lib_symbol.entryName] = active_lib_symbol

    return active_lib_symbols_by_entry_name[entry_name]


def create_pins(component_value, library_contents) -> list[Symbol]:

    MAX_PINS = 60

    num_pins = 0

    if component_value.designator.startswith('J') and 'CONN' in component_value.package:
        num_pins = int(re.search(r'\d+', component_value.package).group())
    else:
        pass

    num_connectors = math.ceil(num_pins / MAX_PINS)
    last_connector = num_pins % MAX_PINS

    conn_name_pattern = 'Conn_01x{num}'
    connector_lib_name = 'Connector_Generic'

    symbols = []

    for i in range(num_connectors):
        if i < num_connectors - 1:
            symbols.append(find_component_in_lib(conn_name_pattern.replace('{num}', '60'), library_contents, connector_lib_name))
        else:
            symbols.append(find_component_in_lib(conn_name_pattern.replace('{num}', str(last_connector)), library_contents, connector_lib_name))

    return symbols


def find_components(component_value, library_contents) -> list[Symbol]:

    if component_value.name.startswith('U'):
        return []

    return create_pins(component_value, library_contents)


def find_max_sub_unit(component) -> int :

    max_unit : int = 0

    for unit in component.units:
        if unit.styleId > max_unit:
            max_unit = unit.styleId

    return max_unit


def find_max_pin_num(component) -> int:

    max_pin_num = 0

    for unit in component.units:
        for pin in unit.pins:
            if int(pin.number) > max_pin_num:
                max_pin_num = int(pin.number)

    return max_pin_num


def add_to_schematic(schematic, components, x_pos, y_pos):

    start_x = x_pos
    start_y = y_pos

    for component in components:

        unit_id = component.unit_id

        if unit_id not in parts_in_schematic.keys():
            parts_in_schematic[component.unitId] = component
            schematic.libSymbols.append(component)

        max_subunit = find_max_sub_unit(component)

        max_pin_number = find_max_pin_num(component)

        for unit_number in range(component.units.count() % (max_subunit + 1)):

            schematic_symbol = SchematicSymbol()
            schematic_symbol.unit_id = unit_id
            schematic_symbol.position.x = start_x
            schematic_symbol.position.y = start_y
            schematic_symbol.position.angle = 0.0
            schematic_symbol.unit = unit_number
            schematic_symbol.inBom = True
            schematic_symbol.onBoard = True
            schematic_symbol.uuid = uuid.uuid4()

            for pin_num in range(1, max_pin_number+1):
                schematic_symbol.pins[str(pin_num)] = str(uuid.uuid4())

            start_y = start_y + DIST_TO_SKIP

            schematic.schematicSymbols.append(schematic_symbol)

        start_y += DIST_TO_SKIP


def place_component(x_pos: float, y_pos: float, component_key: str, component_value: Component, library_contents: dict[str, SymbolLib], schematic: Schematic):

    components = find_components(component_value, library_contents)

    add_to_schematic(schematic, components, x_pos, y_pos)

    pass


def build_ki_cad(design: Design) -> Schematic:
    schematic = Schematic()

    schematic.uuid = str(uuid.uuid4())

    app_data = os.getenv('APPDATA')

    libraies = LibTable().from_file(app_data + '\\kicad\\8.0\\sym-lib-table')

    library_contents = {}

    libs_to_skip = ['Converter_DCDC', 'RF']

    lib_location_key = '${KICAD8_SYMBOL_DIR}/'
    default_lib_location = 'C:\\Program Files\\KiCad\\8.0\\share\\kicad\\symbols\\'

    for lib in libraies.libs:
        lib.uri = lib.uri.replace(lib_location_key, default_lib_location)

        if lib.name in libs_to_skip:
            continue

        library_contents[lib.name] = SymbolLib.from_file(lib.uri)

    print(libraies)
    print(schematic)

    x_pos = 10 * MM_MIN_DIST
    y_pos = 10 * MM_MIN_DIST

    for component_key, component_value in design.Components.items():
        place_component(x_pos, y_pos, component_key, component_value, library_contents, schematic)

        x_pos += DIST_TO_SKIP

    return schematic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fileName')
    args = parser.parse_args()

    d = Design()
    d.ReadCadTemp(args.fileName)

    build_ki_cad(d)


if __name__ == '__main__':
    main()
