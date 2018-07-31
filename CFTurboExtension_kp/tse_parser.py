from pprint import pprint


def make_list_from_file():
    raw_list = []
    with open('Splitter Impeller optim_Co1.tse', 'r') as f:

        for line in f:
            raw_list.append(line.strip())

    return raw_list


def make_machine_data_dict(raw_list):
    machine_data_dict = {}
    machine_data_internal_dict = {}

    for i in range(2, 7):
        data = raw_list[i].split(' = ')
        machine_data_internal_dict[data[0]] = data[1]

    machine_data_dict['MACHINE DATA'] = machine_data_internal_dict

    return machine_data_dict


def make_hub_dict(raw_list):
    hub_dict = {}
    hub_internal_dict = {}

    for i in range(9, 13):
        data = raw_list[i].split(' = ')
        hub_internal_dict[data[0]] = data[1]

    hub_dict['HUB'] = hub_internal_dict

    return hub_dict


def make_shroud_dict(raw_list):
    shroud_dict = {}
    shroud_internal_dict = {}

    for i in range(16, 20):
        data = raw_list[i].split(' = ')
        shroud_internal_dict[data[0]] = data[1]

    shroud_dict['SHROUD'] = shroud_internal_dict

    return shroud_dict


def make_genaral_list(machine_data_dict, hub_dict, shroud_dict):
    general_list = []
    general_list.append(machine_data_dict)
    general_list.append(hub_dict)
    general_list.append(shroud_dict)

    return general_list


def make_main_blade_dict(raw_list):

    main_blade_dict = {}
    main_blade_internal_dict = {}

    main_blade_dict_name = raw_list[23].split(':')[1]

    for i in range(24, 36):
        data = raw_list[i].split(' = ')
        main_blade_internal_dict[data[0]] = data[1]
        main_blade_dict[main_blade_dict_name] =  main_blade_internal_dict

    return main_blade_dict


def make_splitter_1_dict(raw_list):

    if raw_list[37] == 'BLADE:Splitter blade':

        splitter_1_blade_dict = {}
        splitter_1_blade_internal_dict = {}

        splitter_1_blade_dict_name = raw_list[37].split(':')[1]

        for i in range(38, 50):
            data_1 = raw_list[i].split(' = ')
            splitter_1_blade_internal_dict[data_1[0]] = data_1[1]
            splitter_1_blade_dict[splitter_1_blade_dict_name] = splitter_1_blade_internal_dict

        return splitter_1_blade_dict


def make_splitter_2_dict(raw_list):

    if raw_list[51] == 'BLADE:Splitter blade':

        splitter_2_blade_dict = {}
        splitter_2_blade_internal_dict = {}

        splitter_2_blade_dict_name = raw_list[51].split(':')[1]

        for i in range(52, 64):
            data_2 = raw_list[i].split(' = ')
            splitter_2_blade_internal_dict[data_2[0]] = data_2[1]
            splitter_2_blade_dict[splitter_2_blade_dict_name] = splitter_2_blade_internal_dict

        return splitter_2_blade_dict


def make_blade_list(make_main_blade_dict, make_splitter_1_dict, make_splitter_2_dict):
    blade_list = []
    blade_list.append(make_main_blade_dict)

    if make_splitter_1_dict == None:
        pass
    else:
        blade_list.append(make_splitter_1_dict)

    if make_splitter_2_dict == None:
        pass
    else:
        blade_list.append(make_splitter_2_dict)

    return blade_list


def create_inf_file():
    with open('test.inf', 'w') as f:

        s_1 = '!======  CFTurbo Export  ========'
        s_2 = 'Axis of Rotation: {}'.format(general_list[0]['MACHINE DATA']['Principal Axis'])
        s_3 = 'Number of Blade Sets: {}'.format(general_list[0]['MACHINE DATA']['Bladeset Count'])
        s_4 = 'Number of Blades Per Set: {}'.format(len(blade_list))
        s_5 = 'Blade Loft Direction: Spanwise'
        s_6 = 'Geometry Units: {}'.format(general_list[1]['HUB']['Input Length Units'])
        s_7 = 'Coordinate System Orientation: Righthanded'

        blade_0_le_type = blade_list[0]['Main blade']['Leading Edge Type']
        if blade_0_le_type == 'Single':
            blade_0_le_type = 'EllipseEnd'
        else:
            blade_0_le_type = 'CutOffEnd'
        s_8 = 'Blade 0 LE: {}'.format(blade_0_le_type)

        blade_0_te_type = blade_list[0]['Main blade']['Leading Edge Type']
        if blade_0_te_type == 'Single':
            blade_0_te_type = 'EllipseEnd'
        else:
            blade_0_te_type = 'CutOffEnd'
        s_9 = 'Blade 0 LE: {}'.format(blade_0_te_type)

        # s_9
        # s_10
        # s_11
        # s_12
        # s_13
        # s_14
        # s_15

        f.write(s_1 + '\n')
        f.write(s_2 + '\n')
        f.write(s_3 + '\n')
        f.write(s_4 + '\n')
        f.write(s_5 + '\n')
        f.write(s_6.upper() + '\n')
        f.write(s_7 + '\n')
        f.write(s_8 + '\n')
        f.write(s_9 + '\n')


raw_list = make_list_from_file()
machine_data_dict = make_machine_data_dict(raw_list)
hub_dict = make_hub_dict(raw_list)
shroud_dict = make_shroud_dict(raw_list)
general_list = make_genaral_list(machine_data_dict, hub_dict, shroud_dict)

main_blade_dict = make_main_blade_dict(raw_list)
splitter_1_dict = make_splitter_1_dict(raw_list)
splitter_2_dict = make_splitter_2_dict(raw_list)



blade_list = make_blade_list(main_blade_dict, splitter_1_dict, splitter_2_dict)
pprint(blade_list)
print(len(blade_list))

# print(splitter_2_dict)


create_inf_file()


# pprint(raw_list)


# pprint(general_list)

# print(general_list[0]['MACHINE DATA']['Bladeset Count'])
# print(general_list[1]['HUB']['Input Length Units'])


