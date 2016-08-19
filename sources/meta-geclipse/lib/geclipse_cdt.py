#! /usr/bin/python2.7
#
# This module provides support for the Eclipse CDT project
# in Yocto/Poky/OpenEmbedded build system
#
# Copyright (C) 2016  Andrys Jiri (andrys.jiri+project_yoctogeclipse@gmail.com)
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
"""This module provides support for Eclipse's CDT project file in Yocto/Poky/OpenEmbedded build system.

The current version 0.1 is considered as alpha version.
Parse and modify Eclipse's CDT project file(.project), not all options of CDT are supported.
Constructors in this module are called from geclipse class,
calling them directly from another classes have not been tested.
"""

__all__ = ["eclipse_language_file", "build_config"]
__version__ = 0.1
__date__ = '2016-07-03'
__updated__ = '2016-08-14'

import os
#import sys
#import xml.etree.ElementTree as ET
import xml.dom.minidom as MD
import logging
import subprocess
#import multiprocessing
#from multiprocessing import Process
#import shlex
#import time
import random

def __dom_find2(dom, path, bubble_index=0):

        ret_lst = []
        from_root_flg = False
        if path[0] == "." and path[1] == "/":
            from_root_flg = True
            path = path[2:]
        tag_path_arr = path.split("/")
        ## cconfiguration/storageModule/externalSettings/externalSetting
        #time.sleep(0.1)
        while (bubble_index) < len(tag_path_arr):
            found_tag_root = dom.getElementsByTagName(tag_path_arr[bubble_index])
            print "ROOT(len:" + str(len(found_tag_root)) +"; i:" +str(bubble_index) + ") " + tag_path_arr[bubble_index]

            for node in found_tag_root:
                #time.sleep(0.1)
                print " + " + str(node.tagName)
                fnd_node=dom_find(node, path, bubble_index+1)
                if (bubble_index+1)==len(tag_path_arr):
                    print "!!!!" + str(node.attributes["id"].value)
                #if fnd_node is not None:
                #    nodes_list.append(fnd_node)
                #node.dom.getElementsByTagName(tag_path_arr[bubble_index])
            return None
        return None


def get_attribute_value(node, key):
    """Check if node includes attributes and return attribute value

    :param node: Object Node of xml.dom.minidom
    :param key:  String, attribute Key
    :return:     Attribute value or None
    """
    if node.nodeType != MD.Element.ELEMENT_NODE:
        return None
    try:
        value = node.attributes[key].value
    except Exception, e:
        return None
    else:
        return value

def get_tag_name(node):
    """Check if node is having tagName

    :param node: Object Node of xml.dom.minidom
    :return:     node.tagName or None
    """
    try:
        if node.nodeType == MD.Element.ELEMENT_NODE:
            value = node.tagName
        else:
            return None
    except Exception, e:
        return None
    else:
        return value


def dom_find_attributes(dom, attribute_key, attribute_val=None, find_attribute_substring=True):
    """ Find attributes in dom tree,
    bubble from root level to down, allows also partial match attribute of value by setting #find_attribute_substring.
    TODO:This function will be replace it to more generic dom_find()

    :param dom:                         Node of xml.dom.minidom instance
    :param attribute_key:               Attribute key where we wanna find something
    :param attribute_val:               Attribute value
    :param find_attribute_substring:    If True allows to find partial matches of attribute value
    :return:                            Return list of xml.dom.minidom Nodes
    """

    ret_lst=[]

    if not dom.hasChildNodes():
        return None

    chlds = dom.childNodes

    for node in chlds:
        #time.sleep(0.1)
        #print " + " + str(node.nodeType)

        if node.nodeType == MD.Element.ELEMENT_NODE:
            tmp_attr_val=get_attribute_value(node, attribute_key)
            if tmp_attr_val is not None:
                if attribute_val is None:
                    #print " + " + str(tmp_attr_val)
                    ret_lst.append(node)
                else:
                    if find_attribute_substring:
                        if tmp_attr_val.find(attribute_val)>-1:
                            #print " + " + str(tmp_attr_val)
                            ret_lst.append(node)
                    else:
                        if tmp_attr_val==attribute_val :
                            #print " + " + str(tmp_attr_val)
                            ret_lst.append(node)

            fnd_node=dom_find_attributes(node, attribute_key, attribute_val, find_attribute_substring)
            if fnd_node is not None:
                for ret_node_with_attr in fnd_node:
                    ret_lst.append(ret_node_with_attr)

    if ret_lst is not None:
        return ret_lst

    return None


def dom_find(dom, path, attributes_list=None, attribute_value_partial_match=False):
        """ Find Xmlpath with/without attributes in dom tree,
        bubble from root level to down, allows also partial match attribute of value by setting #find_attribute_substring.

        :param dom:                             Node of xml.dom.minidom instance
        :param path:                            The xmlPath with or without attributes "toolChain/tool/option[@valueType=definedSymbols, @superClass=c.compiler.option.preprocessor]"
        :param attributes_list:                 List of attributes
        :param attribute_value_partial_match:   If True allows to find partial matches of attribute value
        :return:                                Return list of xml.dom.minidom Nodes


        1)find attribute values in logical "AND" relation:
            [@atttribute=attrib_value, @atttribute=attrib_value]

        2)find attribute keys; attributes in logical "AND" relation:
            [@atttribute, @atttribute]

        3)find attributes keys and values
            [@id,@bordel,@trash="tH"]

        We could not find tag starting from root, if root structure looks like
        "cconfiguration/storageModule/externalSettings/externalSetting" and root of it is cconfiguration, then
        we have to set path to storageModule/externalSettings/externalSetting
        """

        ret_lst = []
        from_root_flg = False
        lst_node_attributes = None

        if path[0] == "." and path[1] == "/":
            from_root_flg = True
            path = path[2:]


        def _check_all_attributes(node):
            for lst_node_attribute in lst_node_attributes:
                if lst_node_attribute["key"] in node.attributes.keys():
                    #key exist
                    if lst_node_attribute["value"] is None:
                        pass
                    else:
                        #print lst_node_attribute["value"].strip('"')
                        #print node.attributes[lst_node_attribute["key"]].value
                        if not attribute_value_partial_match:
                            if lst_node_attribute["value"] != node.attributes[lst_node_attribute["key"]].value:
                                return False
                        else:
                            if not node.attributes[lst_node_attribute["key"]].value.find(lst_node_attribute["value"])>-1:
                                return False
                else:
                    return False
            return True


        def _attributes_parse(attributes_string):
            cut_path = None
            att_l_b = attributes_string.find("[")
            att_l_e = attributes_string.find("]")
            lst_attributes = []

            if att_l_b > -1:
                tmp = [attr.strip().strip("@") for attr in attributes_string[att_l_b + 1:att_l_e].strip().split(",")]
                if len(tmp) > 0:
                    for attr in tmp:
                        if attr.find("=") > -1:
                            key = attr[:attr.find("=")]
                            value = attr[attr.find("=") + 1:].strip('"')
                        else:
                            key = attr[:]
                            value = None
                        lst_attributes.append({"key": key, "value": value})

                # print "attr : " + str(lst_node_attributes)]
                return lst_attributes
            else:
                return None

        path=path.strip()
        tag2find = path.split("/")[0]
        #root/tag1/tag2[@atttribute=attrib_value, @atttribute=attrib_value]
        if path.find("/")>-1:
            cut_path = "/".join(path.split("/")[1:])
        else:
            #last node in path
            cut_path=None
            # Latest node in path could also include attributes, therefore we need to clear last node name from path
            att_l_b = tag2find.find("[")
            if att_l_b > -1:
                lst_node_attributes=_attributes_parse(tag2find)
                tag2find = tag2find[:att_l_b]

            if attributes_list is not None:
                if lst_node_attributes is not None:
                    for attribute in attributes_list:
                        lst_node_attributes.append(attribute)
                else:
                    #same format in both lists>list of dictionary:
                    # [{"key":attribute_key,"value":attribute_value},{"key":attribute_key,"value":attribute_value}]
                    lst_node_attributes=attributes_list

        #time.sleep(0.1)
        found_tag_root = dom.getElementsByTagName(tag2find)

        for node in found_tag_root:
            #time.sleep(0.1)
            #print " + " + str(node.tagName)

            if cut_path is None:

                if lst_node_attributes is None:
                    #print "!!!!" + str(node.attributes["id"].value)
                    ret_lst.append(node)
                else:
                    if _check_all_attributes(node):
                        #print "!!!!" + str(node.attributes["id"].value)
                        ret_lst.append(node)

            else:
                fnd_node = dom_find(node, cut_path, attributes_list,attribute_value_partial_match)
                if fnd_node is not None:
                    for node in fnd_node:
                        ret_lst.append(node)

        if len(ret_lst)>0:
            return ret_lst

        return []


class build_config(object):
    """Public "modification-class", parse/modify/create build configuration.
    Constructor is called by eclipse_language_file class.
    In feature could be transferred to different class or renamed.
    """
    LNG_FILE_BACKUP=".cproject_orig"

    def __init__(self, dom_xmldoc, dom_node_orig_cconfig, orig_build_config_name, new_build_config_name):
        """Constructor is called by eclipse_language_file class.

        :param dom_xmldoc:              Document Node > xml.dom.minidom.parseString(xml_alltxtdata)
                                                    expatbuilder.parseString(string)
        :param dom_node_orig_cconfig:   Node of xml.dom.minidom pointing to Configuration Node
        :param orig_build_config_name:  Current Build Configuration name
        :param new_build_config_name:   New Build Configuration name
        """

        tmp = dom_node_orig_cconfig.attributes["id"].value

        self.build_parameters={"buildPath":'${workspace_loc}/${ProjName}/${ConfigName}'}
        self._err_exceptioninfo = None
        self.bc_err = {"errno": None, "errinfo": None, "exceptioninfo": None}

        self.bc_orig_dom_xmldoc = dom_xmldoc
        self.bc_orig_name = orig_build_config_name

        # "1333901317.961804378"
        self.bc_orig_id_num = ".".join([tpl for tpl in tmp.split(".") if tpl.isdigit()])

        # "org.eclipse.linuxtools.cdt.autotools.core.configuration.build.1333901317.961804378"
        self.bc_orig_id = tmp

        self.bc_new_name = new_build_config_name
        self.bc_new_node_cconf_cpy = dom_node_orig_cconfig.cloneNode(True)
        #print self.bc_new_node_cconf_cpy.toxml()

        self.bc_new_id_num = self.__gen_id(10)
        self.__modify_template_name_ids()
        #self.set_build_variable("ROOTFS","${YOCTOPATH}")
        #self.set_build_variable("ROOTFS2", "${YOCTOPATH}2")
        #self.set_build_variable("ROOTFS", "SRACKA")
        #self.delete_all_build_variables()
        #self.set_compiler_command("compiler")
        #self.set_linker_command("linker")
        #self.set_assembler_command("assembler")
        #self.set_linker_libname("JMENO")
        #self.set_linker_libname("JMENO2")
        #self.set_linker_libname("JMENO2qww")
        #self.set_linker_libpath("/yocto_directories")
        #self.set_linker_libpath("/yocto_directories2")
        #self.set_compiler_includepath("sysroot_treba")
        #self.set_compiler_includepath("sysroot_2treba")
        #self.set_post_build_command("cp -f ${workspace_loc}/${ProjName}/${ConfigName}/*.so ${HOME}")
        #self.set_define("IamAlmostSureThatSomebodyFkitup")
        #print self.bc_new_node_cconf_cpy.toxml()
        #self.delete_all_build_variables()
        #print self.bc_new_node_cconf_cpy.toxml()
        # cconfiguration/storageModule/externalSettings/externalSetting
        #print self.bc_new_node_cconf_cpy.toxml()
        # cconf_list = dom.getElementsByTagName("cconfiguration")

    def _create_element(self, node, tag_name, attributes ):
        if node.hasChildNodes():
            gaps = len(node.childNodes[0].data.strip("\n").split("\t"))
        else:
            tb_cnt=2
            tmp = node.parentNode
            while True:
                tb_cnt+=2
                tmp=tmp.parentNode
                up_tmp = tmp.nextSibling
                while up_tmp is not None:
                    if up_tmp.nodeType == MD.Element.TEXT_NODE:
                        gaps = len(up_tmp.data.strip("\n").split("\t"))+tb_cnt
                        break
                    up_tmp = tmp.nextSibling
                break

            #MD.Element.parentNode
        txt_node_bf = self.bc_orig_dom_xmldoc.createTextNode("\t")
        txt_node_nl = self.bc_orig_dom_xmldoc.createTextNode("\n")
        txt_node_nl2 = self.bc_orig_dom_xmldoc.createTextNode("\n"+(gaps-1)*"\t")
        txt_node_g = self.bc_orig_dom_xmldoc.createTextNode((gaps-2)*"\t")
        tag = self.bc_orig_dom_xmldoc.createElement(tag_name)

        for attrib in attributes:
            tag.setAttribute(attrib["key"], attrib["value"])

        if not node.hasChildNodes():
            #in case of node like <bla\> only
            node.appendChild(txt_node_nl2)

        node.appendChild(txt_node_bf)
        node.appendChild(tag)
        node.appendChild(txt_node_nl)
        node.appendChild(txt_node_g)

    def set_post_build_command(self, post_build_command):
        """Set/rewrite post build command.

        :param post_build_command:
        :return:
        """
        SEARCH_PATH = "storageModule/configuration[@buildProperties, @name, @parent]"
        conf = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH)
        conf[0].setAttribute("postbuildStep", post_build_command)


    def set_enable_parallel_build(self):
        """Set/Enable parallel build"""

        # parallelBuildOn = "true", parallelizationNumber = "optimal"
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/builder"
        builder = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH)
        builder[0].setAttribute("parallelBuildOn", "true")
        builder[0].setAttribute("parallelizationNumber", "optimal")

    def set_build_make_parameters(self,make_parameters="all"):
        """Set/rewrite make parameter for build.

        :param make_parameters: String which identify build target or parameters in make files
        :return:
        """
        #make all
        #make clean
        #make make_parameters
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/builder"
        builder = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH)
        builder[0].setAttribute("incrementalBuildTarget", make_parameters)
        #if builder["superClass"].find("org.eclipse.cdt.build.core.settings")>-1:
        #    builder[0].setAttribute("enabledIncrementalBuild", "true")

    def set_define(self, preprocessor_define_name):
        """Set/add define to build configuration.

        :param preprocessor_define_name: String, preprocessor define
        :return:
        """

        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=definedSymbols, @superClass=c.compiler.option.preprocessor]"

        option_child_of_cdt_managedbuild_tool_gnu_c_compiler = {
            "id": "gnu.c.compiler.option.preprocessor.def.symbols.XXXXYYYY", "name": "Defined symbols (-D)",
            "superClass": "gnu.c.compiler.option.preprocessor.def.symbols", "valueType": "definedSymbols"
            }
        tool_0 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_compiler,
            "attribute_value_partial_match": True
            }

        option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler = option_child_of_cdt_managedbuild_tool_gnu_c_compiler

        tool_1 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler,
            "attribute_value_partial_match": True
            }

        TOOL_TYPES_LIST = [tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            # block does not exist,create option block + inner lib settings
            for tool in TOOL_TYPES_LIST:
                dom_tool = dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                    attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    # id generation
                    attributes = []
                    id_num = self.__gen_id_alsofrom_new_cconf(10)
                    new_id = tool["child_option_attributes"]["id"][
                             :tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"] = new_id
                    for attr_key in tool["child_option_attributes"]:
                        attributes.append({"key": attr_key, "value": tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)
                    option_node = dom_find(dom_tool[0], "option[@id=" + id_num + "]",
                                           attribute_value_partial_match=True)
                    attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": preprocessor_define_name}]
                    tag_name = "listOptionValue"
                    # print option_node[0].toxml()
                    self._create_element(option_node[0], tag_name, attributes)

        else:
            attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": preprocessor_define_name}]
            tag_name = "listOptionValue"
            self._create_element(options[0], tag_name, attributes)

    def set_compiler_sharedlib_other_flags(self, add_cflags):
        """Set/rewrite CFLAGS

        :param add_cflags: CFLAGS
        :return:
        """
        SEARCH_PATH = "storageModule/configuration[@buildArtefactType=sharedLib]"
        #test if this is shared lib
        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        #print len(options)
        #os.sys.exit(1)
        if len(options) > 0:
            self.set_compiler_other_flags(add_cflags)


    #set/add other_flags
    def set_compiler_other_flags(self,add_cflags):
        """Set/rewrite CFLAGS

        :param add_cflags: CFLAGS
        :return:
        """
        #no need to create new tag just read value and add new value to attribute in case that search path return non zero lenght
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=string, @superClass=c.compiler.option.misc.other]"
        #in case of gcc option does not exist we need to add "-c -fmessage-length=0" to value
        #<option id="gnu.c.compiler.option.misc.other.XXXXYYYY" superClass="gnu.c.compiler.option.misc.other" value="-c -fmessage-length=0 AOCHR_OTHER_FLAGS" valueType="string"/>

        if not len(add_cflags) > 1:
            return

        option_child_of_cdt_managedbuild_tool_gnu_c_compiler = {
            "id": "gnu.c.compiler.option.misc.other.XXXXYYYY",
            "superClass": "gnu.c.compiler.option.misc.other", "valueType": "string",
            "value":"-c -fmessage-length=0  "
        }
        tool_0 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_compiler,
            "attribute_value_partial_match": True
            }

        option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler = {
            "id": "gnu.c.compiler.option.misc.other.XXXXYYYY",
            "superClass": "gnu.c.compiler.option.misc.other", "valueType": "string",
            "value":"-c -fmessage-length=0  "
        }
        tool_1 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler,
            "attribute_value_partial_match": True
            }

        TOOL_TYPES_LIST = [tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            # block does not exist,create option block + set value
            for tool in TOOL_TYPES_LIST:
                dom_tool = dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                    attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    # id generation
                    attributes = []
                    id_num = self.__gen_id_alsofrom_new_cconf(10)
                    new_id = tool["child_option_attributes"]["id"][
                             :tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"] = new_id
                    for attr_key in tool["child_option_attributes"]:
                        if attr_key == "value":
                            tool["child_option_attributes"][attr_key]=tool["child_option_attributes"][attr_key]+add_cflags
                        attributes.append({"key": attr_key, "value": tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)

        else:
            #option exist
            value_attribute__value = options[0].attributes["value"].value
            options[0].setAttribute("value", value_attribute__value + " "+add_cflags)

    def delete_all_non_workspace_related_includepaths(self):
        """Delete all non-workspace-related-include paths(-I).
        This is workspace related path: ${workspace_loc:/xxx}

        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=includePath, @superClass=c.compiler.option.include.paths]"
        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        #sm = dom_find(self.bc_new_node_cconf_cpy, "listOptionValue")
        if len(options) > 0:
            if options[0].hasChildNodes():
                chlds=options[0].childNodes
                for chld in chlds:
                    if get_attribute_value(chld,"value") != None and not str(get_attribute_value(chld,"value")).find(':/')>-1:
                        chld.parentNode.removeChild(chld)

    def set_compiler_includepath(self, include_search_path):
        """Set/add includes directory CFLAGS (-I) $include_search_path.

        :param include_search_path: Includes directory
        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=includePath, @superClass=c.compiler.option.include.paths]"

        option_child_of_cdt_managedbuild_tool_gnu_c_compiler = {
            "id": "gnu.c.compiler.option.include.paths.XXXXYYYY", "name": "Include paths (-I)",
            "superClass": "gnu.c.compiler.option.include.paths", "valueType": "includePath"
        }
        tool_0 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_compiler,
            "attribute_value_partial_match": True
            }

        option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler = option_child_of_cdt_managedbuild_tool_gnu_c_compiler

        tool_1 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.compiler]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_compiler,
            "attribute_value_partial_match": True
            }

        TOOL_TYPES_LIST = [tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            # block does not exist,create option block + inner lib settings
            for tool in TOOL_TYPES_LIST:
                dom_tool = dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                    attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    # id generation
                    attributes = []
                    id_num = self.__gen_id_alsofrom_new_cconf(10)
                    new_id = tool["child_option_attributes"]["id"][
                             :tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"] = new_id
                    for attr_key in tool["child_option_attributes"]:
                        attributes.append({"key": attr_key, "value": tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)
                    option_node = dom_find(dom_tool[0], "option[@id=" + id_num + "]",
                                           attribute_value_partial_match=True)
                    attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": include_search_path}]
                    tag_name = "listOptionValue"
                    # print option_node[0].toxml()
                    self._create_element(option_node[0], tag_name, attributes)

        else:
            attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": include_search_path}]
            tag_name = "listOptionValue"
            self._create_element(options[0], tag_name, attributes)



    def set_linker_flags(self, add_ldflags):
        """Set/add LDFLAGS

        :param add_ldflags: LDFLAGS
        :return:
        """
        # <option id="gnu.c.link.option.ldflags.1477488763" name="Linker flags" superClass="gnu.c.link.option.ldflags" value="-Wl,-Map=${ProjName}.map" valueType="string"/>
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=string, @superClass=c.link.option.ldflags]"

        if not len(add_ldflags) > 1:
            return

        option_child_of_cdt_managedbuild_tool_gnu_c_linker = {
            "id": "gnu.c.link.option.ldflags.XXXXYYYY", "name":"Linker flags",
            "superClass": "gnu.c.link.option.ldflags", "valueType": "string", "value":""
        }
        tool_0 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.linker]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_linker,
            "attribute_value_partial_match": True
            }

        option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker = option_child_of_cdt_managedbuild_tool_gnu_c_linker
        tool_1 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.linker]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker,
            "attribute_value_partial_match": True
            }

        TOOL_TYPES_LIST = [tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            # block does not exist,create option block + set value
            for tool in TOOL_TYPES_LIST:
                dom_tool = dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                    attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    # id generation
                    attributes = []
                    id_num = self.__gen_id_alsofrom_new_cconf(10)
                    new_id = tool["child_option_attributes"]["id"][
                             :tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"] = new_id
                    for attr_key in tool["child_option_attributes"]:
                        if attr_key == "value":
                            tool["child_option_attributes"][attr_key]=tool["child_option_attributes"][attr_key]+add_ldflags
                        attributes.append({"key": attr_key, "value": tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)

        else:
            #option exist
            value_attribute__value = options[0].attributes["value"].value
            options[0].setAttribute("value", value_attribute__value + " "+add_ldflags)

    def delete_all_non_workspace_related_libpaths(self):
        """Delete all non-workspace-related-library paths(-L).
        This is workspace related path: ${workspace_loc:/xxx}

        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=libPaths, @superClass=c.link.option.paths]"
        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        # sm = dom_find(self.bc_new_node_cconf_cpy, "listOptionValue")
        if len(options) > 0:
            if options[0].hasChildNodes():
                chlds = options[0].childNodes
                for chld in chlds:
                    if get_attribute_value(chld, "value") != None and \
                            not str(get_attribute_value(chld, "value")).find(':/') > -1:
                        chld.parentNode.removeChild(chld)



    #set/add linker paths
    def set_linker_libpath(self, lib_search_path):
        """Set/add library paths CFLAGS (-L).

        :param lib_search_path: Libraries directory
        :return:
        """

        SEARCH_PATH  = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=libPaths, @superClass=c.link.option.paths]"

        option_child_of_cdt_managedbuild_tool_gnu_c_linker = {
            "id": "gnu.c.link.option.paths.XXXXYYYY", "name": "Library search path (-L)",
            "superClass": "gnu.c.link.option.paths", "valueType": "libPaths"
        }
        tool_0 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.linker]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_linker,
            "attribute_value_partial_match": True
            }
        option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker = option_child_of_cdt_managedbuild_tool_gnu_c_linker

        tool_1 = {
            "path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.linker]",
            "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker,
            "attribute_value_partial_match": True
            }
        TOOL_TYPES_LIST = [tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            # block does not exist,create option block + inner lib settings
            for tool in TOOL_TYPES_LIST:
                dom_tool = dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                    attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    # id generation
                    attributes = []
                    id_num = self.__gen_id_alsofrom_new_cconf(10)
                    new_id = tool["child_option_attributes"]["id"][
                             :tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"] = new_id
                    for attr_key in tool["child_option_attributes"]:
                        attributes.append({"key": attr_key, "value": tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)
                    option_node = dom_find(dom_tool[0], "option[@id=" + id_num + "]",
                                           attribute_value_partial_match=True)
                    attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": lib_search_path}]
                    tag_name = "listOptionValue"
                    # print option_node[0].toxml()
                    self._create_element(option_node[0], tag_name, attributes)

        else:
            attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": lib_search_path}]
            tag_name = "listOptionValue"
            self._create_element(options[0], tag_name, attributes)

    # set/add lib for linker
    def set_linker_libname(self, lib_name):
        """Set/add library name to build configuration CFLAGS (-l)

        :param lib_name: Library name
        :return:
        """
        SEARCH_PATH  = "storageModule/configuration/folderInfo/toolChain/tool/option[@valueType=libs, @superClass=c.link.option.libs]"

        option_child_of_cdt_managedbuild_tool_gnu_c_linker = {
            "id": "gnu.c.link.option.libs.XXXXYYYY", "name": "Libraries (-l)",
            "superClass": "gnu.c.link.option.libs", "valueType": "libs"
        }

        tool_0 = {"path": "storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.c.linker]",
                  "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_c_linker,
                  "attribute_value_partial_match": True
                  }

        option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker = option_child_of_cdt_managedbuild_tool_gnu_c_linker

        tool_1 = {"path":"storageModule/configuration/folderInfo/toolChain/tool[@superClass=cdt.managedbuild.tool.gnu.cross.c.linker]",
                  "child_option_attributes": option_child_of_cdt_managedbuild_tool_gnu_cross_c_linker,
                  "attribute_value_partial_match": True
                  }
        #{
        # "parent_tool_partialSuperClass":"cdt.managedbuild.tool.gnu.c.linker",
        # "child_option_attributes":option_child_of_cdt_managedbuild_tool_gnu_c_linker
        # }
        TOOL_TYPES_LIST=[tool_0, tool_1]

        options = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        if len(options) == 0:
            #block does not exist,create option block + inner lib settings
            for tool in TOOL_TYPES_LIST:
                dom_tool=dom_find(self.bc_new_node_cconf_cpy, tool["path"],
                                  attribute_value_partial_match=tool["attribute_value_partial_match"])
                if len(dom_tool) != 0:
                    #id generation
                    attributes=[]
                    id_num=self.__gen_id_alsofrom_new_cconf(10)
                    new_id=tool["child_option_attributes"]["id"][:tool["child_option_attributes"]["id"].find("XXXXYYYY")] + str(id_num)
                    tool["child_option_attributes"]["id"]=new_id
                    for attr_key in tool["child_option_attributes"]:
                        attributes.append({"key":attr_key, "value":tool["child_option_attributes"][attr_key]})
                    tag_name = "option"
                    self._create_element(dom_tool[0], tag_name, attributes)
                    option_node=dom_find(dom_tool[0],"option[@id="+id_num+"]",attribute_value_partial_match=True)
                    attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": lib_name}]
                    tag_name = "listOptionValue"
                    #print option_node[0].toxml()
                    self._create_element(option_node[0], tag_name, attributes)

        else:
            attributes = [{"key": 'builtIn', "value": "false"}, {"key": 'value', "value": lib_name}]
            tag_name="listOptionValue"
            self._create_element(options[0],tag_name,attributes)

    def set_compiler_command(self, command_ccompiler):
        """Set/rewrite compiler command(gcc).

        :param command_ccompiler: Compiler command(gcc)
        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool[@superClass=c.compiler]"
        tools = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH,attribute_value_partial_match=True)
        #"valueType"{definedSymbols}
        for nd in tools:
            if not "valueType" in nd.attributes.keys():
                nd.setAttribute('command', command_ccompiler)

    def set_linker_command(self, command_linker):
        """Set/rewrite linker command(ldd/gcc).

        :param command_linker:
        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool[@superClass=c.linker]"
        tools = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        for nd in tools:
                nd.setAttribute('command', command_linker)

    def set_assembler_command(self, command_assembler):
        """Set/rewrite assembler command(as).

        :param command_assembler:
        :return:
        """
        SEARCH_PATH = "storageModule/configuration/folderInfo/toolChain/tool[@superClass=assembler]"
        tools = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH, attribute_value_partial_match=True)
        for nd in tools:
                nd.setAttribute('command', command_assembler)

    def delete_all_build_variables(self):
        """Delete all build variables in build configuration.

        :return:
        """
        SEARCH_PATH = "storageModule/macros"
        sm = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH)
        if len(sm) > 0:
            sm[0].parentNode.removeChild(sm[0])

    def set_build_variable(self, var_name, var_value):
        """Set/Add/modify build variable in build configuration.

        :param var_name:
        :param var_value:
        :return:
        """
        #create/modify/add build variables

        SEARCH_PATH="storageModule[@buildSystemId=org.eclipse.cdt.managedbuilder.core.configurationDataProvider]"
        #SEARCH_PATH2 = "storageModule/macros/stringMacro[@name={0}]".format(var_name)
        SEARCH_PATH2 = "storageModule/macros"
        SEARCH_PATH3 = "storageModule/macros/stringMacro[@name={}]".format(var_name)

        def add_macros_block():
            sm = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH)
            if len(sm) != 0:
                if sm[0].childNodes[0].nodeType == MD.Node.TEXT_NODE:
                    gaps = sm[0].childNodes[0].data.strip("\n")
                else:
                    gaps = "\t"
            else:
                raise UserWarning("Weird format of project file")

            SECTION_BUILD_VARIABLES = "<macros>\n{3}\t<stringMacro name=\"{0}\" type=\"{1}\" value=\"{2}\"/>\n{3}</macros>\n\n".format(
                var_name, "VALUE_PATH_ANY", var_value, gaps)
            txt_node_bf = self.bc_orig_dom_xmldoc.createTextNode("\t")
            txt_node_nl = self.bc_orig_dom_xmldoc.createTextNode("\n")
            txt_node_g = self.bc_orig_dom_xmldoc.createTextNode((len(gaps.split("\t"))-2)*"\t")
            build_vars_block=MD.parseString(SECTION_BUILD_VARIABLES).documentElement
            sm[0].appendChild(txt_node_bf)
            sm[0].appendChild(build_vars_block)
            sm[0].appendChild(txt_node_nl)
            sm[0].appendChild(txt_node_g)
        #print tmp[0].toxml()

        def add_build_var(ms):
            sm_dupl = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH3)
            if len(sm_dupl) !=0:
                #already build var already exist > rewrite value
                sm_dupl[0].setAttribute('value', var_value)
            else:
                gaps=ms.childNodes[0].data.strip("\n")
                txt_node_bf = self.bc_orig_dom_xmldoc.createTextNode("\t")
                txt_node_nl = self.bc_orig_dom_xmldoc.createTextNode("\n")
                txt_node_g = self.bc_orig_dom_xmldoc.createTextNode((len(gaps.split("\t")) - 2) * "\t")
                sm=self.bc_orig_dom_xmldoc.createElement("stringMacro")
                sm.setAttribute('name', var_name)
                sm.setAttribute('type', "VALUE_PATH_ANY")
                sm.setAttribute('value', var_value)
                ms.appendChild(txt_node_bf)
                ms.appendChild(sm)
                ms.appendChild(txt_node_nl)
                ms.appendChild(txt_node_g)

        #main
        macros = dom_find(self.bc_new_node_cconf_cpy, SEARCH_PATH2)
        if len(macros) == 0:
            add_macros_block()
        else:
            add_build_var(macros[0])



    def __modify_template_name_ids(self):
        #we wanna only modify cconfiguration and we only have cconfiguration, therefore value of id attribut is not needed
        _NAME_NODE_ATTRIBUTES=[{"key":"id","value":self.bc_orig_id},\
                               {"key":"moduleId","value":"org.eclipse.cdt.core.settings"},\
                               {"key":"buildSystemId", "value": "org.eclipse.cdt.managedbuilder.core.configurationDataProvider"},\
                               ]
        #self.bc_new_node_cconf_cpy
        #self.bc_orig_dom_xmldoc
        #self.bc_new_node_cconf_cpy

        #print self.bc_new_node_cconf_cpy.toxml()

        def add_new_ids(ids_value, new_id):
            #print "\nBLA:"+ ids_value[len(ids_value) - 1] + "BLA\n"
            if ids_value[len(ids_value)-1] == ".":
                return ids_value + new_id +"."
            else:
                return ids_value +"." + new_id

        def replace_id(ids_value, new_id):
        #return string wit new id value on none if id should not be replaced
            if ids_value[len(ids_value) - 1] == ".":
                lst_tmp=ids_value[:-1].split(".")
                if lst_tmp[-1].isdigit():
                    # id which have to be replaced by new one
                    return ".".join(lst_tmp[:-1])+"."+new_id+"."
                else:
                    return None
            else:
                lst_tmp=ids_value.split(".")
                if lst_tmp[-1].isdigit():
                    # id which have to be replaced by new one
                    return ".".join(lst_tmp[:-1])+"."+new_id
                else:
                    return None

        #print "\nold_id:"+self.bc_orig_id_num
        #print "new_id:"+self.bc_new_id_num +"\n"

        tmp=add_new_ids(self.bc_new_node_cconf_cpy.attributes["id"].value, self.bc_new_id_num)
        self.bc_new_node_cconf_cpy.setAttribute('id', tmp)

        name_node=dom_find(self.bc_new_node_cconf_cpy, 'storageModule', _NAME_NODE_ATTRIBUTES)

        name_node[0].setAttribute('name', self.bc_new_name)

        # add new project id to project related IDs
        all_prj_rel_nodes=dom_find_attributes(self.bc_new_node_cconf_cpy,
                                              "id", attribute_val=self.bc_orig_id_num,
                                              find_attribute_substring=True)
        for node in all_prj_rel_nodes:
            tmp=add_new_ids(node.attributes["id"].value, self.bc_new_id_num)
            node.setAttribute('id', tmp)

        #print "\n"
        #replace id number of all nodes AND not realted to project id, reeeally slow "motion-method"
        all_id_nodes = dom_find_attributes(self.bc_new_node_cconf_cpy, "id")
        new_id_list=[]
        new_id_list.append(self.bc_new_id_num)
        for node in all_id_nodes:
            # process only NOT project related ids
            if not node.attributes["id"].value.find(self.bc_new_id_num)>-1:
                new_id=self.__gen_id(10, new_id_list)
                new_id_list.append(new_id)
                node_id_val=node.attributes["id"].value
                #print node_id_val
                tmp=replace_id(node_id_val, new_id)
                if tmp is not None:
                    #print "  -REPLACE"
                    node.setAttribute('id', tmp)

        #additional modifications:
        #in case of default template buildPath is not set, and it have to be overwrited by new name of build-configuration
        # therefore we will set buildPath to "${workspace_loc}/${ProjName}/${ConfigName}"
        bp_node = dom_find(self.bc_new_node_cconf_cpy, 'storageModule/configuration/folderInfo/toolChain/builder')
        bp_node[0].setAttribute("buildPath", self.build_parameters["buildPath"])
        #orig       :  "${workspace_loc:/test}/build-CHILD_OF_RELEASE"
        #possible   : "${workspace_loc}/${ProjName}/${ConfigName}"
        #print bp_node[0].attributes["buildPath"].value

        conf_node = dom_find(self.bc_new_node_cconf_cpy,
                             "storageModule/configuration[@buildProperties, @name, @parent]")
        conf_node[0].setAttribute("name", self.bc_new_name)

        pths_nodes = dom_find(self.bc_new_node_cconf_cpy,
                             "storageModule/externalSettings/externalSetting/entry[@kind=Path, @name="+self.bc_orig_name+"]",
                              attribute_value_partial_match=True)
        for pth_node in pths_nodes:
            new_name=pth_node.attributes["name"].value.replace(self.bc_orig_name,self.bc_new_name)
            pth_node.setAttribute("name", new_name)



        #for chld_node in chld_nodes:
        #    print chld_node.getElementsByTagName(tag_path_arr[bubble_index])

    def __gen_id(self, nmbrOfdigits, skip_also_id_list=None):
        # nmbrOfdigits=3, min=100, max=999
        min = int("1" + "0" * (nmbrOfdigits - 1))
        max = int("9" * (nmbrOfdigits))

        rnd_num = str(random.randint(min, max))

        if skip_also_id_list is None:
            while self.bc_orig_dom_xmldoc.toxml().find(rnd_num) > -1:
                rnd_num = str(random.randint(min, max))
            return rnd_num
        else:
            while True:
                if rnd_num in skip_also_id_list:
                    rnd_num = str(random.randint(min, max))
                    continue
                if self.bc_orig_dom_xmldoc.toxml().find(rnd_num) > -1:
                    rnd_num = str(random.randint(min, max))
                    continue
                break
            return rnd_num

    def __gen_id_alsofrom_new_cconf(self,nmbrOfdigits):
        min = int("1" + "0" * (nmbrOfdigits - 1))
        max = int("9" * (nmbrOfdigits))

        rnd_num = str(random.randint(min, max))
        while True:
            if self.bc_orig_dom_xmldoc.toxml().find(rnd_num) > -1:
                rnd_num = str(random.randint(min, max))
                continue
            if self.bc_new_node_cconf_cpy.toxml().find(rnd_num) > -1:
                rnd_num = str(random.randint(min, max))
                continue
            return rnd_num


class eclipse_language_file(object):
    """
    Public language-related eclipse configuration class.
    Find/hold "build configuration" in self.bc and allows its modifications by #build_configuration class.

    Example:
        import geclipse_cdt

        plf="/home/MrTrampolina/tests/.cproject"

        eclf = eclipse_language_file(plf)
        eclf.new_build_config("Release", "imx6qdbl-cross-release")

        eclf.bc.delete_all_non_workspace_related_libpaths()
        eclf.bc.delete_all_non_workspace_related_includepaths()
        eclf.bc.set_enable_parallel_build()

        eclf.update_eclipse_file()

    """
    _FILE_ROOT_TAG_NAME_CDT = "cproject"
    _FILE_ROOT_TAG_NAME_PYDEV = "pydev_project"

    _LNG_FILE_TYPE_CDT = "org.eclipse.cdt"
    _LNG_FILE_TYPE_PYDEV = "org.python.pydev"

    # _SUPPORTED_LNG_FILE_TYPES={"root_tag1":CDT_PTR, "root_tag2":{{}}}
    # CDT_PTR={"root_attribute":_ROOT_ATTRIBUTE_CDT}
    # _ROOT_ATTRIBUTE_CDT={"name":name, "value":value}

    _ROOT_ATTRIBUTE_CDT = {"name": "storage_type_id", "value": "org.eclipse.cdt.core.XmlProjectDescriptionStorage"}
    _CDT_PTR = {"root_attribute": _ROOT_ATTRIBUTE_CDT, "lng_file_type": _LNG_FILE_TYPE_CDT}
    _SUPPORTED_LNG_FILE_TYPES = {_FILE_ROOT_TAG_NAME_CDT: _CDT_PTR}

    def __init__(self, eclipse_lang_file):
        """Load language-related-eclipse configuration file
         and fill self.lng_file_dom by Document Node > xml.dom.minidom.parseString(xml_alltxtdata)

        :param eclipse_lang_file: Path to .cproject file
        """
        self.lng_file = eclipse_lang_file
        self._err_exceptioninfo = None
        self.lng_file_err = {"errno": None, "errinfo": None, "exceptioninfo": None}
        self.lng_file_dom = None
        self.bc = None
        err, dom = self._get_xml_dom()
        if err != 0:
            raise UserWarning(self.geterr())

    def _get_xml_dom(self):
        """Parse  #lng_file file and return root of xml.dom.minidom,
        fill #self.lng_file_dom
        in case of error fill #self.lng_file_type

        #lng_file
                 is path to language related project file

        #return values
                This function should return list of two items
                    return [error_number, dom]

                    where,
                        #error_number           : integer value
                        #dom                    : object > xml.dom.minidom ()

                        if #error_number==0 -> OK,
                        if #error_number==1 -> NG, error project file does not exist
                        if #error_number==2 -> NG, error open/read project file
                        if #error_number==3 -> NG, error xml, format
                        if #error_number==4 -> NG, error xml, can not get root
                        if #error_number==5 -> NG, error unexpected tag of xml root
         """

        if os.path.isfile(self.lng_file):
            try:
                of = open(self.lng_file, "rt")
                xml_alltxtdata = of.read()
            except Exception, e:
                self._err_exceptioninfo = str(e.message)
                of.close()
                self.lng_file_err["errno"] = 2
                return [self.lng_file_err["errno"], None]
            else:
                try:
                    of.close()
                    dom = MD.parseString(xml_alltxtdata)

                except Exception, e:
                    self._err_exceptioninfo = str(e.message)
                    self.lng_file_err["errno"] = 3
                    return [self.lng_file_err["errno"], None]
                else:
                    if dom is not None:
                        root_node = dom.documentElement
                        if str(root_node.tagName) in self._SUPPORTED_LNG_FILE_TYPES:
                            supp_root_attribute_name = \
                            self._SUPPORTED_LNG_FILE_TYPES[str(root_node.tagName)]["root_attribute"]["name"]
                            supp_root_attribute_value = \
                            self._SUPPORTED_LNG_FILE_TYPES[str(root_node.tagName)]["root_attribute"]["value"]
                            try:
                                root_attribute_value = str(root_node.attributes[supp_root_attribute_name].value)
                            except Exception, e:
                                # unexpected tag of root
                                self._err_exceptioninfo = " XML_ROOT: " + root_attribute_value
                                self.lng_file_err["errno"] = 5
                                return [self.lng_file_err["errno"], None]
                            else:
                                if root_attribute_value == supp_root_attribute_value:
                                    self.lng_file_dom = dom
                                    return [0, self.lng_file_dom]
                        else:
                            # unexpected tag of root
                            self.lng_file_err["errno"] = 5
                            return [self.lng_file_err["errno"], None]
                    else:
                        # cannot get dom
                        self.lng_file_err["errno"] = 4
                        return [self.lng_file_err["errno"], None]
        else:
            # prj file not found
            self.lng_file_err["errno"] = 1
            return [self.lng_file_err["errno"], None]

    # def _dom_find(self,path):

    # def insert_after(self,):


    @staticmethod
    def __geterrdesc(errno):
        if errno == 0:
            return "It seems that everything is okeey, but who knows ...."
        elif errno == 1:
            return "Project file error, no such a file."
        elif errno == 2:
            return "Project file error, open/read file."
        elif errno == 3:
            return "Xml error, xml format."
        elif errno == 4:
            return "Xml error, can not get xml root."
        elif errno == 5:
            return "Xml error, unexpected tag of xml root."
        elif errno == 6:
            return "Build configuration was not found"

    def geterr(self):
        """Return all information about error"""

        if self.lng_file_err["errno"] is None:
            return None

        tmp = eclipse_language_file.__geterrdesc(self.lng_file_err["errno"])

        errmess = "Project file: " + self.lng_file + '\n'

        errmess += "  Error: " + '\n'
        errmess += "    Errno: " + str(self.lng_file_err["errno"]) + '\n'
        errmess += "    Errorinfo: " + tmp + '\n'
        if self._err_exceptioninfo is not None:
            errmess += "    XML: " + self._err_exceptioninfo + '\n'

        return errmess

    @staticmethod
    def __get_cconf(dom, build_config_str):
        # return only element node type 1
        cconf_list = dom.getElementsByTagName("cconfiguration")
        for cconf in cconf_list:
            #print cconf.attributes["id"].value
            for cconf_child_node in cconf.childNodes:
                if str(get_tag_name(cconf_child_node)) == "storageModule" and \
                                str(get_attribute_value(cconf_child_node,
                                                                              "moduleId")) == "org.eclipse.cdt.core.settings" and \
                                str(get_attribute_value(cconf_child_node,
                                                                              "name")) == build_config_str:
                    return [0, cconf]

        return [6, None]

    @staticmethod
    def __get_cconf_new(dom, build_config_str):
        pass

    def new_build_config(self, name_of_existing_build_configuration_str, name_of_new_build_configuration_str):
        """On base of current #name_of_existing_build_configuration_str create new #name_of_new_build_configuration_str
        and store new build configuration in self.bc.

        :param name_of_existing_build_configuration_str:    Current Build Configuration
        :param name_of_new_build_configuration_str:         New Build Configuration
        :return:
        """

        err, dom_cconf_node = self.__get_cconf(self.lng_file_dom, name_of_existing_build_configuration_str)
        if err != 0:
            self.lng_file_err["errno"] = err
            raise UserWarning(self.geterr())

        self.bc = build_config(self.lng_file_dom, dom_cconf_node, \
                               name_of_existing_build_configuration_str, name_of_new_build_configuration_str)

    def _just_to_be_sure_make_backup(self):
        #bla = time.localtime()
        #f_name="{0}{1}{2}_{3}{4}{5}_.cproject".format(bla[0], bla[1], bla[2], bla[3], bla[4], bla[5])
        f = open(os.path.dirname(self.lng_file)+"/"+build_config.LNG_FILE_BACKUP, "wb")
        self.lng_file_dom.writexml(f)

    def update_eclipse_file(self, lng_file_path=None):
        """In order to apply all changes made in new build configuration we have to call this method.

        :param lng_file_path:  For debug purposes only
        :return:
        """

        self._just_to_be_sure_make_backup()

        if lng_file_path is None:
            lng_file_path=self.lng_file

        SEARCH_PATH = "storageModule/cconfiguration[@id="+  self.bc.bc_orig_id+"]"
        cconf = dom_find(self.lng_file_dom, SEARCH_PATH)

        txt_node_bf = self.lng_file_dom.createTextNode("\n\t\t")
        cconf[0].parentNode.insertBefore(self.bc.bc_new_node_cconf_cpy, cconf[0].nextSibling)
        cconf[0].parentNode.insertBefore(txt_node_bf, cconf[0].nextSibling)

        f = open(lng_file_path, "wb")
        self.lng_file_dom.writexml(f)
        #print self.lng_file_dom.toxml()

