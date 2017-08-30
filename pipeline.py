#!/usr/bin/env python

import json
import subprocess
import sys

class PipelineDependencyFailedException(Exception):
    pass

class PipelineDependencyNotFinishedException(Exception):
    pass

class PipelineProcess(object):

    def __init__(self, jsonParameters,config):
        self._id        = jsonParameters['id']
        self._name      = str(jsonParameters['name'])
        self._command   = str(jsonParameters['command'])
        self._parameters= jsonParameters['parameters']
        self._depends_on= jsonParameters['dependsOn']
        if 'log' in jsonParameters:
            self._log    = jsonParameters['log']
        else:
            self._log = None

        if 'err' in jsonParameters:
            self._err    = jsonParameters['err']
        else:
            self._err = None

        self._config    = config

    @property
    def command(self):
        """
        Assembles CLI command from parameters
        """
        command = str(self._command)
        
        for key in self._config:
            command = command.replace(str('@'+key),str(self._config[key]))

        for key in self._parameters:
            command = command.replace(str('@'+key),str(self._parameters[key]))
        
        if '@log' in command and self._log:
            command = command.replace('@log','>' + str(self._log))
        elif self._log:
            command += " > " + self._log

        if '@err' in command and self._err:
            command = command.replace('@err','2>' + str(self._err))
        elif self._err:
            command += " 2> " + self._err

        return command

    @property
    def id(self):
        """ Gets process id """ 
        return self._id

    @id.setter
    def set_id(self,value):
        """ Sets process id """
        self._id = value

    @property
    def depends_on(self):
        return self._depends_on

    @property
    def name(self):
        return self._name

class Pipeline(object):
    def __init__(self,configFile = './config.json'):

        self._finishedProcesses = []
        self._failedProcesses = []
        self._waitingProcesses = []
        self._log = {}

        with open(configFile) as a_file:
            self._configuration = json.load(a_file)

    @property
    def finished_processes(self):
        return self._finishedProcesses

    @property
    def failed_processes(self):
        return self._failedProcesses

    @property
    def waiting_processes(self):
        return self._waitingProcesses
    
    @property
    def log(self):
        return self._log

    def processes(self):
        """
        Generates a list of PipelineProcesses
        """
        for process in self._configuration['processes']:
            yield PipelineProcess(process,self._configuration['config'])

    def runProcess(self,process):
        """
        Executes a process of the pipeline
        """
        try:
            if len([d for d in process.depends_on if d in self._failedProcesses]) > 0:
                raise PipelineDependencyFailedException()
            elif len(self._finishedProcesses) > 0 and len([d for d in process.depends_on if d in self._finishedProcesses]) == 0:
                raise PipelineDependencyNotFinishedException()
                 
            print('STARTING %s ' % (process.name)) 
            print(process.command)

            subprocess.check_output(process.command, shell=True)
            self._finishedProcesses.append(process.id)
            self._log[process.id] = [process.name,process.command]
            
            print('FINISHED %s ' % (process.name)) 
            
        except subprocess.CalledProcessError as grepexc:
            self._failedProcesses.append(process.id)
            self._log[process.id] = [process.name,process.command,grepexc.returncode, grepexc.output]
        except PipelineDependencyFailedException as pex:
            self._failedProcesses.append(process.id)
            self._log[process.id] = [process.name,process.command]
        except PipelineDependencyNotFinishedException as pex:
            self._waitingProcesses.append(process)

    def gatherCommands(self):
        
        for process in self.processes():
            yield process.command


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(prog='Backdoor')
    parser.add_argument('--conf', type=str)
    parser.add_argument('--dry', action='store_true')
    args = parser.parse_args()

    pipeline = Pipeline()

    if args.dry:
        for command in pipeline.gatherCommands():
            print(command)

    else:
        for process in pipeline.processes():
            pipeline.runProcess(process)

        for process in pipeline.waiting_processes:
            pipeline.runProcess(process)

        
        print('FINISHED PROCESSES')
        for finished_id in pipeline.finished_processes:
            print(pipeline.log[finished_id][0])
            print(pipeline.log[finished_id][1])

        print('')
        print('')
        print('')
    
        if(len(pipeline.failed_processes) > 0):
            print('FAILED PROCESSES')
            for failed_id in pipeline.failed_processes:
                print(pipeline.log[failed_id][0])
                print(pipeline.log[failed_id][1])
    
