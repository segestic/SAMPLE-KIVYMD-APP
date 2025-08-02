from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from os import environ

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe for compiling llama-cpp-python.
    This version correctly identifies scikit-build-core as a build dependency
    and disables incompatible native optimizations.
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
            # --- THIS IS THE FIX ---
            # Disable native optimization flag that fails during cross-compilation
            '-DLLAMA_NATIVE=OFF',
        ]
        
        env['CMAKE_ARGS'] = ' '.join(cmake_args)
        environ['CMAKE_ARGS'] = env['CMAKE_ARGS']
        
        return env

# This line is essential
recipe = LlamaCppPythonRecipe()
