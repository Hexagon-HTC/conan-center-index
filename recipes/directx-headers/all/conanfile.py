from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, rmdir
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.scm import Version
from conan.tools.microsoft import is_msvc
import os

required_conan_version = ">=1.52.0"


class DirectXHeadersConan(ConanFile):
    name = "directx-headers"
    description = "Headers for using D3D12"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/DirectX-Headers"
    topics = ("3d", "d3d", "d3d12", "direct", "direct3d", "directx", "graphics")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"

    @property
    def _min_cppstd(self):
        return 11

    @property
    def _compilers_minimum_version(self):
        return {
            "apple-clang": "10",
            "clang": "5",
            "gcc": "6",
            "msvc": "191",
            "Visual Studio": "15",
        }

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if not self.settings.os in ["Linux", "Windows"]:
            raise ConanInvalidConfiguration(f"{self.name} is not supported on {self.settings.os}")
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        self.tool_requires("meson/1.2.2")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = MesonToolchain(self)
        tc.project_options["build-test"] = False
        tc.generate()
        virtual_build_env = VirtualBuildEnv(self)
        virtual_build_env.generate()

    def build(self):
        meson = Meson(self)
		# Calling configure ends with error on docker with v143:
        # ..\..\source\meson.build:4:0: ERROR: prefix value '/' must be an absolute path
        # conan meson tool was rewritten in conan 2.x and they added prefix option to set before configure (it should be changed when we upgrade to conan 2.x)
        # for now we calling meson configure manually in case of MSVC
        if is_msvc(self):
            native_file = os.path.join(self.build_folder, "conan", "conan_meson_native.ini")
            self.run(f"meson setup --native-file {native_file} {self.build_folder} {self.source_folder} --prefix={self.package_folder}")
        else:
            meson.configure()
        meson.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        meson = Meson(self)

        if is_msvc(self):
            meson_build_folder = self.build_folder.replace("\\", "/")
            cmd = f'meson install -C "{meson_build_folder}" --destdir /'
            self.run(cmd)
        else:
            meson.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        if self.settings.os == "Linux" or self.settings.get_safe("os.subsystem") == "wsl":
            self.cpp_info.includedirs.append(os.path.join("include", "wsl", "stubs"))
        self.cpp_info.libs = ["d3dx12-format-properties", "DirectX-Guids"]
        self.cpp_info.set_property("cmake_file_name", "DirectX-Headers")
        self.cpp_info.set_property("cmake_target_name", "Microsoft::DirectX-Headers")
        self.cpp_info.set_property("pkg_config_name", "DirectX-Headers")
        if self.settings.os == "Windows":
            self.cpp_info.system_libs.append("d3d12")
        if self.settings.compiler == "msvc":
            self.cpp_info.system_libs.append("dxcore")
