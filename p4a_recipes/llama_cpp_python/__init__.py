from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from os.path import join
import sh

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe for compiling llama-cpp-python.
    FINAL ATTEMPT: This version manually edits the CMakeLists.txt
    to forcefully remove the incompatible '-march=native' flag.
    """
    
    version = '0.2.20'
    url = f'https://github.com/abetlen/llama-cpp-python/archive/refs/tags/v{version}.tar.gz'
    name = 'llama-cpp-python'
    
    depends = ['numpy', 'typing_extensions', 'diskcache', 'scikit-build-core']
    
    site_packages_name = 'llama_cpp'

    def prebuild_arch(self, arch):
        """
        This method is called before the build. We use it to edit the file.
        """
        super().prebuild_arch(arch)

        # Get the path to the CMakeLists.txt file within the build directory
        build_dir = self.get_build_dir(arch.arch)
        cmake_file = join(build_dir, 'vendor', 'llama.cpp', 'CMakeLists.txt')

        # Use the 'sed' command to find the line with '-march=native' and delete it.
        # This is more forceful than a patch.
        print(f"Patching {cmake_file} to remove '-march=native'")
        sh.sed('-i', "/-march=native/d", cmake_file)

    def get_recipe_env(self, arch):
        """
        Set the environment variables for the build.
        """
        env = super().get_recipe_env(arch)
        
        cmake_args = [
            '-DCMAKE_BUILD_TYPE=Release',
            '-DLLAMA_CUBLAS=OFF',
            '-DLLAMA_METAL=OFF',
            '-DLLAMA_CLBLAST=OFF',
            '-DLLAMA_BUILD_SERVER=OFF',
            '-DLLAMA_BUILD_TESTS=OFF',
            '-DLLAMA_BUILD_EXAMPLES=OFF',
        ]
        
        env['SKBUILD_CMAKE_ARGS'] = ' '.join(cmake_args)
        
        return env

# This line is essential
recipe = LlamaCppPythonRecipe()
