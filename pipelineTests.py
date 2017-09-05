#!/usr/bin/env python

from pipeline import Pipeline
import unittest
import json

class PipelineInitTest(unittest.TestCase):

    def runTest(self):
        self.assertTrue(Pipeline() is not None,'')

class PipelineFinishedProcesses(unittest.TestCase):


    def runTest(self):
        
        p = Pipeline('./config.json','finished.json')

        processes = p.processes()
        print processes
        self.assertTrue(len(list(processes)) == 2)


if __name__ == '__main__':
    unittest.main()