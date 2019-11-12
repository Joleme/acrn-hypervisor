# Copyright (C) 2019 Intel Corporation. All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import sys
import board_cfg_lib


def gen_cat(config):
    """
    Get CAT information
    :param config: it is a file pointer of board information for writing to
    """
    err_dic = {}
    (cache_support, clos_max) = board_cfg_lib.clos_info_parser(board_cfg_lib.BOARD_INFO_FILE)

    print("\n#include <board.h>", file=config)
    print("#include <acrn_common.h>", file=config)
    print("#include <msr.h>", file=config)

    if cache_support == "False" or clos_max == 0:
        print("\nstruct platform_clos_info platform_clos_array[0];", file=config)
        print("uint16_t platform_clos_num = 0;", file=config)
    else:
        print("\nstruct platform_clos_info platform_clos_array[{0}] = {{".format(
            clos_max), file=config)
        for i_cnt in range(clos_max):
            print("\t{", file=config)

            print("\t\t.clos_mask = {0},".format(hex(0xff)), file=config)
            if cache_support == "L2":
                print("\t\t.msr_index = MSR_IA32_{0}_MASK_{1},".format(
                    cache_support, i_cnt), file=config)
            elif cache_support == "L3":
                print("\t\t.msr_index = {0}U,".format(hex(0x00000C90+i_cnt)), file=config)
            else:
                err_dic['board config: generate board.c failed'] = "The input of {} was corrupted!".format(board_cfg_lib.BOARD_INFO_FILE)
                return err_dic
            print("\t},", file=config)

        print("};\n", file=config)
        print("uint16_t platform_clos_num = ", file=config, end="")
        print("(uint16_t)(sizeof(platform_clos_array)/sizeof(struct platform_clos_info));",
              file=config)

    print("", file=config)
    return err_dic


def gen_single_data(data_lines, domain_str, config):
    line_i = 0
    data_statues = True
    data_len = len(data_lines)
    for data_l in data_lines:
        if line_i == 0:
            if "not available" in data_l:
                print(data_l.strip(), file=config)
                print("static const struct cpu_{}x_data board_cpu_{}x[0];".format(domain_str, domain_str), file=config)
                print("", file=config)
                data_statues = False
                break
            else:
                print("static const struct cpu_{}x_data board_cpu_{}x[{}] = {{".format(domain_str, domain_str, data_len), file=config)
        print("\t{0}".format(data_l.strip()), file=config)
        line_i += 1
    if data_statues:
        print("};\n", file=config)


def gen_px_cx(config):
    """
    Get Px/Cx and store them to board.c
    :param config: it is a file pointer of board information for writing to
    """
    cpu_brand_lines = board_cfg_lib.get_info(
        board_cfg_lib.BOARD_INFO_FILE, "<CPU_BRAND>", "</CPU_BRAND>")
    cx_lines = board_cfg_lib.get_info(board_cfg_lib.BOARD_INFO_FILE, "<CX_INFO>", "</CX_INFO>")
    px_lines = board_cfg_lib.get_info(board_cfg_lib.BOARD_INFO_FILE, "<PX_INFO>", "</PX_INFO>")

    gen_single_data(cx_lines, 'c', config)
    gen_single_data(px_lines, 'p', config)

    for brand_line in cpu_brand_lines:
        cpu_brand = brand_line

    print("const struct cpu_state_table board_cpu_state_tbl = {", file=config)
    print("\t{0},".format(cpu_brand.strip()), file=config)
    print("\t{(uint8_t)ARRAY_SIZE(board_cpu_px), board_cpu_px,", file=config)
    print("\t(uint8_t)ARRAY_SIZE(board_cpu_cx), board_cpu_cx}", file=config)
    print("};", file=config)


def generate_file(config):
    """
    Start to generate board.c
    :param config: it is a file pointer of board information for writing to
    """
    err_dic = {}
    print("{0}".format(board_cfg_lib.HEADER_LICENSE), file=config)

    # insert bios info into board.c
    board_cfg_lib.handle_bios_info(config)

    # start to parser to get CAT info
    err_dic = gen_cat(config)
    if err_dic:
        return err_dic

    # start to parser PX/CX info
    gen_px_cx(config)

    return err_dic
