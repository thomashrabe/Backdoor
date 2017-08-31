#!/usr/bin/env python
import json
import subprocess
import sys,time

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
        self._rawObject = jsonParameters

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

    @property
    def processJSON(self):
        return self._rawObject

class Pipeline(object):
    def __init__(self,configFile = './config.json',previoslyFinished = None):

        self._finishedProcesses = []
        self._failedProcesses = []
        self._waitingProcesses = []
        self._log = {}
        self._previousProcesses = None

        with open(configFile) as a_file:
            self._configuration = json.load(a_file)

        if previoslyFinished:
            with open(previoslyFinished) as a_file:
                self._previousProcesses = json.load(a_file)
    

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
            elif len([ p for p in self._previousProcesses if p.id == process.id]) > 0:
                print '%s was finished in a previous run of Backdoor.' % (process.name)
                return    
            
            print('STARTING %s ' % (process.name)) 
            print(process.command)

            startTime = time.time()

            subprocess.check_output(process.command, shell=True)
            self._finishedProcesses.append(process.id)
            self._log[process.id] = [process.name,process.command]
            
            endTime = time.time()
            difference = endTime - startTime
            print('FINISHED %s ' % (process.name)) 
            print('Processing took %i seconds') % (differnce)
            print('')
            
        except subprocess.CalledProcessError as grepexc:
            self._failedProcesses.append(process.id)
            self._log[process.id] = [process.name,process.command,grepexc.returncode, grepexc.output]
        except PipelineDependencyFailedException as pex:
            print >> sys.stderr , 'Process ',process.id, ' not run because of dependency'
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
    parser.add_argument('--finished', type=str)
    parser.add_argument('--dry', action='store_true')
    
    args = parser.parse_args()
    
    if args.conf:
        pipeline = Pipeline(args.conf,args.finished)
    else:
        pipeline = Pipeline()

    if args.dry:
        for command in pipeline.gatherCommands():
            print(command)

    else:
        for process in pipeline.processes():
            pipeline.runProcess(process)

        for process in pipeline.waiting_processes:
            pipeline.runProcess(process)

        
        with open('Backdoor-finished.json','w') as f:
            processes = pipeline.processes()
            finshedProcesses = [processes[i] for i in pipeline.finished_processes]

            json.dump(finshedProcesses,f,indent=4, separators=(',', ': '))

        with open('Backdoor-failed.json','w') as f:
            processes = pipeline.processes()
            failedProcesses = [processes[i] for i in pipeline.failed_processes]
            json.dump(failedProcesses,f,indent=4, separators=(',', ': '))


        print('All finished and failed processes were written into')
        print('Backdoor-finished.json and Backdoor-failed.json')

