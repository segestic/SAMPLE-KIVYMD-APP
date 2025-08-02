from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Definitive recipe for compiling llama-cpp-python.
    This version uses the correct GGML_NATIVE flag to disable
    incompatible host-specific optimizations.
    """

    version = '0.2.20'
    url = f'https://github.com/abetlen/llama-cpp-python/archive/refs/tags/v{version}.tar.gz'
    name = 'llama-cpp-python'

    depends = ['numpy', 'typing_extensions', 'diskcache', 'scikit-build-core']

    site_packages_name = 'llama_cpp'

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)

        cmake_args = [
            '-DCMAKE_BUILD_TYPE=Release',
            '-DLLAMA_CUBLAS=OFF',
            '-DLLAMA_METAL=OFF',
            '-DLLAMA_CLBLAST=OFF',
            '-DLLAMA_BUILD_SERVER=OFF',
            '-DLLAMA_BUILD_TESTS=OFF',
            '-DLLAMA_BUILD_EXAMPLES=OFF',
            # --- THIS IS THE CORRECT FLAG ---
            '-DGGML_NATIVE=OFF',
        ]

        # Use the specific environment variable for scikit-build-core
        env['SKBUILD_CMAKE_ARGS'] = ' '.join(cmake_args)

        return env

# This line is essential
recipe = LlamaCppPythonRecipe()
