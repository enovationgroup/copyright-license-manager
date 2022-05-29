import filecmp
import os


from clmgr.main import main

test_dir = os.path.dirname(os.path.realpath(__file__))

def test_single_java():
        global test_dir

        # Test arguments
        test_args = ['-c', test_dir + '/config/multiple.yml', '--file', test_dir + '/input/java/multiple.java', '--header-length', '120']

        main(test_args)

        assert filecmp.cmp(test_dir + '/input/java/multiple.java', test_dir + '/output/java/multiple.java', shallow=False)
