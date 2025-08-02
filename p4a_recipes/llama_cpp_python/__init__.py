from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe for compiling llama-cpp-python.
    This version uses an explicit self.apply_patch() call to ensure
    the '-march=native' flag is removed.
    """

    version = '0.2.20'
    url = f'https://github.com/abetlen/llama-cpp-python/archive/refs/tags/v{version}.tar.gz'
    name = 'llama-cpp-python'

    depends = ['numpy', 'typing_extensions', 'diskcache', 'scikit-build-core']

    site_packages_name = 'llama_cpp'

    def prebuild_arch(self, arch):
        """
        This method is called before the build. We explicitly apply our patch here.
        """
        super().prebuild_arch(arch)
        self.apply_patch('disable_native.patch', arch.arch)

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
