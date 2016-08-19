# *meta-geclipse* plugin/bbclass/inherit for yocto
==================================================
  

## 0. Overview 

The `meta-geclipse` allows konfiguration/build of eclipse-project 
directly from yocto-recipes. 

We suppose that we already have sw in eclipse with 
availabe *Build Configuration*, for example for x86 platform and we
want to build our sw for different platform by yocto recipes.


Some features are not supported, 
plugin itself should be considered as beta version.

Eclipse(>=kepler) IDE with CDT(C,C++ dev) have to be in system !

Plugin has been tested on fsl-bsp version of yocto.

Maintainer  	:  Jiri Andrys (andrys.jiri+project_yoctogeclipse@gmail.com)   
Contributors	:  Jiri Andrys


## 1. Motivation 
for `meta-geclipse` is software which is using eclipse as development
platform and is in a state of wild development phase and running on many diferent HW platforms.
Modification of makefiles/eclipse took a lot of time.

*Note:*
>* We can use "meta-toolchain" from poky and source "environment-setup-XXX.sh"
and cross compile sw, but this method is more for early phase of development and could not 
give us features and scaling same as recipes. 

> * Eclipse it self is having plugin for yocto:
***The Yocto Project Application Development Toolkit (ADT)***
Unfortunattely ADT does not fit to our needs in late development phase,
when we need to build images for multiple customized platforms.


## 2. Limitations

Currently this plugin supports only Eclipse's CDT projects(Eclipse's C/C++ Development Tooling).
Eclipse's linked resources called "virtual folders" are not supported.



## 3. Version

		0.1



## 4. Getting started 

Here we suppose basic knowledge of writing yocto-recipes
and yocto build system.
  
  


### 4.1 Yocto Settings

1. To get started, clone the `meta-geclipse` repository :
	>`git clone https://github.com/meta-geclipse.git`


2. After cloning the repository, 
copy `meta-geclipse` folder to source folder of yocto environment.


3. Add bblayer to `conf/bblayers.conf`: 
	>`BBLAYERS += " ${BSPDIR}/sources/meta-gnomon-eclipse "`

>>At this point poky knows about `meta-geclipse` layer 
and included ***geclipse.bbclass*** . Because of this
we can add ***`inherit geclipse`*** to our recipes.



	
### 4.2 Yocto-Geclipse-Recipes:

>* All variables related to geclipse plugin have **GECLIPSE** prefix

>* All variables are in format KEY="VALUE" **or** 
in case of list comma-delimitedKEY="VALUE1, VAULE2"

>* Eclipse(>=kepler) IDE with CDT(C,C++ dev) have to be in system !
>* The ***whereis*** command has to be able to find eclipse executable 
 ***OR*** geclipse-recipes need to set ***GECLIPSE_ECLIPSE_BIN*** variable.




#### 4.2.1 Generic GECLIPSE Variables:


**`GECLIPSE_ECLIPSE_BIN`**
>This is **mandatory** variable only in case that 
***whereis*** command is not able to find eclipse.  
  
  
  
**`S`** 

>This is **mandatory** variable
and is used as starting point for searching eclipse-project-files(.project). 
The same way as yocto describes:
>>```The location in the Build Directory where unpacked recipe source code resides.```
  
  
  
**`GECLIPSE_PROJECTS_NAMES_DELIMSTR`**

>This is **optional** variable, but it is highly recomended.

>Defines list of eclipse projects in **`S`** directory,
which are going to be available for import and build.

>All projects are going to be available for import and build if we skip this varible.
  
  
  
**`GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH`**

>This is **optional** variable.

>In case that we want to skip some projects which are having in path 
some particular string we can use this variable.
  
  
  
**`GECLIPSE_PROJECTS_BUILD_CONF_STR`**

>This is **mandatory** variable.

>Defines eclipse's "Build Configuration"(Project/Build Configuration)




#### 4.2.2 (CFLAGS -I), (LDFLAGS -L) GECLIPSE Variables:

Poky does support pkg-config.
In case that sysroot do have some library pkg-config should 
tell us LDFLAGS and CFLAGS. We suppose that basic settings is done by 
"Build Configuration" and only missing parts are paths to includes and libraries.
Because of that Geclipse recipes only needs paths:


**`GECLIPSE_PROJECTS_ALL_FIND_INCLUDE_PATHS`**
>This is **optional** variable.

>Try to find includes by pkg-config which should be added to eclipse.(CFLAGS -I)

>*Example:*
 >>GECLIPSE_PROJECTS_ALL_FIND_INCLUDE_PATHS="dbus-1, glib-2.0, gthread-2.0,
											gobject-2.0, libxml-2.0"


**`GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS`**
>This is **optional** variable.

>Add include paths to the eclipse.(CFLAGS -I)


**`GECLIPSE_PROJECTS_ALL_FIND_LIBRARY_PATHS`**
>This is **optional** variable.

>Try to find paths of libraries by pkg-config which should be added to eclipse.(LDFLAGS -L)

>*Example:*
 >>GECLIPSE_PROJECTS_ALL_FIND_LIBRARY_PATHS="dbus-1, glib-2.0, gthread-2.0,
											gobject-2.0, libxml-2.0"


**`GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS`**
>This is **optional** variable.

>Add library paths to the eclipse.


**`GECLIPSE_PROJECTS__XXX__LDFLAGS_LIBNAMES`**
>This is **optional** variable.

>Add library to the eclipse.(LDFLAGS -l)

>XXX is the name of eclipse project(big letters) where we want to add library.




#### 4.2.3 Eclipse`s "Build Variables" :
Eclipse is having so called "Build Variables"
which are accessible during eclipse build.
We can add this "Build Variable" to eclipse in recipes by **`GECLIPSE_PROJECTS_ALL_BUILD_VARS`** variable.




#### 4.2.4 Eclipse`s "Post-Build Steps" :
When eclipse finish build of particular project,
we usually want to copy result of build(shared libs, etx) to particular
destination or run sume kind of test.
We can do this from recipes side by **`GECLIPSE_PROJECTS__XXX__POST_BUILD_STEP`** variable.
XXX is the name of eclipse project(big letters) where we want to run post build step.

>*Example:*
>>`GECLIPSE_PROJECTS__XXX__POST_BUILD_STEP`="cp -rf ${SOME_PATH}/somelib.so ${SOME_PATH2}"


#### 4.2.5 GECLIPSE FLAGS :
Sometimes we need to apply some set of tasks on all projects.
We can control this tasks by following flags :

**IGNORE_YOCTO_CC_LD_FLAGS**
>Ignore yocto's CFLAGS and LDFLAGS

**SAME_LINKER_COMMAND_AS_COMPILER_COMMAND**
>Set the same linker command as compiler command 

**ADD_FPIC_TO_SHARED_LIBS**
>Set -fPIC parameter to shared libs

**ENABLE_PARALLEL_BUILD**
>Enable parallel build

**REMOVE_ALL_NON_WORKSPACE_RELATED_INCLUDE_PATHS_AND_LIBRARY_PATHS**
>On the begining we said that we have most probably Build Configuration
on base of x86 platform and most of library related paths are out of our
project, because we need to use cross compile which is in sysroots of yocto and 
not inside our native system we neeed to clear it.


Flags should be listed in followin!!!g variable:
**`GECLIPSE_PROJECTS_ALL_FLAGS`** 



## 5. Geclipse-Recipes Example:

~~~bitbake

#{DATE: 1984XXXX; AUTHOR: Andrys Jiri;  DESCRIPTION: Bla bla

DESCRIPTION = "Sample Geclipse Build"
LICENSE = "CLOSED"

FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

PR = "r1" 

DEPENDS = "dbus glib-2.0 dbus-glib "
RDEPENDS_${PN} = "dbus glib-2.0 dbus-glib "

INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_PACKAGE_STRIP = "1"

SRC_URI += "file://${PN}_${PV}.tar.gz"

#{DATE: 1984XXXX; NAME: Andrys Jiri; DESCRIPTION: xxx patch
SRC_URI += "file://xxx.patch"
#}1984XXXX:


#=====================================================================================

#{DATE: XXXXXXXX; NAME: Andrys Jiri; #DESCRIPTION: Mandatory settings:

S="${WORKDIR}/${PN}_${PV}"

GECLIPSE_ECLIPSE_BIN="/home/trubka/eclipse/eclipse"
GECLIPSE_PROJECTS_NAMES_DELIMSTR="prj1, prj2, prj3"
GECLIPSE_PROJECTS_SKIP_IF_STR_IN_PRJPATH="android"
GECLIPSE_PROJECTS_BUILD_CONF_STR="Release"

#}XXXXXXXX:

DEST_LIB_PATH="/usr/local/lib/"
DEST_APP_PATH="/opt/"
LIB_PATH="${WORKDIR}${DEST_LIB_PATH}"
APP_PATH="${WORKDIR}${DEST_APP_PATH}"

GECLIPSE_PROJECTS_ALL_FLAGS="SAME_LINKER_COMMAND_AS_COMPILER_COMMAND, \
                             ADD_FPIC_TO_SHARED_LIBS, \
                             ENABLE_PARALLEL_BUILD,\
                             REMOVE_ALL_NON_WORKSPACE_RELATED_INCLUDE_PATHS_AND_LIBRARY_PATHS"

#{DATE: XXXXXXXX; NAME: Andrys Jiri; DESCRIPTION: add dependencies[cflags[-I], ldflags[-L] ]:
GECLIPSE_PROJECTS_ALL_FIND_INCLUDE_PATHS="dbus-1, glib-2.0, dbus-glib-1, libxml-2.0"
GECLIPSE_PROJECTS_ALL_FIND_LIBRARY_PATHS="dbus-1, glib-2.0, dbus-glib-1, libxml-2.0"
#}

GECLIPSE_PROJECTS_ALL_BUILD_VARS="LIB_PATH=${LIB_PATH}, APP_PATH=${APP_PATH}"
GECLIPSE_PROJECTS_ALL_INCLUDE_PATHS="${S}/prj1/include"
GECLIPSE_PROJECTS_ALL_LIBRARY_PATHS="${LIB_PATH}"

GECLIPSE_PROJECTS__PRJ1__LDFLAGS_LIBNAMES="CZECHIA1, VACLAV4"
GECLIPSE_PROJECTS__PRJ2__LDFLAGS_LIBNAMES="CZECHIA1, VACLAV4"

#{Post-build commands:
LIB_POST_BUILD_STEP="cp -rf ${S}/src/${ProjName}/${ConfigName}/lib${ProjName}.so ${LIB_PATH}"
GECLIPSE_PROJECTS__PRJ1__POST_BUILD_STEP="${LIB_POST_BUILD_STEP}"
GECLIPSE_PROJECTS__PRJ2__POST_BUILD_STEP="${LIB_POST_BUILD_STEP}"

GECLIPSE_PROJECTS__PRJ3__POST_BUILD_STEP="cp -rf ${S}/src/${ProjName}/${ConfigName}/${ProjName} ${APP_PATH}"
#}

inherit pkgconfig
inherit geclipse

do_prepare() {
    mkdir -p "${LIB_PATH}"
    mkdir -p "${APP_PATH}"
}

addtask do_prepare before do_configure


do_install() {

  mkdir -p "${D}/${DEST_LIB_PATH}"
  mkdir -p "${D}/${DEST_APP_PATH}"

  cp -af ${LIB_PATH}/*.so ${D}/${DEST_LIB_PATH}
  cp -af ${APP_PATH}/* ${D}/${DEST_APP_PATH}
}

FILES_${PN} += "${DEST_APP_PATH}/*"
FILES_${PN} += "${DEST_LIB_PATH}/*"

#}1984XXXX:
~~~
