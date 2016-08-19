#! /usr/bin/python2.7
#
# This module provides support for the generic Eclipse project file
# in Yocto/Poky/OpenEmbedded build system
#
# Copyright (C) 2016  Andrys Jiri(andrys.jiri+project_yoctogeclipse@gmail.com)
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Depends what FAQ(https://eclipse.org/legal/eplfaq.php) says,
# using modules of eclipse,
# linking and therefore interfacing with eclipse is not derivative
# work ?
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
"""This module provides support for building eclipse projects in Yocto/Poky/OpenEmbedded build system.

The current version 0.2 supports only CDT-projects writen in c\nand is considered as beta version.

Example:
    Just imagine that we have cdt projects :
    "prj1", "prj2(executable)", "prj3(tests)", in "/home/username/project_root" folder.

    Folder-tree structure:
        "/home/username/projects_root/posixAPI/prj1"
        "/home/username/projects_root/winAPI/prj1"
        "/home/username/projects_root/prj2"
        "/home/username/projects_root/prj3"

    We want to build only "prj1" and "prj2".
    Unfortunately, we have prj1 called twice the same way and we wanna build sw for posixAPI.

    SRC:
        import geclipse

        ecp=geclipse.eclipse_projects("/home/username/projects_root", "prj1, prj2", "winAPI")

        if ecp.projects_err["errno"] is None:
            for prj in ecp.eclipse_projects:
                print("This is path to project file:" + prj.project_file)
                .
                .
                .

            et=geclipse.eclipse_tasks("/home/$SOMEUSER/eclipse/eclipse","/home/$SOMEUSER/workspace/",\
                                      ecp.eclipse_projects)

            #For yocto env we need to set it like that:
            et.set_status_handler(print, et.STATUS_LEVEL_INFO)
            et.set_status_handler(print, et.STATUS_LEVEL_ERROR)
            et.set_status_level(level,et.STATUS_LEVEL_INFO)
            et.set_progress_handler(print, " ERR:")

            et.add_include_dir("/home/username/projects_root/prj2/includes")

            et.import2ws()

            et.build2("Release")
            .
            .
            .
"""

import os, sys
import xml.etree.ElementTree as ET
import subprocess, shlex
import time

__all__ = ["eclipse_projects", "eclipse_tasks"]
__version__ = 0.2
__date__ = '2016-05-14'
__updated__ = '2016-08-14'

class eclipse_project(object):
    """Public class which holds properties of one single project and parse eclipse-project-file.
    This class is initiated by "eclipse_projects" class,
    therefore user will not call its constructor directly.
    """

    def __init__(self, prj_file, prj_lang_file):
        """Initiated by "eclipse_projects" class, parse eclipse-project-file and holds paths to project's resources.
        Linked resource called "virtual folders" are not supported !
        """

        self.project_file=prj_file
        self.project_language_file = prj_lang_file
        self.project_name=None
        self.project_linked_resources = None
        self.project_err = {"errno":None, "errinfo":None, "exceptioninfo":None}
        self.__project_err_exceptioninfo=None

        tmp=self.__parse_project_file(prj_file)
        if tmp[0] == 0:
            self.project_linked_resources=tmp[2]

        else:
            self.project_err["errno"]=tmp[0]
            self.project_err["errinfo"]=eclipse_project.__geterrdesc(tmp[0])
            self.project_err["exceptioninfo"]=self.__project_err_exceptioninfo

        #LOGGER:INFO
        #glogger.debug("project_name: " + self.project_name)
        #glogger.debug("project_file: " + self.project_file)

    def __parse_project_file(self, prj_file):
        """Parse eclipse #prj_file file and return project name

        #prj_file
                 is path to .project

        #return values
                This function should return list of two items
                    return [error_number,  project_name, [linked resources]]

                    where,
                        #error_number           : integer value
                        #project_name           : string, project name
                        #[linked_resource]      : list of linked resources
                        #linked_resource        : dictionary which describes one linked resource
                        #linked_resource        : {"abspath": abs_path,
                                                    "uri":value_of_locationURI,
                                                    "name": value_of_tag_name"),
                                                    "type": value_of_tag_type")}
                        OR

                        #linked_resource        : {"abspath": abs_path,
                                                    "location":value_of_tag_location,
                                                    "name": value_of_tag_name),
                                                    "type": value_of_tag_type)}

                        if #error_number==0 -> OK,
                        if #error_number==1 -> NG, error project file does not exist
                        if #error_number==2 -> NG, error open/read project file
                        if #error_number==3 -> NG, error xml, format
                        if #error_number==4 -> NG, error xml, can not get root
                        if #error_number==5 -> NG, error unexpected tag of xml root
                        if #error_number==6 -> NG, error linked resource tag found but link tag not found
                        if #error_number==7 -> NG, error linked resource type != 2 > file
                        if #error_number==8 -> NG, error linked resource virtual folders are not supported
                        if #error_number==9 -> NG, error linked resource folder does not exist
                        if #error_number==10 -> NG, error linked resource path related tag was not found
         """
        #prj_file=".project"

        ECLIPSE_PROJECT_XML_FILE_ROOT_TAG_NAME="projectDescription"

        if os.path.isfile(prj_file):
            try:
                of = open(prj_file, "rt")
                xml_alltxtdata = of.read()
            except Exception, e:
                #sys.stderr.write("\nError: " + prj_file + " :" + str(e.message) + "\n")
                self.__project_err_exceptioninfo=str(e.message)
                #sys.stderr.flush()
                of.close()
                return  [2, None, None]
            else:
                try:
                    of.close()
                    tree = ET.ElementTree(ET.fromstring(xml_alltxtdata))
                except Exception, e:
                    #sys.stderr.write("\nError: "+prj_file+" :"+str(e.message)+"\n")
                    self.__project_err_exceptioninfo = str(e.message)
                    #sys.stderr.flush()
                    return [3, None, None]
                else:
                    if tree.getroot().tag is not None:
                        if tree.getroot().tag == ECLIPSE_PROJECT_XML_FILE_ROOT_TAG_NAME:

                            el_name=tree.find("./name")

                            if ET.iselement(el_name):

                                #fill if u can!!
                                self.project_name=el_name.text

                                #check if src is somewhere else: tag=linkedResources
                                el_linkedResources = tree.find("./linkedResources")
                                if el_linkedResources is None:
                                    return [0, el_name.text, None]

                                #linkedResources:
                                #   Type 1 is file
                                #   Type 2 is folder
                                #   Only type 2 is supported, virtual folders are not supported:
                                #< name > src / rtsp_client < / name >
                                #< type > 2 < / type >
                                #< locationURI > virtual: / virtual < / locationURI >

                                # in gui: import-> "Create links in workspace"
                                #   absolut path in link structure
                                #   <type>2</type>
                                #   <location>/mnt/bla</location>
                                #
                                #   After convert to dyn path:
                                #       <type>2</type>
                                #       <locationURI>PARENT-1-ECLIPSE_HOME/mnt/bla</locationURI>

                                # if proj_file=workspace/proj_name/.project then:
                                # if path2eclipse=home/$USER/eclipse/eclipse then:
                                # PROJECT_LOC=workspace/proj_name/
                                # PARENT_LOC=workspace
                                # WORKSPACE_LOC=workspace
                                # ECLIPSE_HOME==home/$USER/eclipse/

                                el_linkedResources_links = tree.findall("./linkedResources/link")
                                if el_linkedResources_links is not None:

                                    linked_resources = []
                                    for lnk in el_linkedResources_links:


                                        #test unsupported types
                                        if lnk.find("./type").text != "2":
                                            self.__project_err_exceptioninfo = " <link>\n  <name>"+lnk.find("./name").text+"<name>\n  </link>"
                                            return [7, None, None]

                                        el_loc_uri=lnk.find("./locationURI")
                                        el_loc = lnk.find("./location")

                                        #locationURI tag
                                        if el_loc_uri is not None:

                                            #dynamic_relative_variable=PARENT-1-ECLIPSE_HOME | PROJECT_LOC | PARENT_LOC | WORKSPACE_LOC
                                            dynamic_rel_var=el_loc_uri.text.split("/")[0]
                                            if dynamic_rel_var.find("virtual:")>-1:
                                                self.__project_err_exceptioninfo = \
                                                    " <locationURI>" + el_loc_uri.text + "</locationURI>"
                                                return [8, None, None]

                                            #relative_move_test
                                            if dynamic_rel_var.startswith("PARENT-"):

                                                #PROJECT_LOC only is implemented
                                                if dynamic_rel_var.endswith("-PROJECT_LOC"):

                                                    num = [int(char) for char in dynamic_rel_var.split("-") if char.isdigit()]
                                                    dyn_var=os.path.dirname(prj_file)+"/.." * num[0]
                                                    rel_prj_pth=el_loc_uri.text[el_loc_uri.text.find("/"):]
                                                    pth=dyn_var+rel_prj_pth
                                                    if os.path.isdir(pth):
                                                        abs_path=os.path.abspath(pth)
                                                        link_res = {"abspath": abs_path, "uri": el_loc_uri.text,
                                                                    "name": lnk.find("./name").text,
                                                                    "type": lnk.find("./type").text}
                                                    else:
                                                        #path does not exist
                                                        self.__project_err_exceptioninfo = \
                                                            " <locationURI>" + el_loc_uri.text + "</locationURI>"
                                                        return [9, None, None]

                                        #locaction tag
                                        elif el_loc is not  None:
                                            if os.path.isdir(el_loc.text):
                                                link_res = {"abspath":os.path.abspath(el_loc.text), "location": el_loc.text,
                                                            "name": lnk.find("./name").text,
                                                            "type": lnk.find("./type").text}
                                            else:
                                                # path does not exist
                                                self.__project_err_exceptioninfo = \
                                                    " <location>" + el_loc.text + "</location>"
                                                return [9, None, None]

                                        # linked resources path related tags not found
                                        else:
                                            self.__project_err_exceptioninfo = " <name>" + lnk.find("./name").text + "</name>"
                                            return [10, None, None]

                                        #lnk resource add to arr
                                        linked_resources.append(link_res)

                                    #RETURN all with list of linked resources
                                    return [0, el_name.text, linked_resources]

                                else:
                                    #"resource tag found and link tag not found."
                                    return [6, None, None]
                        else:
                            # unexpected tag of root
                            self.__project_err_exceptioninfo = " XML_ROOT: " + tree.getroot().tag
                            return [5, None, None]
                    else:
                        # cannot get root
                        return [4, None, None]
        else:
            #prj file not found
            return [1, None, None]

    @staticmethod
    def __geterrdesc(errno):
        if errno == 0:
            return "It seems that everything is okeey, but who knows ...."
        if errno == 1:
            return "Project file error, no such a file."
        if errno == 2:
            return "Project file error, open/read file."
        elif errno == 3:
            return "Xml error, xml format."
        elif errno == 4:
            return "Xml error, can not get xml root."
        elif errno == 5:
            return "Xml error, unexpected tag of xml root."
        elif errno == 6:
            return "Xml error, linked resource tag found and link tag not found."
        elif errno == 7:
            return "Linked resource error, unsupported format of project, linked resource type != 2 > file."
        elif errno == 8:
            return "Linked resource error, unsupported format of project, virtual folders are not supported."
        elif errno == 9:
            return "Linked resource error, linked folder does not exist."
        elif errno == 10:
            return "Linked resource error, path related tag was not found."
        else:
            return "Unknown error."


    def geterr(self):

        if self.project_err["errno"] is None:
            return None

        tmp=eclipse_project.__geterrdesc(self.project_err["errno"])

        errmess="Project file: "+self.project_file+'\n'

        if self.project_name is not None:
            errmess+="Project name: "+self.project_name+'\n'

        errmess += "  Error: " + '\n'
        errmess += "    Errno: " + str(self.project_err["errno"]) + '\n'
        errmess += "    Errorinfo: " + tmp + '\n'
        if self.__project_err_exceptioninfo is not None:
            errmess += "    XML: " + self.__project_err_exceptioninfo + '\n'

        return errmess


class eclipse_projects(object):
    """Common public class which find and parse project-eclipse-files[.project],
    and holds basic paths to projects in #self.eclipse_projects and check if language related eclipse file exists.
    """

    def __init__(self, projects_root_dir, projects_delim_str=None, skip_if_str_in_path=None,
                 eclipse_project_file=".project", eclipse_project_language_file=".cproject"):
        """Search and parse #eclipse_project_file under #projects_root_dir.

        #projects_root_dir
             is path to root directory/workspace where projects are located,
             does not matter how deep project files are

        #projects_delim_str
             is space delimited string of projects names

        #skip_if_str_in_path
            is string, skip project if given #skip_if_str_in_path string is in path

        #eclipse_project_file=".project"
            is string, name of project file,
            most probably always the same, for features purposes

        #eclipse_project_language_file=".cproject"
            is string, name of programming-language related file,
            right now only cdt is supported(.cproject)

        """

        self.projects_root_dir=projects_root_dir
        self.projects_delim_str=projects_delim_str
        self.skip_if_str_in_path=skip_if_str_in_path
        self.eclipse_proj_file = eclipse_project_file
        self.eclipse_project_language_file = eclipse_project_language_file
        self.eclipse_projects=None
        self.projects_err={"errno": None, "errinfo": None}

        tmp=self.__eclipse_projects_find()
        if tmp[0] == 0 :
            self.eclipse_projects=tmp[1]
        else:
            self.projects_err["errno"] = tmp[0]
            errmess = "Eclipse projects root folder: " + self.projects_root_dir + "\n"
            errmess += "  Error: \n"

            #errors in this class
            if tmp[0] == 101:
                errmess += "    Projects root folder not found\n"
            if tmp[0] == 102:
                errmess += "    Language-related project file .cproject not found\n"
            if tmp[0] == 103:
                errmess += "    Number of requested projects is smaller than number of found projects\n"
            if tmp[0] == 104:
                errmess += '    Requested project "'+tmp[1]+'" has not been found'+"\n"

            self.projects_err["errinfo"] = errmess

    def __eclipse_projects_find(self):
        """Parse eclipse #prj_file file and return project name

        #projects_root_dir
             is path to root directory/workspace where projects are located,
             does not matter how deep project files are,

        #projects_delim_str
             is space delimited string of projects names

        #skip_if_str_in_path
            is string, skip project if given string is in path

        #return values
            This function should return list of two items
                return [error_number,  [instances of class eclipse_project ] ]

                where,
                    #error_number    : integer value

        """

        f_projects=[]
        f_prj_files=[]
        if os.path.isdir(self.projects_root_dir):

            for root, dirs, files in os.walk(self.projects_root_dir):
                for file in files:
                    if file == self.eclipse_proj_file:
                        f_prj_files.append(os.path.join(root, file))

            if self.skip_if_str_in_path is not None:
                f_prj_files=[ prj_file for prj_file in f_prj_files if not prj_file.find(self.skip_if_str_in_path)>-1 ]
        else:
            # 1: "Projects root folder not found"
            return [101, [None]]


        #Get projects information, parse all project files ".project"
        for f_prj_file in f_prj_files:

            f_prj_lang_file=os.path.dirname(f_prj_file)+"/"+self.eclipse_project_language_file
            if not os.path.isfile(f_prj_lang_file):
                # 2: "Eclipse language project file .croject not found"
                #print f_prj_lang_file
                return [102, [None]]

            prj_obj=eclipse_project(f_prj_file, f_prj_lang_file)
            if prj_obj.project_err["errno"] is None:
                f_projects.append(prj_obj)
            else:
                return [prj_obj.project_err["errno"], [prj_obj]]

            #glogger.info("f_project: " + prj_obj.project_name)

        #No project list ->  projects_delim_str = None -> All projects in gived folder and subfolders
        if self.projects_delim_str is None:
            return [0, f_projects]
        else:
            n_projects_names = [prj.strip(" ") for prj in self.projects_delim_str.split(",")]

        #if n_projects[:] > f_projects[:] : -> ERROR
        #[prj1 prj2 prj3] > [prj1 prj2] -> ERROR
        #
        if len(n_projects_names) > len(f_projects):
            #Number of requested projects is smaller than number of found projects
            return [103, None]

        f_projects_filtered=[]
        for n_prj_name in n_projects_names:
            tmp=eclipse_projects.__is_n_prj_in_fnd_prj(n_prj_name, f_projects)
            if not tmp[0] is 0:
                # Requested project n_prj has not been found
                return [104, n_prj_name]
            else:
                f_projects_filtered.append(tmp[1])

        return [0, f_projects_filtered]

    @staticmethod
    def __is_n_prj_in_fnd_prj(n_prj_name, fnd_prj_objects):
        for f_prj in fnd_prj_objects:
            if f_prj.project_name == n_prj_name:
                #glogger.info('"'+f_prj.project_name+'"' +" == "+ '"'+n_prj_name+'"')
                return [0, f_prj]
        return [1, None]


class eclipse_tasks():
    """Common public class which run headlessbuild class from eclipse.

    Allows basic modification of build configuration by
        self.add_include_dir()
        self.add_preprocdefine()
        self.add_evar_replace()
        self.add_evar_append()
        self.add_evar_prepend()
        self.add_evar_unset()
        self.add_tooloption_append()

    export to workspace by
        self.import2ws()
    projects build by headlessbuild class by
        self.build2()

    Constructor of this class need to have list of "eclipse_project" instances.

    Example:
        import geclipse

        ecp=geclipse.eclipse_projects("/home/username/projects_root", "prj1, prj2", "winAPI")

        if ecp.projects_err["errno"] is None:
            et=geclipse.eclipse_tasks("/home/$SOMEUSER/eclipse/eclipse","/home/$SOMEUSER/workspace/",\
                                      ecp.eclipse_projects)

            et.add_include_dir("/home/username/projects_root/prj2/includes")

            et.import2ws()

            et.build2("Release")
    """

    __base_params="-noSplash --launcher.suppressErrors "
    __ec_hlb_cmd="-application org.eclipse.cdt.managedbuilder.core.headlessbuild "

    #-no-indexer is not compatible with kepler and older version of eclipse
    #__ec_hlb_cmd="-application org.eclipse.cdt.managedbuilder.core.headlessbuild -no-indexer"

    __PI_DELIM = "ECLIPSE: = PROJECT_IMPORT ============================================= \n"
    STATUS_LEVEL_ERROR=0
    STATUS_LEVEL_INFO=1

    def __init__(self, eclipse_path, workspace, list_eclipse_project):
        """Constructor parameters:

        #eclipse_path
            is string, path to eclipse binary

        #workspace
            is string, path to workspace directory

        #list_eclipse_project
            is list of "project_eclipse" instances
        """
        self.eclipse_path=eclipse_path
        self.workspace=workspace
        self.list_eclipse_project=list_eclipse_project
        self.global_eclipse_project={"include_dirs":None,"preprocD":None,"evars":None, "tooloption":None}
        self.statushandler=[None, None]
        self.progresshandler = None
        self.progressprefix = ""
        self.statuslevel  =  None
        self.statusprefix = ""

    def set_status_handler(self,status_handler, handler_level):
        """Set #status_handler function which will be called and depend on status level.
        The #status_handler is print-like function.
        """
        self.statushandler[handler_level]=status_handler

    def set_status_level(self, level):
        """Set status level for status_handler function"""
        self.statuslevel = level

    def set_status_prefix(self, prefix_string):
        self.statusprefix = prefix_string

    def __smess(self, messstr, current_level):
        #err=0;info=1;all=2
        if self.statuslevel >= current_level and \
                        self.statushandler[current_level] is not None and \
                        self.statuslevel is not None:
            self.statushandler[current_level](self.statusprefix + str(messstr))

    def status_test_print(self, somestring, level):
        self.__smess(somestring,level)

    def set_progress_handler(self, progress_handler, message_prefix=""):
        """Set #progress_handler function which will be called during import2ws() and build2() task.
        The #progress_handler is print-like function.
        """
        self.progresshandler = progress_handler
        self.progressprefix = message_prefix

    def __pmess(self, messstr, lastmess=False):
        #err=0;info=1;all=2
        if self.progresshandler is not None:
            if not lastmess:
                self.progresshandler('\x1b[80D\x1b[1A\x1b[1A\x1b[K'+self.progressprefix + str(messstr)+"\n")
            else:
                self.progresshandler('\x1b[80D\x1b[1A\x1b[1A\x1b[K' + self.progressprefix + str(messstr))

    __add_include_dir = "-I"
    def add_include_dir(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project[""] is None:
          self.global_eclipse_project["include_dirs"]=[]
        self.global_eclipse_project["include_dirs"].append(eclipse_tasks.__add_include_dir +" "+ var_val + " ")

    __add_preprocdefine = "-D"
    def add_preprocdefine(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project[""] is None:
          self.global_eclipse_project["preprocD"]=[]
        self.global_eclipse_project["preprocD"].append(eclipse_tasks.__add_preprocdefine +" "+ var_val + " ")

    __evar_param_replace = "-E"
    def add_evar_replace(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project["evars"] is None:
          self.global_eclipse_project["evars"]=[]
        self.global_eclipse_project["evars"].append(eclipse_tasks.__evar_param_replace +" "+ var_val + " ")

    __evar_param_apppend = "-Ea"
    def add_evar_append(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project["evars"] is None:
          self.global_eclipse_project["evars"]=[]
        self.global_eclipse_project["evars"].append(eclipse_tasks.__evar_param_apppend +" "+ var_val + " ")

    __evar_param_prepend = "-Ep"
    def add_evar_prepend(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project["evars"] is None:
          self.global_eclipse_project["evars"]=[]
        self.global_eclipse_project["evars"].append(eclipse_tasks.__evar_param_prepend +" "+ var_val + " ")

    __evar_param_unset = "-Er"
    def add_evar_unset(self, var_val, project_name=None):
      if project_name is None:
        if self.global_eclipse_project["evars"] is None:
          self.global_eclipse_project["evars"]=[]
        self.global_eclipse_project["evars"].append(eclipse_tasks.__evar_param_unset +" "+ var_val + " ")
        
        
    __add_to_append = "-Ta"
    def add_tooloption_append(self, toolid, optionid_val):
      if self.global_eclipse_project["tooloption"] is None:
        self.global_eclipse_project["tooloption"]=[]
      self.global_eclipse_project["tooloption"].append(eclipse_tasks.__add_to_append +" "+ toolid + " "+optionid_val+" ")

    def import2ws(self, timeout_sec=180):
        """Eclipse need to have workspace before build."""

        cmd_import =self.eclipse_path+" "
        cmd_import += "-data "+self.workspace+" "
        cmd_import += eclipse_tasks.__base_params+" "
        cmd_import +=eclipse_tasks.__ec_hlb_cmd+" "
        cmd_projects=""
        
        for prj in self.list_eclipse_project:
            cmd_projects+="-importAll "+'"'+os.path.dirname(prj.project_file)+'"'+" "
        cmd_import+=cmd_projects

        cmd_glob=" "
        for key in self.global_eclipse_project.keys():
            if self.global_eclipse_project[key] is not None:
                cmd_glob=" ".join(self.global_eclipse_project[key])

        cmd_import+=" "+cmd_glob


        args = shlex.split(cmd_import)
        #glogger.info(args)
        self.__smess(args,self.STATUS_LEVEL_INFO)
        self.__smess("", self.STATUS_LEVEL_INFO)
        sp = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        old_time=time.time()
        time_s=0;it=1;
        while (time.time() - old_time) < timeout_sec:

            it += 0.1;
            time_s = (1.5 + (it * it * 0.25) / 1000)
            time.sleep(time_s)

            #glogger.info("importing: {:4f}".format(time.time() - old_time))
            #self.__smess("ECLIPSE_IMPORT: {:4f}".format(time.time() - old_time), self.STATUS_LEVEL_INFO)
            self.__pmess("ECLIPSE_IMPORT: {:4f}".format(time.time() - old_time))
            if sp.poll() is not None:
                ret_stdout, ret_stderr=sp.communicate()
                self.__pmess("ECLIPSE_IMPORT:retcode>{0}".format(str(sp.returncode)),lastmess=True)
                return (sp.returncode, ret_stdout, ret_stderr)

        # timeout
        if sp.returncode is None:
            #glogger.error("Timeout")
            sp.kill()
            ret_stdout, ret_stderr = sp.communicate()
            ##glogger.error("[eclipse_import]:"+"returncode:"+sp.returncode+"stdout: "+ret_stdout+" stderr:"+ret_stderr)
            #if sp.returncode == 13 >>  Application "org.eclipse.cdt.managedbuilder.core.headlessbuild" could not be found in the registry
            self.__smess("[eclipse_import]:"+"returncode:"+sp.returncode+"stdout: "+ret_stdout+" stderr:"+ret_stderr, \
                         self.STATUS_LEVEL_ERROR)
            return (sp.returncode+100, ret_stdout, ret_stderr)



    def build2(self, projects_build_conf, cleanbuild=False, timeout_sec=1200):
        """Projects build in the same order as we pass to eclipse_task's konstructor #list_eclipse_project"""

        cmd_build = self.eclipse_path + " "
        cmd_build += "-data " + self.workspace + " "
        cmd_build += eclipse_tasks.__base_params + " "
        cmd_build += eclipse_tasks.__ec_hlb_cmd + " "


        buildtype = " -build "
        if cleanbuild:
            buildtype = " -cleanBuild "

        for prj in self.list_eclipse_project:
            prj_bld=prj.project_name+"/"+projects_build_conf

            cmd_build_project=cmd_build+buildtype+'"'+prj_bld+'"'+" "

            cmd_glob = " "
            for key in self.global_eclipse_project.keys():
                if self.global_eclipse_project[key] is not None:
                    cmd_glob = " ".join(self.global_eclipse_project[key])

            cmd_build_project += " " + cmd_glob

            args = shlex.split(cmd_build_project)
            # glogger.info(args)
            self.__smess(args, self.STATUS_LEVEL_INFO)
            sp = subprocess.Popen(args)

            old_time = time.time()
            time_s = 0;
            it = 0.1;
            while (time.time() - old_time) < timeout_sec:
                it += 0.2;
                time_s = (0.5 + (it * it * 0.000625) / 1000)
                time.sleep(time_s)

                # glogger.info("building: {:4f}".format(time.time() - old_time))
                self.__pmess("ECLIPSE_BUILD[{0}]: {1:4f}".format(prj.project_name, time.time() - old_time))
                if sp.poll() is not None:
                    #process finished, check retlevel

                    if self.list_eclipse_project[len(self.list_eclipse_project)-1].project_name != prj.project_name:
                        self.__pmess("ECLIPSE_BUILD[{0}]\t\t:retcode>{1}\n\n".format(prj.project_name, str(sp.returncode)),lastmess=True)
                    else:
                        self.__pmess("ECLIPSE_BUILD[{0}]:\t\tretcode>{1}".format(prj.project_name, str(sp.returncode)),
                                     lastmess=True)

                    if sp.returncode == 1:
                        #ok
                        #eclipse usually return 1 not 0 in case of build success and some warnings
                        break
                    else:
                        #error
                        return sp.returncode

        self.progresshandler('\x1b[80D\x1b[1A\x1b[K')
        return 1


    def build_old(self, projects_build_conf, cleanbuild=True, timeout_sec=1200):
        cmd_build = self.eclipse_path + " "
        cmd_build += "-data " + self.workspace + " "
        cmd_build += eclipse_tasks.__base_params + " "
        cmd_build += eclipse_tasks.__ec_hlb_cmd + " "
        cmd_projects = ""
        
        buildtype=" -build "
        if cleanbuild:
            buildtype=" -cleanBuild "
        
        for prj in self.list_eclipse_project:
            prj_bld=prj.project_name+"/"+projects_build_conf
            cmd_projects+=buildtype+'"'+prj_bld+'"'+" "
            
        cmd_build += cmd_projects
        
        cmd_glob=" "
        for key in self.global_eclipse_project.keys():
            if self.global_eclipse_project[key] is not None:
                cmd_glob=" ".join(self.global_eclipse_project[key])

        cmd_build+=" "+cmd_glob
        
        args = shlex.split(cmd_build)
        #glogger.info(args)
        self.__smess(args, self.STATUS_LEVEL_INFO)
        sp = subprocess.Popen(args)
        
        old_time=time.time()
        time_s=0;it=0.1;
        while (time.time() - old_time) < timeout_sec:
            it += 0.5;time_s = (1.5 + ( it * it * 0.000625 ) / 1000)
            time.sleep(time_s)

            #glogger.info("building: {:4f}".format(time.time() - old_time))
            self.__pmess("ECLIPSE_BUILD: {:4f}".format(time.time() - old_time))
            if sp.poll() is not None:
                ret_stdout, ret_stderr=sp.communicate()
                return (sp.returncode, ret_stdout, ret_stderr)

        # timeout
        if sp.returncode is None:
            #glogger.error("Timeout")
            sp.kill()
            ret_stdout, ret_stderr = sp.communicate()
            return (sp.returncode, ret_stdout, ret_stderr)

    #no need to since parallel make partially solve it ....
    #def __spawn_ps(self,cmd, mtx):
        #sp = subprocess.Popen(args)
        #Process(target=self.__spawn_ps(cmd_import,mtx),name="import2ws")
        #sp.communicate()
        #args = shlex.split(cmd)
        #mtx.acquire()
        #sp = subprocess.Popen(args)
        #sp.
        #mtx.release()

    def __new_proc(self):
        pass

    # {ec} -nosplash -data $_ws -application org.eclipse.cdt.managedbuilder.core.headlessbuild -importAll


#delete no-workspace-related paths
#delete absolute path
# ${workspace_loc:/xxx}

