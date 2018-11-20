"""This module parses .tse file from TG and create .inf file based on attributes from .tse file.

"""

import re
from os import path
from ntpath import basename


class Geometry:
    def __init__(self, task):
        self.task = task

    def obtain_cft_file_name(self, task):
        cft_file_path = Impeller(task).get_cft_batch_path(task)
        cft_file_name = basename(cft_file_path).split('.cft')[0]
        return cft_file_name

    def obtain_tse_file(self, task):
        cft_file_name = self.obtain_cft_file_name(task)
        file_name = cft_file_name + '.tse'
        tse_file = path.join(task.ActiveDirectory, file_name)
        return tse_file

    def extract_attribs(self, task, start, end):

        tse_file = self.obtain_tse_file(task)

        attribs = {}
        with open(tse_file) as f:
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


class Attribs(Geometry):
    def __init__(self, task):
        Geometry.__init__(self, task)
        self.machine_data_attribs = Geometry(task).extract_attribs(task, 'MACHINE DATA:', 'END')
        self.hub_attribs = Geometry(task).extract_attribs(task, 'HUB:', 'END')
        self.shroud_attribs = Geometry(task).extract_attribs(task, 'SHROUD:', 'END')
        self.main_blade_attribs = Geometry(task).extract_attribs(task, 'BLADE:Main blade', 'END')
        self.splitter_blade_attribs = Geometry(task).extract_attribs(task, 'BLADE:Splitter blade', 'END')

        self.MachineData = type('MachineData', (), self.machine_data_attribs)
        self.Hub = type('Hub', (), self.hub_attribs)
        self.Shroud = type('Shroud', (), self.shroud_attribs)
        self.MainBlade = type('MainBlade', (), self.main_blade_attribs)


class FilesStrings(Geometry):
    def __init__(self, task):
        Geometry.__init__(self, task)
        self.s1 = '!======  CFTurbo Export  ========'
        self.s2 = 'Axis of Rotation: {}'.format(Attribs(task).MachineData.Principal_Axis)
        self.s3 = 'Number of Blade Sets: {}'.format(Attribs(task).MachineData.Bladeset_Count)
        self.s5 = 'Blade Loft Direction: Spanwise'
        geometry_units = Attribs(task).Hub.Input_Length_Units
        self.s6 = 'Geometry Units: {}'.format(geometry_units.upper())
        self.s7 = 'Coordinate System Orientation: Righthanded'
        self.s12 = 'Hub Data File: {}'.format(path.basename(Attribs(task).Hub.Input_Filename))
        self.s13 = 'Shroud Data File: {}'.format(path.basename(Attribs(task).Shroud.Input_Filename))
        self.s14 = 'Profile Data File: {}'.format(path.basename(Attribs(task).MainBlade.Input_Filename))

    def make_s4(self, task):
        if Attribs(task).splitter_blade_attribs == {}:
            blades_per_set = int(Attribs(task).MainBlade.Blade_Number)
            s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)
        else:
            SplitterBlade = type('SplitterBlade', (), Attribs(task).splitter_blade_attribs)
            blades_per_set = int(SplitterBlade.Blade_Number)
            s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)
        return s4

    def make_s8_s9(self, edgeType, LeTe):
        blade_type = edgeType
        if blade_type == 'Single':
            blade_type = 'EllipseEnd'
        else:
            blade_type = 'CutOffEnd'
        s8_s9 = 'Blade 0 {}: {}'.format(LeTe, blade_type)
        return s8_s9

    def make_s10(self, task):
        if Attribs(task).splitter_blade_attribs == {}:
            return
        else:
            SplitterBlade = type('SplitterBlade', (), Attribs(task).splitter_blade_attribs)
            blade_1_le_type = SplitterBlade.Leading_Edge_Type
            if blade_1_le_type == 'Single':
                blade_1_le_type = 'EllipseEnd'
            else:
                blade_1_le_type = 'CutOffEnd'
            s10 = 'Blade 1 LE: {}'.format(blade_1_le_type)
        return s10

    def make_s11(self, task):
        if Attribs(task).splitter_blade_attribs == {}:
            return
        else:
            SplitterBlade = type('SplitterBlade', (), Attribs(task).splitter_blade_attribs)
            blade_1_te_type = SplitterBlade.Trailing_Edge_Type
            if blade_1_te_type == 'Single':
                blade_1_te_type = 'EllipseEnd'
            else:
                blade_1_te_type = 'CutOffEnd'
            s11 = 'Blade 1 TE: {}'.format(blade_1_te_type)
        return s11

    def create_inf_file(self, task):
        cft_file_name = Geometry(task).obtain_cft_file_name(task)
        inf_file = cft_file_name + '.inf'
        active_dir = path.join(task.ActiveDirectory, inf_file)
        mainBlade = Attribs(task).MainBlade

        with open(active_dir, 'w') as f:
            f.write(self.s1 + '\n')
            f.write(self.s2 + '\n')
            f.write(self.s3 + '\n')
            f.write(self.make_s4(task) + '\n')
            f.write(self.s5 + '\n')
            f.write(self.s6 + '\n')
            f.write(self.s7 + '\n')
            f.write(self.make_s8_s9(mainBlade.Leading_Edge_Type, 'LE') + '\n')
            f.write(self.make_s8_s9(mainBlade.Trailing_Edge_Type, 'TE') + '\n')

            if self.make_s10(task) is None:
                pass
            else:
                f.write(self.make_s10(task) + '\n')
                f.write(self.make_s11(task) + '\n')

            f.write(self.s12 + '\n')
            f.write(self.s13 + '\n')
            f.write(self.s14 + '\n')