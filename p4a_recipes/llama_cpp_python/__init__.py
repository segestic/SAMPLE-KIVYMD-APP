from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Definitive recipe for llama-cpp-python.
    1. Downloads from the user's pre-patched URL.
    2. Forcefully injects the correct Android compiler flags into CMake
       to prevent the build system from adding '-march=native'.
    """

    # Using your specified URL for the pre-patched source code
    url = 'https://github.com/segestic/llama-cpp-python/releases/download/v0.2.20/llama-cpp-python-0.2.20.zip'

    version = '0.2.20'
    name = 'llama-cpp-python'
    depends = ['numpy', 'typing_extensions', 'diskcache', 'scikit-build-core']
    site_packages_name = 'llama_cpp'

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)

        # Get the standard Android compiler flags from python-for-android
        c_flags = " ".join(arch.get_c_compiler_args())
        cxx_flags = " ".join(arch.get_cxx_compiler_args())

        cmake_args = [
            '-DCMAKE_BUILD_TYPE=Release',
            '-DGGML_NATIVE=OFF',
            '-DLLAMA_CUBLAS=OFF',
            '-DLLAMA_METAL=OFF',
            '-DLLAMA_CLBLAST=OFF',
            '-DLLAMA_BUILD_SERVER=OFF',
            '-DLLAMA_BUILD_TESTS=OFF',
            '-DLLAMA_BUILD_EXAMPLES=OFF',
            # Final safeguard: Forcefully override the C and CXX flags
            f'-DCMAKE_C_FLAGS="{c_flags}"',
            f'-DCMAKE_CXX_FLAGS="{cxx_flags}"',
        ]

        # Use the specific environment variable for scikit-build-core
        env['SKBUILD_CMAKE_ARGS'] = ' '.join(cmake_args)

        return env

recipe = LlamaCppPythonRecipe()
