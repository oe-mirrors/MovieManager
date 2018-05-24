from distutils.core import setup
import setup_translate

pkg = 'Extensions.MovieManager'
setup (name = 'enigma2-plugin-extensions-moviemanager',
       version = '1.53',
       description = 'copy, move and delete more files at once',
       packages = [pkg],
       package_dir = {pkg: 'plugin'},
       package_data = {pkg: ['*.xml', 'locale/*.pot', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass = setup_translate.cmdclass, # for translation
      )
