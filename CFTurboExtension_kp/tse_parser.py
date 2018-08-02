from os import path


def obtain_tse_file():
    tse_file = 'Splitter Impeller optim_Co1.tse'

    return tse_file

def extract_attribs(start, end):

    tse_file = obtain_tse_file()
    attribs = {}

    with open(tse_file) as f:
        for line in f:
            if line.strip() == start:
                break

        for line in f:
            if line.strip() == end:
                break

            data = line.strip().split(' = ')
            attribs[data[0]] = data[1]

    return attribs


def extract_machine_data_attribs():
    machine_data_attribs = extract_attribs('MACHINE DATA:', 'END')

    return machine_data_attribs


def extract_hub_attribs():
    hub_attribs = extract_attribs('HUB:', 'END')

    return hub_attribs


def extract_shroud_attribs():
    shroud_attribs = extract_attribs('SHROUD:', 'END')

    return shroud_attribs


def extract_main_blade_attribs():
    main_blade_attribs = extract_attribs('BLADE:Main blade', 'END')

    return main_blade_attribs


def extract_splitter_blade_attribs():
    splitter_blade_attribs = extract_attribs('BLADE:Splitter blade', 'END')

    return splitter_blade_attribs


def make_s4():

    splitter_blade_attribs = extract_splitter_blade_attribs()
    main_blade_attribs = extract_main_blade_attribs()

    if splitter_blade_attribs == {}:
        blades_per_set = int(main_blade_attribs['Blade Number'])
        s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)
    else:
        blades_per_set = int(splitter_blade_attribs['Blade Number'])
        s4 = 'Number of Blades Per Set: {}'.format(blades_per_set + 1)

    return s4


def make_s8():

    main_blade_attribs = extract_main_blade_attribs()

    blade_0_le_type = main_blade_attribs['Leading Edge Type']
    if blade_0_le_type == 'Single':
        blade_0_le_type = 'EllipseEnd'
    else:
        blade_0_le_type = 'CutOffEnd'
    s8 = 'Blade 0 LE: {}'.format(blade_0_le_type)

    return s8


def make_s9():

    main_blade_attribs = extract_main_blade_attribs()

    blade_0_te_type = main_blade_attribs['Trailing Edge Type']
    if blade_0_te_type == 'Single':
        blade_0_te_type = 'EllipseEnd'
    else:
        blade_0_te_type = 'CutOffEnd'
    s9 = 'Blade 0 LE: {}'.format(blade_0_te_type)

    return s9


def make_s10():

    splitter_blade_attribs = extract_splitter_blade_attribs()

    if splitter_blade_attribs == {}:
        return
    else:
        blade_1_le_type = splitter_blade_attribs['Leading Edge Type']
        if blade_1_le_type == 'Single':
            blade_1_le_type = 'EllipseEnd'
        else:
            blade_1_le_type = 'CutOffEnd'
        s10 = 'Blade 1 LE: {}'.format(blade_1_le_type)

    return s10


def make_s11():

    splitter_blade_attribs = extract_splitter_blade_attribs()

    if splitter_blade_attribs == {}:
        return
    else:
        blade_1_te_type = splitter_blade_attribs['Trailing Edge Type']
        if blade_1_te_type == 'Single':
            blade_1_te_type = 'EllipseEnd'
        else:
            blade_1_te_type = 'CutOffEnd'
        s11 = 'Blade 1 TE: {}'.format(blade_1_te_type)

    return s11


def create_inf_file(inf_file):

    machine_data_attribs = extract_machine_data_attribs()
    hub_attribs = extract_hub_attribs()
    shroud_attribs = extract_shroud_attribs()
    main_blade_attribs = extract_main_blade_attribs()

    s1 = '!======  CFTurbo Export  ========'
    s2 = 'Axis of Rotation: {}'.format(machine_data_attribs['Principal Axis'])
    s3 = 'Number of Blade Sets: {}'.format(machine_data_attribs['Bladeset Count'])
    s4 = make_s4()
    s5 = 'Blade Loft Direction: Spanwise'
    geometry_units = hub_attribs['Input Length Units']
    s6 = 'Geometry Units: {}'.format(geometry_units.upper())
    s7 = 'Coordinate System Orientation: Righthanded'
    s8 = make_s8()
    s9 = make_s9()
    s10 = make_s10()
    s11 = make_s11()
    s12 = 'Hub Data File: {}'.format(path.basename(hub_attribs['Input Filename']))
    s13 = 'Shroud Data File: {}'.format(path.basename(shroud_attribs['Input Filename']))
    s14 = 'Profile Data File: {}'.format(path.basename(main_blade_attribs['Input Filename']))

    with open(inf_file, 'w') as f:
        f.write(s1 + '\n')
        f.write(s2 + '\n')
        f.write(s4 + '\n')
        f.write(s5 + '\n')
        f.write(s6 + '\n')
        f.write(s7 + '\n')
        f.write(s8 + '\n')
        f.write(s9 + '\n')

        if s10 is None:
            pass
        else:
            f.write(s10 + '\n')
            f.write(s11 + '\n')

        f.write(s12 + '\n')
        f.write(s13 + '\n')
        f.write(s14 + '\n')


create_inf_file('tets.inf')