"""
This script will set the TeamCity build number of a configuration to 
max(dependencies_build_numbers + [own_build_number])

Motivation:
Say you have an installer configuration, which depends on the module1 and
module2 configurations. Let the installer have vcs number 100, and module1 have
vcs number 103. Then the installer build number will be 100, but we want it to be
103.

How to use:
-In the artifact paths of all the configurations that should influence the final
build number, add "vcsnumber*.txt => vcsnumbers.zip"
-In the artifact dependencies of all the configurations that should be
influenced by its dependencies, add "vcsnumbers.zip!*.* =>"
-In all of the above, add a build step that calls this module.

What happens:
For a configuration that has no dependencies, this script just saves the
current build number to 'vcsnumber_CONFIGURATION_NAME.txt' This file is then
included in the artifacts for that configuration.
For a configuration that has dependencies, the artifact dependencies copy all
the vcsnumber_CONFIGURATION_NAME.txt files, and find the largest build number
from those. It then selects the largest number of those and its own build
number.
Finally the script writes out "##teamcity[buildNumber 'COMPUTED_NUMBER']" 
This message tells TeamCity to update its build number to the one that was
computed by this script.
"""

from __future__ import print_function #To be able to monkeypatch print

import glob
import os
import re
import unittest

#from mock import patch #Commented out to avoid dependency on mock library on buildservers

def main():
    build_number = get_build_number()
    print(get_teamcity_message(build_number))
    write_vcs_number_file(get_vcs_number(build_number))

def get_teamcity_message(build_number):
    return "##teamcity[buildNumber '%s']" % build_number

def get_build_number():
    return re.sub('\d+$',
        str(get_final_vcs_number()),
        get_own_build_number())

def get_final_vcs_number():
    return max(
        get_vcs_number(get_own_build_number()),
        get_largest_dependency_vcs_number())

def get_own_build_number():
    own_number = os.environ.get('BUILD_NUMBER')
    if not own_number:
        raise Exception("BUILD_NUMBER not set in environment variables")
    return own_number

def get_largest_dependency_vcs_number():
    files = glob.glob('vcsnumber*.txt')
    if not files:
        return 0
    return max([get_vcs_number_from_file(f) for f in files])

def get_vcs_number_from_file(file_name):
    with open(file_name) as f:
        return int(f.read())

def get_vcs_number(build_number):
    try:
        return int(build_number.split('.')[-1])
    except Exception:
        raise Exception("Check the build number format in your TeamCity configuration. %s is not a valid build number, it needs to end with the vcs number." % build_number)

def get_branch_number(build_number):
    return '.'.join(build_number.split('.')[:-1])

def write_vcs_number_file(vcs_number):
    config_name = os.environ['TEAMCITY_BUILDCONF_NAME']
    config_name = config_name.replace(' ', '_')
    with open("vcsnumber_%s.txt" % config_name, 'w') as f:
        f.write(str(vcs_number))


# Tests below this point. Commented out to avoid dependency on mock library on buildservers

#class TestIntegration(unittest.TestCase):
#
#    @patch('__builtin__.print')
#    def test_given_no_dependencies(self, mock_print):
#        os.environ['BUILD_NUMBER'] = '7.3.0.1337'
#        os.environ['TEAMCITY_BUILDCONF_NAME'] = 'RulesEngine - static'
#        main()
#        mock_print.assert_called_once_with("##teamcity[buildNumber '7.3.0.1337']")
#        self.assertHasVcsNumberFile('vcsnumber_RulesEngine_-_static.txt', '1337')
#
#    @patch('__builtin__.print')
#    def test_given_several_dependencies__returns_largest_number(self, mock_print):
#        os.environ['BUILD_NUMBER'] = '7.3.0.1337'
#        os.environ['TEAMCITY_BUILDCONF_NAME'] = 'RulesEngine - static'
#        with open('vcsnumber_dep1.txt', 'w') as f:
#            f.write('1000')
#        with open('vcsnumber_dep2.txt', 'w') as f:
#            f.write('2000')
#        with open('vcsnumber_dep3.txt', 'w') as f:
#            f.write('3000')
#        main()
#        mock_print.assert_called_once_with("##teamcity[buildNumber '7.3.0.3000']")
#        self.assertHasVcsNumberFile('vcsnumber_RulesEngine_-_static.txt', '3000')
#
#    def assertHasVcsNumberFile(self, file_name, vcs_number):
#        with open(file_name) as f:
#            self.assertEqual(vcs_number, f.read())
#
#    def tearDown(self):
#        if os.environ.has_key('BUILD_NUMBER'):
#            del(os.environ['BUILD_NUMBER'])
#        if os.environ.has_key('TEAMCITY_BUILDCONF_NAME'):
#            del(os.environ['TEAMCITY_BUILDCONF_NAME'])
#        for f in glob.glob('vcsnumber_*.txt'):
#            os.remove(f)
#        
#
#class Test_main(unittest.TestCase):
#    
#    @patch('__main__.write_vcs_number_file')
#    @patch('__main__.get_build_number')
#    @patch('__builtin__.print')
#    def test(self, mock_print, mock_get_build_number, mock_write_vcs_number_file):
#        mock_get_build_number.return_value = '7.3.0.1814'
#        main()
#        mock_print.assert_called_once_with("##teamcity[buildNumber '7.3.0.1814']")
#        mock_write_vcs_number_file.assert_called_once_with(1814)
#        
#
#class Test_get_teamcity_message(unittest.TestCase):
#    
#    def test(self):
#        self.assertEqual("##teamcity[buildNumber '7.3.0.1234']", get_teamcity_message('7.3.0.1234'))
#
#class Test_get_build_number(unittest.TestCase):
#
#    @patch('__main__.get_final_vcs_number')
#    @patch('__main__.get_own_build_number')
#    def test(self, mock_get_own_build_number, mock_get_final_vcs_number):
#        mock_get_own_build_number.return_value = '7.3.0.1000'
#        mock_get_final_vcs_number.return_value = '1337'
#        self.assertEqual('7.3.0.1337', get_build_number())
#        
#
#class Test_get_final_vcs_number(unittest.TestCase):
#
#    @patch('__main__.get_largest_dependency_vcs_number')
#    @patch('__main__.get_own_build_number')
#    def test_when_own_number_is_largest(self, mock_get_own_build_number, mock_get_largest_dependency_vcs_number):
#        mock_get_own_build_number.return_value = '7.3.0.1000'
#        mock_get_largest_dependency_vcs_number.return_value = 999
#        self.assertEqual(1000, get_final_vcs_number())
#
#    @patch('__main__.get_largest_dependency_vcs_number')
#    @patch('__main__.get_own_build_number')
#    def test_when_other_number_is_largest(self, mock_get_own_build_number, mock_get_largest_dependency_vcs_number):
#        mock_get_own_build_number.return_value = '7.3.0.1000'
#        mock_get_largest_dependency_vcs_number.return_value = 1001
#        self.assertEqual(1001, get_final_vcs_number())
#
#class Test_get_largest_dependency_number(unittest.TestCase):
#    
#    def test_given_no_dependencies__returns_zero(self):
#        self.assertEqual(0, get_largest_dependency_vcs_number())
#
#    def test_given_one_dependency__returns_that_number(self):
#        with open('vcsnumber_dep1.txt', 'w') as f:
#            f.write('1000')
#        self.assertEqual(1000, get_largest_dependency_vcs_number())
#
#    def test_given_several_dependencies__returns_largest_number(self):
#        with open('vcsnumber_dep1.txt', 'w') as f:
#            f.write('1000')
#        with open('vcsnumber_dep2.txt', 'w') as f:
#            f.write('2000')
#        with open('vcsnumber_dep3.txt', 'w') as f:
#            f.write('3000')
#        self.assertEqual(3000, get_largest_dependency_vcs_number())
#
#    def tearDown(self):
#        for f in glob.glob('vcsnumber_*.txt'):
#            os.remove(f)
#
#
#class Test_get_branch_number(unittest.TestCase):
#
#    def test(self):
#        self.assertEqual('7.3.0', get_branch_number('7.3.0.1337'))
#        self.assertEqual('7.1.0', get_branch_number('7.1.0.2000'))
#
#class Test_get_vcs_number(unittest.TestCase):
#    
#    def test_given_valid_build_numbers__returns_vcs_number(self):
#        self.assertEqual(1337, get_vcs_number('7.3.0.1337'))
#        self.assertEqual(2000, get_vcs_number('7.1.0.2000'))
#
#    def test_given_invalid_build_number__raises(self):
#        with self.assertRaises(Exception) as e:
#            get_vcs_number('7.3.0.')
#        self.assertIn('Check the build number format in your TeamCity configuration. 7.3.0. is not a valid build number, it needs to end with the vcs number.', str(e.exception))
#
#class Test_get_own_build_number(unittest.TestCase):
#
#    def test_happy_path(self):
#        os.environ['BUILD_NUMBER'] = '7.3.0.1337'
#        self.assertEqual('7.3.0.1337', get_own_build_number())
#        os.environ['BUILD_NUMBER'] = '7.3.0.2000'
#        self.assertEqual('7.3.0.2000', get_own_build_number())
#        del(os.environ['BUILD_NUMBER'])
#
#    def test_when_build_number_is_not_set__throws(self):
#        os.environ['BUILD_NUMBER'] = ''
#        self.assertRaises(Exception, get_own_build_number)
#        del(os.environ['BUILD_NUMBER'])
#        self.assertRaises(Exception, get_own_build_number)

if __name__ == '__main__':
    #unittest.main()
    main()
