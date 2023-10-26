"""
Unit and integration tests for check_overlap.py

Author: Serena G. Lotreck
"""
import shutil, tempfile
import os
import unittest

import sys
sys.path.append('../annotation/abstract_scripts/')
import check_overlap as chk

class TestoverlapFunctions:
    """
    Tests individual helper functions to main()
    """

    def setup_method(self):
        """
        Create a temporary directory with the test data
        """
        # Make directories
        self.test_top_dir = tempfile.mkdtemp()
        self.test_tr_dir = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_te_dir = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_ap_dir = tempfile.mkdtemp(dir=self.test_top_dir)

        # Make files
        self.tr_names = [f'fake_doc{i}' for i in range(5)]
        self.te_names = [f'fake_doc{i}' for i in range(6)]
        self.ap_names = [f'fake_doc{i}' for i in range(17)]

        self.names = {self.test_tr_dir:self.tr_names,
                self.test_te_dir:self.te_names,
                self.test_ap_dir:self.ap_names}

        for dir_name, names_list in self.names.items():
            for name in names_list:
                with open(f'{dir_name}/{name}.txt', 'w') as f:
                    f.write('hello world!')


    def teardown_method(self):
        """
        Delete temporary files used for testing
        """
        # Remove temp data
        shutil.rmtree(self.test_top_dir)


    def test_get_names(self):
        """
        Check that .txt properly gets removed and that all files are
        retained when the input is as expected (only .txt files in the
        directory, no empty directories, no multiple file extensions).

        I can think of edge cases here, but given that these data files
        are generated by one of my own scripts upstream, I don't necessarily
        feel that it's necessary to test those edges. Can revise this later
        if needed.

        The script itself only takes files (so doesn't matter if there are
        directories within the directory of interest), and enforcers via assert
        statement that the directory is not empty of files.
        """
        fnames = chk.get_names(self.test_tr_dir, self.test_te_dir,
                                self.test_ap_dir)

        assert fnames['train'] == self.tr_names
        assert fnames['test'] == self.te_names
        assert fnames['apply'] == self.ap_names


    def test_compare_two_dirs_no_overlap(self):
        """
        Check that compare_two_dirs returns the string 'No data overlap!'
        when presented with two disjoint lists.
        """
        list1 = ['a','b','c']
        list2 = ['d','e']
        overlap = chk.compare_two_dirs(list1, list2)

        assert overlap == 'No data overlap!'


    def test_compare_two_dirs_overlap(self):
        """
        Check that compare_two_dirs returns a list with items in the
        intersection of two lists. Order does not matter.
        """
        list1 = ['a','b','c','d','e','f','g']
        list2 = ['e','f','g','x','y','z']
        overlap = chk.compare_two_dirs(list1, list2)

        assert set(overlap) == set(['e','f','g'])



class TestIntegration:
    """
    Tests that the script as a whole works with input/output
    """

    def setup_method(self):
        """
        Create a temporary directory containing the mock data
        """
        pass
        # Make directories
        self.test_top_dir = tempfile.mkdtemp()
        self.test_tr_dir_overlap = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_te_dir_overlap = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_ap_dir_overlap = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_tr_dir_no_overlap = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_te_dir_no_overlap = tempfile.mkdtemp(dir=self.test_top_dir)
        self.test_ap_dir_no_overlap = tempfile.mkdtemp(dir=self.test_top_dir)

        # Make files
        self.tr_names_overlap = [f'fake_doc{i}' for i in range(5)]
        self.te_names_overlap = [f'fake_doc{i}' for i in range(2,7)]
        self.ap_names_overlap = [f'fake_doc{i}' for i in range(6,10)]

        self.tr_names_no_overlap = [f'fake_doc{i}' for i in range(5)]
        self.te_names_no_overlap = [f'fake_doc{i}' for i in range(5,10)]
        self.ap_names_no_overlap = [f'fake_doc{i}' for i in range(10,15)]

        self.names = {self.test_tr_dir_overlap:self.tr_names_overlap,
                self.test_te_dir_overlap:self.te_names_overlap,
                self.test_ap_dir_overlap:self.ap_names_overlap,
                self.test_tr_dir_no_overlap:self.tr_names_no_overlap,
                self.test_te_dir_no_overlap:self.te_names_no_overlap,
                self.test_ap_dir_no_overlap:self.ap_names_no_overlap}

        for dir_name, names_list in self.names.items():
            for name in names_list:
                with open(f'{dir_name}/{name}.txt', 'w') as f:
                    f.write('hello world!')


        def test_main_overlap(self):
            """
            Check the contents of the output function after calling
            main() on directories that overlap with one another.
            """
            chk.main(self.test_tr_dir_overlap, self.test_te_dir_overlap,
                    self.test_ap_dir_overlap, self.test_top_dir)

            output = 'Overlapping abstracts between {key}:\n'