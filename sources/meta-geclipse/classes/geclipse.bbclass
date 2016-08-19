#************************************************************************************
# NAME          : geclipse.bbclass                                                   *
# AUTHOR        : Andrys Jiri (andrys.jiri+project_yoctogeclipse@gmail.com)          *
# VERSION       : 0.2                                                                *
#                                                                                    *
# DEPENDENCIES  :                                                                    *
#                 python2.7                                                          *
#                 >geclipse.py(0.2):                                                 *
#                   >>eclipse (>=kepler)
#                   >>os, sys, time, xml.etree.ElementTree, subprocess, shlex        *
#                 >geclipse_cdt.py(0.1):                                             *
#                   >>os, xml.dom.minidom, subprocess, random                        *
#                                                                                    *
#                                                                                    *
#                                                                                    *
# DESCRIPTION   :                                                                    *
#                 The `meta-geclipse` allows konfiguration/build of eclipse-project  *
#                 directly from yocto-recipes.                                       *
#                 The geclipse.bbclass should be considered as beta version.         *
#                                                                                    *
#                 Plugin has been tested on fsl-bsp version of yocto.                *
#                 Tested on Freescale's BSP 3.10.17[fsl-bsp_kernel 3.10.17]          *
#                                                                                    *
#                 Currently this plugin supports only Eclipse's CDT projects         *
#                 (Eclipse's C/C++ Development Tooling).                             *
#                 Eclipse's linked resources("virtual folders") are not supported.   *
#                                                                                    *
#*                                                                                   *
#*                                                                                   *
#* NO  Date                Modifier    Modified Content                              *
#*                                                                                   *
#* 1   20160514[YYMMDD]    J.Andrys    Initial version                               *
#*                                                                                   *
#* 2   20160703            J.Andrys    Add new functionality for                     *
#*                                     modification of CDT-xml                       *
#*                                                                                   *
#* 3   20150817            J.Andrys    Release 0.2 as beta release:                  *
#*                                                                                   *
#*                                                                                   *
#************************************************************************************


#GECLIPSE_PROJECTS_ALL_BUILD_VARS
#GECLIPSE_PROJECTS_ALL_FLAGS="IGNORE_YOCTO_CC_LD_FLAGS,
#                              SAME_LINKER_COMMAND_AS_COMPILER_COMMAND,
#                              ADD_FPIC_TO_SHARED_LIBS, ENABLE_PARALLEL_BUILD,
#                              REMOVE_ALL_NON_WORKSPACE_RELATED_INCLUDE_PATHS_AND_LIBRARY_PATHS"

#GECLIPSE_PROJECTS__ProjectNameBigLetters__POST_BUILD_STEP
#GECLIPSE_PROJECTS__ProjectNameBigLetters__LDFLAGS_LIBNAMES
# not yet> GECLIPSE_PROJECTS__ProjectNameBigLetters__CFLAGS
# not yet> GECLIPSE_PROJECTS__ProjectNameBigLetters__LDFLAGS


def get_prj_rel_var(d, obj_project, suffix_var_type):
    yocto_recipe_var_name="GECLIPSE_PROJECTS__{0}__{1}".format(obj_project.project_name.upper(),suffix_var_type)
    return d.getVar(yocto_recipe_var_name, True)

def get_new_build_configuration_name(d):
    return "geclipse-"+str(d.getVar("MACHINE", True))+"-"+str(d.getVar("GECLIPSE_PROJECTS_BUILD_CONF_STR", True))

def build_configuration_cdt(d, list_obj_project):
    import geclipse, geclipse_cdt, os
    bvars_lst=[]

    STAGING_DIR_HOST=d.getVar("STAGING_DIR_HOST", True)
    d.setVar("ROOTFS", STAGING_DIR_HOST)
    ROOTFS=d.getVar("ROOTFS", True)
    WORKDIR=d.getVar("WORKDIR", True)

    GECLIPSE_PROJECTS_ALL_FLAGS_list=[]
    if d.getVar("GECLIPSE_PROJECTS_ALL_FLAGS", True) is not None:
        GECLIPSE_PROJECTS_ALL_FLAGS_list=[ gflag.strip("\n").strip(" ") for gflag in d.getVar("GECLIPSE_PROJECTS_ALL_FLAGS", True).split(",") if len(gflag.strip("\n").strip(" ")) >0 ]


    CC_tmp=[ flg.strip(" ") for flg in d.getVar("CC", True).split(" ") if len(flg.strip(" ")) >0 ]
    CC=CC_tmp[0]
    cc_flags=""
    if len(CC_tmp) > 1:
        cc_flags=" ".join(CC_tmp[1:])
    tmp=d.getVar("CFLAGS", True)
    if len(tmp) > 1:
        cc_flags=cc_flags+" "+tmp

    LD_tmp=[ flg.strip(" ") for flg in d.getVar("LD", True).split(" ") if len(flg.strip(" ")) >0 ]
    LD=LD_tmp[0]
    ld_flags=""
    if len(LD_tmp) > 1:
        ld_flags=" ".join(LD_tmp[1:])
    tmp=d.getVar("LDFLAGS", True)
    if len(tmp) > 1:
        ld_flags=ld_flags+" "+tmp


    AS_tmp=[ flg.strip(" ") for flg in d.getVar("AS", True).split(" ") if len(flg.strip(" ")) >0 ]
    AS=AS_tmp[0]
    #as_flags=""
    #if len(AS_tmp) > 1:
    #    AS_flags=" ".join(AS_tmp[1:])


    if "IGNORE_YOCTO_CC_LD_FLAGS" in GECLIPSE_PROJECTS_ALL_FLAGS_list:
        #lazy settings of eclipse project without fPIC and yocto flags causing error
        cc_flags=""
        ld_flags=""
        #as_flags=""

    if "SAME_LINKER_COMMAND_AS_COMPILER_COMMAND" in GECLIPSE_PROJECTS_ALL_FLAGS_list:
        #in case of arm-XX-XX-ld for linker, and linker flags -Map={ProjName}.map, in lazy project setting > error
        LD=CC


    #{ PARSING BUILD VARIABLES
    #"{GECLIPSE_PROJECTS_ALL_BUILD_VARS}"

    bvars_lst.append({"name":"ROOTFS","value":ROOTFS})
    bvars_lst.append({"name":"WORKDIR","value":WORKDIR})

    bvs=d.getVar("GECLIPSE_PROJECTS_ALL_BUILD_VARS", True)
    if bvs is not None:
        bvars_lst_tmp=[ bv.strip("\n").strip(" ").replace(ROOTFS,"$"+"{ROOTFS}") for bv in bvs.split(",") if len(bv.strip("\n").strip(" ")) > 0 ]
        for var in bvars_lst_tmp:
            bvars_lst.append({"name":var.split("=")[0],"value":var.split("=")[1]})
    #}

    inc_paths=[ inc_path for inc_path in d.getVar("GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS", False).split(", ") ]
    lib_paths=[ lib_path for lib_path in d.getVar("GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS", False).split(", ") ]

    original_build_config=str(d.getVar("GECLIPSE_PROJECTS_BUILD_CONF_STR", True))
    new_build_config=get_new_build_configuration_name(d)

    #bb.plain("!!!!!!!: "+ str(new_build_config))


    #cdt project modification
    for obj_project in list_obj_project:
        pass
        lng_file=obj_project.project_language_file

        ec_cdt = geclipse_cdt.eclipse_language_file(lng_file)
        ec_cdt.new_build_config(original_build_config, new_build_config)
        #here we have build configuration on base of "${GECLIPSE_PROJECTS_BUILD_CONF_STR}"

        bc=ec_cdt.bc
        #clean all non workspace related include paths and library paths
        if "REMOVE_ALL_NON_WORKSPACE_RELATED_INCLUDE_PATHS_AND_LIBRARY_PATHS" in GECLIPSE_PROJECTS_ALL_FLAGS_list:
            bc.delete_all_non_workspace_related_libpaths()
            bc.delete_all_non_workspace_related_includepaths()


        #clean all build variables and set new ones
        bc.delete_all_build_variables()
        for bld_var in bvars_lst:
            bc.set_build_variable(bld_var["name"],bld_var["value"])

        #set compiler, linker, assembler, flags
        bc.set_compiler_command(CC)
        bc.set_linker_command(LD)
        bc.set_assembler_command(AS)

        bc.set_compiler_other_flags(cc_flags)
        bc.set_linker_flags(ld_flags)

        #includes, headers
        for inc_path in inc_paths:
            bc.set_compiler_includepath(inc_path)

        for lib_path in lib_paths:
            bc.set_linker_libpath(lib_path)


        if "ENABLE_PARALLEL_BUILD" in GECLIPSE_PROJECTS_ALL_FLAGS_list:
            bc.set_enable_parallel_build()

        #project-related variables
        if "ADD_FPIC_TO_SHARED_LIBS" in GECLIPSE_PROJECTS_ALL_FLAGS_list:
            #bb.plain(obj_project.project_name)
            bc.set_compiler_sharedlib_other_flags("-fPIC")

        yocto_recipe_var_value=get_prj_rel_var(d, obj_project, "POST_BUILD_STEP")
        if yocto_recipe_var_value is not None:
            yocto_recipe_var_value=yocto_recipe_var_value.replace(WORKDIR,"$"+"{WORKDIR}")
            bc.set_post_build_command(yocto_recipe_var_value)

        yocto_recipe_var_value=get_prj_rel_var(d, obj_project, "LDFLAGS_LIBNAMES")
        if yocto_recipe_var_value is not None:
            lbs_lst=[ lb.strip("\n").strip(" ") for lb in yocto_recipe_var_value.split(",") if lb.strip("\n").strip(" ") ]
            for lb in lbs_lst:
                bc.set_linker_libname(lb)


        #os.sys.exit(1)
        ec_cdt.update_eclipse_file()


#ROOTFS="STAGING_DIR_HOST"

#ORDER>
#1) Native path
#2) #GECLIPSE_PROJECTS_ALL_XXXX_PATHS
#3) #GECLIPSE_PROJECTS_ALL_FIND_XXXX_PATHS
#4) NOT IMPLEMENTED> #GECLIPSE_PROJECT_{ProjectName}_XXXX_PATHS
#5) NOT IMPLEMENTED> #GECLIPSE_PROJECT_{ProjectName}_FIND_XXXX_PATHS
#6) NOT IMPLEMENTED> #GECLIPSE_PROJECT_{ProjectName}_COMPILER_PARAMETERS
#7) NOT IMPLEMENTED> #GECLIPSE_PROJECT_{ProjectName}_LINKER_PARAMETERS


#COMPILER_RELATED_VARS:
#   GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS
#   GECLIPSE_PROJECTS_ALL_FIND_INCLUDE_PATHS

#LINKER_RELATED_VARS:
#   GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS
#   GECLIPSE_PROJECTS_ALL_FIND_LIBRARY_PATHS


def parse_params_geclipse_cdt(d):

    import subprocess, shlex

    DELIMS="\n {--parse_params_geclipse_cdt:--------------\n"
    DELIME=" }--parse_params_geclipse_cdt:--------------\n"
    DELIM1="   "

    bb.note(DELIMS)

    STAGING_DIR_HOST=d.getVar("STAGING_DIR_HOST", True)
    d.setVar("ROOTFS", STAGING_DIR_HOST)
    ROOTFS=d.getVar("ROOTFS", True)

    def get_inf_pkgconfig(packages_names_delim_str, pkgconfig_option="--cflags-only-I"):
        lst_paths_flags=[]

        packages=[ package.strip(" ") for package in packages_names_delim_str.split(",") if len(package) > 0 ]
        #bb.plain("  "+str(packages))
        for package in packages:
            #bb.plain(str(package))
            tmp="pkg-config {0} {1}  ".format(package, pkgconfig_option)
            flags_paths = subprocess.check_output(shlex.split(tmp))
            #bb.plain("  "+'"'+str(flags_paths)+'"')
            if pkgconfig_option == "--cflags-only-I" :
                delimiter="-I"
            elif pkgconfig_option == "--libs-only-L":
                delimiter="-L"
            elif pkgconfig_option == "--cflags-only-other" :
                delimiter="-D"

            one_lib_pths=[ pth.strip("\n").strip(" ").replace(ROOTFS,"$"+"{ROOTFS}") for pth in flags_paths.split(delimiter) if len(pth.strip("\n").strip(" ")) > 0 ]
            #bb.plain("  "+str(one_lib_pths))
            for pth in one_lib_pths:
                lst_paths_flags.append(pth)

        return lst_paths_flags
        #bb.plain("  "+str(lst_paths_flags))

    #--All paths for Includes(-I)----
    inc_pths_lst=[]
    inc_pths_lst.append(d.getVar("STAGING_INCDIR", True).replace(ROOTFS,"$"+"{ROOTFS}"))

    inc_pths_all_str=d.getVar("GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS", True)
    if inc_pths_all_str is not None:
        include_paths=[ pth.strip(" ").replace(ROOTFS,"$"+"{ROOTFS}") for pth in inc_pths_all_str.split(",") if (len(pth) > 0)  ]
        for pth in include_paths:
            inc_pths_lst.append(str(pth))

    packages_inc_pths=d.getVar("GECLIPSE_PROJECTS_ALL_FIND_INCLUDE_PATHS", True)
    if packages_inc_pths is not None:
        include_paths=get_inf_pkgconfig(packages_inc_pths, pkgconfig_option="--cflags-only-I")
        for pth in include_paths:
            inc_pths_lst.append(str(pth))

    #wipe out duplicities:
    inc_pths_lst=list(set(inc_pths_lst))
    back_to_str=", ".join(inc_pths_lst)
    d.setVar("GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS", back_to_str)

    bb.note(" "+"$"+"{GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS}:")
    for inc_path in d.getVar("GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS", False).split(", "):
        bb.note("   " + inc_path)
    bb.note("\n")


    #--All paths for Libraries(-L)----
    lib_pths_lst=[]
    lib_pths_lst.append(d.getVar("STAGING_BASELIBDIR", True).replace(ROOTFS,"$"+"{ROOTFS}"))
    lib_pths_lst.append(d.getVar("STAGING_LIBDIR", True).replace(ROOTFS,"$"+"{ROOTFS}"))

    lib_pths_all_str=d.getVar("GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS", True)
    if lib_pths_all_str is not None:
        lib_paths=[ pth.strip(" ").replace(ROOTFS,"$"+"{ROOTFS}") for pth in lib_pths_all_str.split(",") if (len(pth) > 0)  ]
        for pth in lib_paths:
            lib_pths_lst.append(str(pth))

    packages_lib_pths=d.getVar("GECLIPSE_PROJECTS_ALL_FIND_LIBRARY_PATHS", True)
    if packages_lib_pths is not None:
        lib_paths=get_inf_pkgconfig(packages_lib_pths, pkgconfig_option="--libs-only-L")
        #bb.plain(str(lib_paths))
        for pth in lib_paths:
            lib_pths_lst.append(str(pth))

    #wipe out duplicities:
    lib_pths_lst=list(set(lib_pths_lst))
    back_to_str=", ".join(lib_pths_lst)
    d.setVar("GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS", back_to_str)

    bb.note(" "+"$"+"{GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS}:")
    for lib_path in d.getVar("GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS", False).split(", "):
        bb.note("   " + lib_path)
    bb.note("\n")

    bb.note(DELIME)


#GENERAL OPTION FOR GECLIPSE.PY
#OPTIONAL                       : GECLIPSE_ECLIPSE_BIN
#MANDATORY                      : GECLIPSE_PROJECTS_ROOT_DIR OR "S" VARIABLE IN YOCTO
#OPTIONAL                       : GECLIPSE_PROJECTS_WORKSPACE_DIR
#HIGHLY_RECOMMENDED/OPTIONAL    : GECLIPSE_PROJECTS_NAMES_DELIMSTR
#OPTIONAL:                      : GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH
#MANDATORY                      : GECLIPSE_PROJECTS_BUILD_CONF_STR

def parse_params_geclipse(d):
    import subprocess, sys, os
    #sys.path.append(os.path.dirname(os.path.abspath("__file__")))
    DELIMS=" {--do_parse_param:--------------\n"
    DELIME=" }--do_parse_param:--------------\n"
    DELIM1="   "

    bb.note(DELIMS)

    ec=d.getVar("GECLIPSE_ECLIPSE_BIN", True)
    if ec is None:
      ec=subprocess.check_output("whereis eclipse",shell=True)
      if len(ec.split("/")) > 1:
        ec=ec.split(" ")[1].strip("\n")
        bb.note(DELIM1 + "Eclipse was found by whereis !!!! ")
      else:
        bb.error(DELIM1 + 'Eclipse not found by "whereis" command !!!! "'+str(ec)+'"')
        os.sys.exit(1)
    if not os.path.isfile(ec):
      bb.error(DELIM1 + 'Eclipse not found by "whereis" command !!!! "'+str(ec)+'"')
      os.sys.exit(1)
    bb.note(DELIM1 + 'GECLIPSE_ECLIPSE_BIN="'+str(ec)+'"')

    ec_ps_root=d.getVar("S", True)
    if not os.path.isdir(str(ec_ps_root)):
      bb.error(DELIM1 + 'Path in "S" variable was not found !!!! "'+str(ec_ps_root)+'"')
      os.sys.exit(1)

    d.setVar("GECLIPSE_PROJECTS_ROOT_DIR", ec_ps_root)
    ec_ps_root=d.getVar("GECLIPSE_PROJECTS_ROOT_DIR", True)
    if os.path.isdir(ec_ps_root) is not True:
      bb.error(DELIM1 + "GECLIPSE_PROJECTS_ROOT_DIR="+str(ec_ps_root)+" not found !!!! ")
      os.sys.exit(1)
    bb.note(DELIM1 + 'GECLIPSE_PROJECTS_ROOT_DIR="'+ str(ec_ps_root)+'"')

    ec_ps_ws=d.getVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", True)
    if ec_ps_ws is None:
      ec_ps_ws=ec_ps_root+"/workspace"
      if os.path.isdir(ec_ps_ws) is False:
        try:
          os.mkdir(ec_ps_ws)
          bb.note(DELIM1 + 'Workspace directory was created"'+ str(ec_ps_ws)+'"')
        except Exception, e:
          bb.error(DELIM1 + 'Unable to create workspace directory: "'+ec_ps_ws+" !!!! "+DELIM1+str(e.message))
          os.sys.exit(1)
        else:
          d.setVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", ec_ps_ws)
          ec_ps_ws=d.getVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", True)
      else:
        bb.note(DELIM1 + 'Workspace directory already exists')
        d.setVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", ec_ps_ws)
        ec_ps_ws=d.getVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", True)
    else:
      if os.path.isdir(ec_ps_ws) is False:
        bb.error(DELIM1 + "GECLIPSE_PROJECTS_WORKSPACE_DIR="+str(ec_ps_ws)+" not found !!!! ")
        os.sys.exit(1)
    bb.note(DELIM1 + 'GECLIPSE_PROJECTS_WORKSPACE_DIR="'+ str(ec_ps_ws)+'"')

    ec_ps_strlst=d.getVar("GECLIPSE_PROJECTS_NAMES_DELIMSTR", False)
    if ec_ps_strlst is not None:
      ec_ps_strlst=[ prj.strip(" ") for prj in ec_ps_strlst.split(",") ]
      ec_ps_strlst=",".join(ec_ps_strlst)
    bb.note(DELIM1 + 'GECLIPSE_PROJECTS_NAMES_DELIMSTR="'+ str(ec_ps_strlst)+'"')

    ec_ps_skip_if_in_prjpath=d.getVar("GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH", False)
    bb.note(DELIM1 + 'GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH="'+ str(ec_ps_skip_if_in_prjpath)+'"')

    ec_ps_build_conf=d.getVar("GECLIPSE_PROJECTS_BUILD_CONF_STR", True)
    if ec_ps_build_conf is None:
      bb.error(DELIM1 + 'The "GECLIPSE_PROJECTS_BUILD_CONF_STR" variable was not set in yocto-recipe !!!! "'+str(ec_ps_build_conf)+'"')
      os.sys.exit(1)
    bb.note(DELIM1 + 'GECLIPSE_PROJECTS_BUILD_CONF_STR="'+ str(ec_ps_build_conf)+'"')

    bb.note(DELIME)


#addtask btest before do_configure

#python geclipse_do_btest() {
#    DELIM="\n-----------------\n"
#    bb.plain(DELIM)
#    parse_params(d)
#    bb.plain(DELIM)
#}

#geclipse_do_configure() {
#    :
#}

python geclipse_do_configure() {
    parse_params_geclipse(d)
    parse_params_geclipse_cdt(d)

    import geclipse, geclipse_cdt
    #import time, sys, curses, termios
    #crs=curses
    #crs.setupterm()

    #bb.plain("\n--------------------------------------")

    DELIMS="\n {--do_configure:--------------\n"
    DELIME=" }--do_configure:--------------\n"
    DELIM1="   "
    bb.note(DELIMS)

    tmp=geclipse.eclipse_projects(d.getVar("GECLIPSE_PROJECTS_ROOT_DIR", True), \
                                  d.getVar("GECLIPSE_PROJECTS_NAMES_DELIMSTR", False), \
                                  d.getVar("GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH", False))
    if tmp.projects_err["errno"] is not None:
        bb.error(DELIM1 + tmp.projects_err["errinfo"])
        os.sys.exit(1)
    else:
        f_projects = tmp.eclipse_projects

    for bla in f_projects:
        bb.note(DELIM1 + os.path.dirname(bla.project_file).replace(str(d.getVar("WORKDIR",True)),"$"+"{WORKDIR}"))
    bb.note(DELIM1)


    #=BUILD_CONFIGURATION===========================================
    #Here should be filled all paths to libs and includes gived by
    # GECLIPSE_PROJECTS_ALL_FIND_{LIBRARY|HEADERS}_PATHS >
    #
    #${GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS} , ${GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS}
    #

    build_configuration_cdt(d, f_projects)

    #
    #=BUILD_CONFIGURATION===========================================



    et=geclipse.eclipse_tasks(d.getVar("GECLIPSE_ECLIPSE_BIN", True), \
                              d.getVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", True), \
                              tmp.eclipse_projects)

    et.set_status_prefix(DELIM1)
    et.set_status_handler(bb.error, geclipse.eclipse_tasks.STATUS_LEVEL_ERROR)
    et.set_status_handler(bb.note, geclipse.eclipse_tasks.STATUS_LEVEL_INFO)
    et.set_progress_handler(bb.plain, DELIM1)
    et.set_status_level(geclipse.eclipse_tasks.STATUS_LEVEL_INFO)

    bb.note(DELIM1)
    bb.note(DELIM1 + "{ --ECLIPSE_IMPORT-------------- ")
    bb.plain("\n"+DELIM1 + "{ --ECLIPSE_IMPORT-------------- \n\n")
    returncode, ret_stdout, ret_stderr=et.import2ws()
    bb.plain(DELIM1 + "{ --ECLIPSE_IMPORT-------------- ")
    bb.note(DELIM1 + "} --ECLIPSE_IMPORT-------------- ")

    if returncode == 0:
      bb.note(DELIM1 + "ECLIPSE_IMPORT: return code: "+str(returncode))
      bb.note(DELIM1 + "ECLIPSE_IMPORT: stderr: \n"+str(ret_stderr))
      bb.note(DELIM1 + "ECLIPSE_IMPORT: stdout: \n"+str(ret_stdout))
    else:
      bb.error("Eclipse_returncode: "+str(returncode))
      bb.error("Eclipse_stderr: "+str(ret_stderr))
      bb.error("Eclipse_stdout: "+str(ret_stdout))
      bb.plain(DELIM1 + "{ --ECLIPSE_IMPORT-------------- ")
      os.sys.exit(1)
    bb.note(DELIME)
}

#geclipse_do_compile() {
#    :
#}

python geclipse_do_compile() {
    parse_params_geclipse(d)
    import geclipse

    #bb.plain("\n--------------------------------------")
    #bb.plain(d.getVar("KERNEL_DIR", True))
    #bb.plain("\n--------------------------------------")

    #os.sys.exit(1)


    DELIMS="\n {--do_compile:--------------\n"
    DELIME=" }--do_compile:--------------\n"
    DELIM1="   "
    bb.note(DELIMS)

    path2projects=[]
    tmp=geclipse.eclipse_projects(d.getVar("GECLIPSE_PROJECTS_ROOT_DIR", True), \
                                  d.getVar("GECLIPSE_PROJECTS_NAMES_DELIMSTR", False), \
                                  d.getVar("GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH", False))
    if tmp.projects_err["errno"] is not None:
        bb.error(DELIM1 + tmp.projects_err["errinfo"])
        os.sys.exit(1)
    else:
        f_projects = tmp.eclipse_projects

    for bla in f_projects:
        bb.note(DELIM1 + os.path.dirname(bla.project_file))
        path2projects.append(os.path.dirname(bla.project_file))
    bb.note(DELIM1)

    et=geclipse.eclipse_tasks(d.getVar("GECLIPSE_ECLIPSE_BIN", True), \
                              d.getVar("GECLIPSE_PROJECTS_WORKSPACE_DIR", True), \
                              tmp.eclipse_projects)

    et.set_status_prefix(DELIM1)
    et.set_status_handler(bb.error, geclipse.eclipse_tasks.STATUS_LEVEL_ERROR)
    et.set_status_handler(bb.note, geclipse.eclipse_tasks.STATUS_LEVEL_INFO)
    et.set_progress_handler(bb.plain,DELIM1)
    et.set_status_level(geclipse.eclipse_tasks.STATUS_LEVEL_INFO)

    bb.note(DELIM1 + "{ --ECLIPSE_BUILD-------------- ")
    bb.plain("\n"+DELIM1 + "{ --ECLIPSE_BUILD-------------- \n\n")

    returncode=et.build2(get_new_build_configuration_name(d))

    bb.plain(DELIM1 + "{ --ECLIPSE_BUILD-------------- ")
    bb.note(DELIM1 + "} --ECLIPSE_BUILD-------------- ")

    if returncode == 1:
      bb.note(DELIM1 + "ECLIPSE_BUILD: return code: "+str(returncode))
      #bb.note(DELIM1 + "ECLIPSE_BUILD: stderr: \n"+str(ret_stderr))
      #bb.note(DELIM1 + "ECLIPSE_BUILD: stdout: \n"+str(ret_stdout))
    else:
      bb.error("Eclipse_returncode: "+str(returncode))
      #bb.error("Eclipse_stderr: "+str(ret_stderr))
      #bb.error("Eclipse_stdout: "+str(ret_stdout))
      bb.note(DELIME)
      os.sys.exit(1)
    bb.note(DELIME)
}

EXPORT_FUNCTIONS do_compile do_configure