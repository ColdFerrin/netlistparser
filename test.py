from kiutils.schematic import Schematic


def main():
    schematic = Schematic().from_file('test_projecty.kicad_sch')

    print(schematic)


if __name__ == '__main__':
    main()
