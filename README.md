# Backdoor
Python based pipeline to for batch processing 


A side-product of current projects. 
A simple pipeline to process batch jobs in a more organized manner than a simple `bash` script but not over the top as full-scale libraries.

#### config.json

`Config.json` is the heart of `Backdoor`. Create an array of `processes` and you're done.

Each `procees` requires to specify:

```
{
            "id" : 2,
            "name" : "Create test file",
            "command" : "touch  @file",
            "parameters" : {"file":"backdoor.txt"},
            "log" : "step1.log",
            "err" : "step1.err",
            "dependsOn" : [1]
}
```

1. ID : Process id. It's best to use successive numbers 1,2,3...
2. Name : A short description of the current process
3. command : The command. Any entry marked with `@` such as `@file` will be replaced with the matching parameter in parameters. `@file` would be replaced with the `file` entry in `parameters`
4. parameters : All parameters required for the command
5. log : If set, will either replace any occurence of `>@log` with the value or will append `>step1.log` (the specified filename) to command
6. err : Same as `log`, but for `std::cerr`
7. dependsOn : Any previous process ID. Pipeline executes this process if all processes in depends on finished successfully.

#### Run Backdoor

Change into your Backdoor directory, specify processes in `config.json` and run `./pipeline`.
In order to check command prior to processing, run `./pipeline --dry`
