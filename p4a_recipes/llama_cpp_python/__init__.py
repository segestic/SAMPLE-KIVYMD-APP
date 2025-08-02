from pythonforandroid.recipe import CompiledComponentsPythonRecipe

class LlamaCppPythonRecipe(CompiledComponentsPythonRecipe):
    """
    Final recipe. Builds llama-cpp-python from a pre-patched
    source zip provided by a direct URL.
    """
    
    # The URL now points directly to your fixed zip file.
    #url = 'https://github.com/segestic/llama-cpp-python/releases/download/v0.2.20/llama-cpp-python.zip'
    url = 'https://github.com/segestic/llama-cpp-python/releases/download/v0.2.20/llama-cpp-python-0.2.20.zip'
    
    # The name, version, and dependencies are still needed.
    name = 'llama-cpp-python'
    version = '0.2.20'
    depends = ['numpy', 'typing_extensions', 'diskcache', 'scikit-build-core']
    site_packages_name = 'llama_cpp'

# This is the entire recipe.
recipe = LlamaCppPythonRecipe()
