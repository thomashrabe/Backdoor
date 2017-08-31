#!/usr/bin/env python

from pipeline import Pipeline
import unittest
import json

class PipelineInitTest(unittest.TestCase):

    def runTest(self):
        self.assertTrue(Pipeline() is not None,'')

if __name__ == '__main__':
    unittest.main()