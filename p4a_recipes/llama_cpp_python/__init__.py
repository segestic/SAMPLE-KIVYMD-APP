from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from os import environ

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe for compiling llama-cpp-python.
    
    This recipe works by passing the correct CMake arguments via environment
    variables to the llama-cpp-python setup.py script, which then handles
    the compilation of the bundled llama.cpp library.
    """
    
    # The version of the Python package from your requirements
    version = '0.2.20'
    
    # The URL should point to the Python package source, not the C++ library.
    # The setup.py script will handle the C++ submodule.
    url = f'https://github.com/abetlen/llama-cpp-python/archive/refs/tags/v{version}.tar.gz'
    
    # Name of the recipe
    name = 'llama-cpp-python'
    
    # Dependencies that must be built before this recipe
    depends = ['numpy', 'setuptools']
    
    # The name of the folder that is created in site-packages
    site_packages_name = 'llama_cpp'

    def get_recipe_env(self, arch):
        # Get the default environment from the base class
        env = super().get_recipe_env(arch)

        # The llama-cpp-python setup.py reads CMAKE_ARGS from the environment.
        # We set it here to configure the C++ build for Android.
        cmake_args = [
            '-DCMAKE_BUILD_TYPE=Release',
            '-DLLAMA_CUBLAS=OFF',
            '-DLLAMA_METAL=OFF',
            '-DLLAMA_CLBLAST=OFF',
            '-DLLAMA_BUILD_SERVER=OFF',
            '-DLLAMA_BUILD_TESTS=OFF',
            '-DLLAMA_BUILD_EXAMPLES=OFF',
        ]
        
        # Add our CMake arguments to the environment
        env['CMAKE_ARGS'] = ' '.join(cmake_args)
        
        # To be safe, also set LLAMA_CPP_PATH if needed, though CMAKE_ARGS
        # is the primary mechanism.
        environ['CMAKE_ARGS'] = env['CMAKE_ARGS']
        
        return env

# This line is essential
recipe = LlamaCppPythonRecipe()
