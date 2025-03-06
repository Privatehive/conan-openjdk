#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.files import copy, get, symlinks
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration
import json, os

required_conan_version = ">=2.0"

class OpenJDK(ConanFile):

    jsonInfo = json.load(open("info.json", 'r'))
    # ---Package reference---
    name = jsonInfo["projectName"]
    version = jsonInfo["version"]
    user = jsonInfo["domain"]
    channel = "stable"
    # ---Metadata---
    description = jsonInfo["projectDescription"]
    license = jsonInfo["license"]
    author = jsonInfo["vendor"]
    topics = jsonInfo["topics"]
    homepage = jsonInfo["homepage"]
    url = jsonInfo["repository"]
    # ---Requirements---
    requires = []
    tool_requires = []
    # ---Sources---
    exports = ["info.json"]
    exports_sources = []
    # ---Binary model---
    settings = "os", "arch"
    options = {}
    default_options = {}
    # ---Build---
    generators = []
    # ---Folders---
    no_copy_source = True

    def validate(self):
        if self.settings.os == "Windows" and self.settings.arch != "x86_64" and Version(self.version) < "16.0.0":
            raise ConanInvalidConfiguration("Unsupported Architecture for Windows. This package currently only supports x86_64 for versions < 16.0.0.")
        valid_os = ["Windows", "Linux", "Macos"]
        if str(self.settings.os) not in valid_os:
            raise ConanInvalidConfiguration(f"{self.name} {self.version} is only supported for the following operating systems: {valid_os}")
        valid_arch = ["x86_64", "armv8"]
        if str(self.settings.arch) not in valid_arch:
            raise ConanInvalidConfiguration(f"{self.name} {self.version} is only supported for the following architectures on {self.settings.os}: {valid_arch}")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.os)][str(self.settings.arch)],
                  destination=self.source_folder, strip_root=True)

    def package(self):
        if self.settings.os == "Macos":
            source_folder = os.path.join(self.source_folder, "zulu-%s.jdk" % Version(self.version).major, "Contents", "Home")
        else:
            source_folder = self.source_folder
        symlinks.remove_broken_symlinks(self, source_folder)
        copy(self, pattern="*",
                src=os.path.join(source_folder, "bin"),
                dst=os.path.join(self.package_folder, "bin"),
                excludes=("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"))
        copy(self, pattern="*",
                src=os.path.join(source_folder, "include"),
                dst=os.path.join(self.package_folder, "include"))
        copy(self, pattern="*",
                src=os.path.join(source_folder, "lib"),
                dst=os.path.join(self.package_folder, "lib"))
        copy(self, pattern="*",
                src=os.path.join(source_folder, "jmods"),
                dst=os.path.join(self.package_folder, "jmods"))
        copy(self, pattern="*",
                src=os.path.join(source_folder, "legal"),
                dst=os.path.join(self.package_folder, "licenses"))
        copy(self, pattern="*",
                src=os.path.join(source_folder, "jre"),
                dst=os.path.join(self.package_folder, "jre"))
        copy(self, pattern="LICENSE",
                src=source_folder,
                dst=self.package_folder)
        # conf folder is required for security settings, to avoid
        # java.lang.SecurityException: Can't read cryptographic policy directory: unlimited
        # https://github.com/conan-io/conan-center-index/pull/4491#issuecomment-774555069
        copy(self, pattern="*",
                src=os.path.join(source_folder, "conf"),
                dst=os.path.join(self.package_folder, "conf"))

    def package_info(self):
        self.output.info("Creating JAVA_HOME environment variable: %s" % self.package_folder)
        self.buildenv_info.define_path("JAVA_HOME", self.package_folder)
        self.output.info("Prepending to PATH environment variable: %s" % os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
