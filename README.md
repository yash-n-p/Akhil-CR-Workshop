# Framework 
The Library is to develop a methodology to use machine learning models as a surrogate for finite element human body models.

# FE
This library conatin Finite Elemental class which performs various operations to Run FE simulations and post processing the simulation results. The FE simulations are run using the sampled data set using stanadard sampling methods for FE-parameters input data provided by the user. The simulation results are processed into post processing software named META to obatin required results. The results from this will used as the raw data for training Machine learning Algorithms.

## Flowchart of FE:
<p align="center">
  <img src="https://github.com/jobindj/framework/blob/master/framework/FE_flow.png" alt="Sublime's custom image"/>
</p>


## Input files:
This is a user defined files which is specified by the user in `settings.yaml`
``` yaml
# Input settings file for FE simulations to get the user input:
Newfolder_name: 'akhil3t_ne'
Runs: 1
key: 'run_main_upd.key'
config: 'config.yaml'
# LS Dyna Run settings
LS_Run_path: 'abc.exe'
NCPU: 4
# Add Meta
meta_exec : 'qwe.bat'
# meta session parh
ses_path : 'K:/New/'
# meta sesion file name
ses_file : 'file.ses'
```

The `config.yaml` defined by the user with DOE values:
``` yaml
parameters:
  'delta velocity' :
        type :  dynaParameter
        parameter : DV
        default : 45
        max : 60
        min : 40
        distribution: Uniform
```
## Design of Experiments
Using `pyDOE` library to sample data based on Latin hypercube method. Each parameter sampling is done by Uniform distribution.

# Machine Learning
under development...
