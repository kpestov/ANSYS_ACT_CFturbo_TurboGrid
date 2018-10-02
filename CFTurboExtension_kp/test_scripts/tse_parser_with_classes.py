from pprint import pprint
import re
from os import path

FILE = 'test-impeller.tse'
# FILE = 'test-impeller.tse'

class Geometry:

    def extract_attribs(self, FILE, start, end):
        attribs = {}
        with open(FILE) as f:
            for line in f:
                if line.strip() == start:
                    break

            for line in f:
                if line.strip() == end:
                    break

                data = line.strip().split(' = ')
                new_keys = re.sub(' ', '_', data[0])
                attribs[new_keys] = data[1]

        return attribs


machine_data = Geometry()
hub = Geometry()
shroud = Geometry()
main_blade = Geometry()
splitter_blade = Geometry()

machine_data_attribs = machine_data.extract_attribs(FILE, 'MACHINE DATA:', 'END')
hub_attribs = hub.extract_attribs(FILE, 'HUB:', 'END')
shroud_attribs = shroud.extract_attribs(FILE, 'SHROUD:', 'END')
main_blade_attribs = main_blade.extract_attribs(FILE, 'BLADE:Main blade', 'END')
splitter_blade_attribs = splitter_blade.extract_attribs(FILE, 'BLADE:Splitter blade', 'END')

MachineData = type('MachineData', (), machine_data_attribs)
Hub = type('Hub', (), hub_attribs)
Shroud = type('Shroud', (), shroud_attribs)
MainBlade = type('MainBlade', (), main_blade_attribs)


class FilesStrings():

    s1 = '!======  CFTurbo Export  ========'
    s2 = 'Axis of Rotation: {}'.format(MachineData.Principal_Axis)
    s3 = 'Number of Blade Sets: {}'.format(MachineData.Bladeset_Count)
    s5 = 'Blade Loft Direction: Spanwise'
    geometry_units = Hub.Input_Length_Units
    s6 = 'Geometry Units: {}'.format(geometry_units.upper())
    s7 = 'Coordinate System Orientation: Righthanded'
    s12 = 'Hub Data File: {}'.format(path.basename(Hub.Input_Filename))
    s13 = 'Shroud Data File: {}'.format(path.basename(Shroud.Input_Filename))
    s14 = 'Profile Data File: {}'.format(path.basename(MainBlade.Input_Filename))

    def make_s4(self):

        if splitter_blade_attribs == {}:
            blades_per_set = int(MainBlade.Blade_Number)
            s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)
        else:
            SplitterBlade = type('SplitterBlade', (), splitter_blade_attribs)
            blades_per_set = int(SplitterBlade.Blade_Number)
            s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)

        return s4


    def make_s8(self):

        blade_0_le_type = MainBlade.Leading_Edge_Type
        if blade_0_le_type == 'Single':
            blade_0_le_type = 'EllipseEnd'
        else:
            blade_0_le_type = 'CutOffEnd'
        s8 = 'Blade 0 LE: {}'.format(blade_0_le_type)

        return s8


    def make_s9(self):

        blade_0_te_type = MainBlade.Trailing_Edge_Type
        if blade_0_te_type == 'Single':
            blade_0_te_type = 'EllipseEnd'
        else:
            blade_0_te_type = 'CutOffEnd'
        s9 = 'Blade 0 LE: {}'.format(blade_0_te_type)

        return s9


    def make_s10(self):
        if splitter_blade_attribs == {}:
            return
        else:
            SplitterBlade = type('SplitterBlade', (), splitter_blade_attribs)
            blade_1_le_type = SplitterBlade.Leading_Edge_Type
            if blade_1_le_type == 'Single':
                blade_1_le_type = 'EllipseEnd'
            else:
                blade_1_le_type = 'CutOffEnd'
            s10 = 'Blade 1 LE: {}'.format(blade_1_le_type)

        return s10


    def make_s11(self):
        if splitter_blade_attribs == {}:
            return
        else:
            SplitterBlade = type('SplitterBlade', (), splitter_blade_attribs)
            blade_1_te_type = SplitterBlade.Trailing_Edge_Type
            if blade_1_te_type == 'Single':
                blade_1_te_type = 'EllipseEnd'
            else:
                blade_1_te_type = 'CutOffEnd'
            s11 = 'Blade 1 TE: {}'.format(blade_1_te_type)

        return s11


def write_inf_file():

    s4 = FilesStrings()
    s8 = FilesStrings()
    s9 = FilesStrings()
    s10 = FilesStrings()
    s11 = FilesStrings()

    with open('test.inf', 'w') as f:
        f.write(FilesStrings.s1 + '\n')
        f.write(FilesStrings.s2 + '\n')
        f.write(FilesStrings.s3 + '\n')
        f.write(s4.make_s4() + '\n')
        f.write(FilesStrings.s5 + '\n')
        f.write(FilesStrings.s6 + '\n')
        f.write(FilesStrings.s7 + '\n')
        f.write(s8.make_s8() + '\n')
        f.write(s9.make_s9() + '\n')

        if s10.make_s10() is None:
            pass
        else:
            f.write(s10.make_s10() + '\n')
            f.write(s11.make_s11() + '\n')

        f.write(FilesStrings.s12 + '\n')
        f.write(FilesStrings.s13 + '\n')
        f.write(FilesStrings.s14 + '\n')


write_inf_file()













