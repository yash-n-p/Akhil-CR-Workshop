# AUTOGENERATED! DO NOT EDIT! File to edit: FE.ipynb (unless otherwise specified).

__all__ = ['FE']

# Cell

from pyDOE import lhs
import numpy as np
from scipy.stats.distributions import norm
from scipy.stats import uniform
import yaml
from qd.cae.dyna import KeyFile
import os
import sys
import pandas as pd
import subprocess
import shlex

class FE():
    """
    This Class contains set of methods which performs reading of the .yaml file and replaces values of the input parameters
    with newly generated sample data sets. And then, new key files are generated for simulation. and also inclues runnings the simulations in LsDyna
    using the generated key files and postprocessing the results using Metapost.

    -----------
       INPUTS
    -----------
            settigs : Input file for FE simulations to get the user input

    """

    def __init__(self, settings):

        self.settings = settings
        self._get_user_input()

    def _get_user_input(self):
        """ gets the user input details from the settings.yaml file.

        Returns
        -------
        self.fin_dir         :   Final path of the created directory
        self.Run        :   Number of runs
        self.para_list  :   A .yaml file containing the parameters/ features/ variables for sampling with appropriate
                            values as subkeys in the same file.
        self.key        :   .key file containg the initial simulation details.
        self.ls_run_exe :   exectuable file for Ls run
        self.ncpu       :   Numebr of memory to run LsDyna
        self.meta_exe   :   Metapost batch command (depends on your installation of Metapost)
        self.ses_path   :   Meta session file path
        self.ses        :   Meta session file
        """

        with open(self.settings,'r') as file:
            inp = yaml.load(file, Loader=yaml.FullLoader)
        inp_vals=[*inp.values()]
        inp_keys=[*inp.keys()]

        req=['Newfolder_name','Runs','key','config','LS_Run_path','NCPU','type','meta_exec','ses_path','ses_file']

        for name in req:
            if name not in inp_keys:
                raise Exception(name +" not in settings.yaml file")

            if inp[name] == None:
                raise Exception(name +" value not in settings.yaml file")

        if isinstance(inp['Runs'], int) == False:
            raise Exception("Enter a integer value for Run in settings.yaml")

        for i in range(0,len(inp_keys)):
            if inp_keys[i] =='Newfolder_name':
                file_name=inp_vals[i]
            elif inp_keys[i] =='Runs':
                self.Run=inp_vals[i]
            elif inp_keys[i] =='key':
                self.key=inp_vals[i]
            elif inp_keys[i] =='config':
                self.para_list=inp_vals[i]
            elif inp_keys[i] =='LS_Run_path':
                self.ls_run_exe = inp_vals[i]
            elif inp_keys[i] =='NCPU':
                self.ncpu=inp_vals[i]
            elif inp_keys[i] =='meta_exec':
                self.meta_exe=inp_vals[i]
            elif inp_keys[i] =='ses_path':
                self.ses_path=inp_vals[i]
            elif inp_keys[i] =='ses_file':
                self.ses=inp_vals[i]

        current_directory = os.getcwd()
        self.fin_dir = os.path.join(current_directory,file_name)
        try:
            os.mkdir(self.fin_dir)
        except OSError as err:
            print(err)

        self._set_keypath()

        return self.fin_dir , self.Run , self.key , self.para_list

    def _set_keypath(self):
        """ changes the *INCLUDE PATH card in the key file

        Parameters
        ----------
        self.fin_dir: Path of include dyna files

        Returns
        -------
        self.newkey : a new key file with an updated file path.

        """
        k = KeyFile(self.key)
        include_path = k["*INCLUDE_PATH"][0]
        include_path[0] = self.fin_dir.replace('\\','/')
        k.save("upd_key.key")
        self.newkey ='upd_key.key'

        return self.newkey

    def Read_config(self):
        """ converts the .yaml file to a dataframe

        Parameters
        ----------
        self.para_list : the config.yaml file  with the user inputs

        Returns
        -------
        self.dynaParameters : Dataframe consisting yaml file data

        """
        with open(self.para_list,'r') as file:
            parameter_list  = yaml.load(file, Loader=yaml.FullLoader)
        dynParams = {k: v for k, v in parameter_list['parameters'].items() if parameter_list['parameters'][k]['type'] == 'dynaParameter'}
        self.dynaParameters = pd.DataFrame.from_dict(dynParams)

        return self.dynaParameters


    def get_samples(self):
        """ samples the data based on the .yaml file using lhs library and Uniform distribution

        Parameters
        ----------
        self.dynaParameters  : Dataframe consisting yaml file data

        Returns
        -------
        self.DOE   : sampled Dataframe

        """
#         global Data
#         Data=[]
#         Data = lhs(self.para_num, samples=self.Run)
#         means = var[0]
#         stdvs = var[1]
#         for i in range(0,self.para_num,1):
#             Data[:, i] = norm(loc=means[i], scale=stdvs[i]).ppf(Data[:, i])

        self.DOE = lhs(len(self.dynaParameters.loc['parameter']),samples = self.Run)
        minimum_val = self.dynaParameters.loc['min']
        maximum_val = self.dynaParameters.loc['max']
        for i in range(0,len(self.dynaParameters.loc['parameter'])):
            self.DOE[:,i]=uniform(minimum_val[i], maximum_val[i]-minimum_val[i]).ppf(self.DOE[:, i])
        return self.DOE

    def generate_key_file(self):
        """ Generate the new updated .key file and a FE_Parameters.yaml file containing respective sampled values
        for each parameters in new folders.

        Parameters
        ----------
        self.newkey          : a new key file with an updated file path.
        self.fin_dir         : final path of the created directory
        self.Run             : Number of samples required
        self.dynaParameters  : Dataframe consisting yaml file data
        self.DOE             : sampled Dataframe

        Returns
        -------
         Generates new keyfile directories with FE_parameters.yaml for each sample set.

        """
        kf=KeyFile(self.newkey)
        key_parameters=kf["*PARAMETER"][0]
        key_parameters_array=np.array(kf["*PARAMETER"][0])

        # Creating a dictionary with key and it's values:
        key_dict={}
        R_index=[]
        for i in range(0,len(key_parameters_array)):
            if key_parameters_array[i].startswith('R'):
                R_index.append(i)
                f=key_parameters_array[i].split(' ')
                key_dict[f[1]]=f[-1]
        par_lis=[*key_dict.keys()]
        os.chdir(self.fin_dir)

        for run in range(0,self.Run):

            os.mkdir('Run_'+str(run+1))
            os.chdir('Run_'+str(run+1))
            FE_Parameters = {}

            for para in range(0,len(self.dynaParameters.loc['parameter'])):

                for i in range(0,len(R_index),1):

                    if par_lis[i] == self.dynaParameters.loc['parameter'][para]:

                        key_parameters[i+1,1] = self.DOE[run,para]
                        kf.save("run_main_{}.key".format(str(run+1)))
                    FE_Parameters[par_lis[i]] =  key_parameters[i+1,1]
                    with open('FE_Parameters.yaml','w') as FE_file:
                        yaml.dump(FE_Parameters,FE_file,default_flow_style = False)
            os.chdir(self.fin_dir)

    def get_simulation_files(self):
        """
        Runs all the methods of pre-process class

        """
        self.Read_config()
        self.get_samples()
        self.generate_key_file()


    def Run_LS(self):
        """
        Runs LsDyna

        """
        os.chdir(self.fin_dir)
        for i in range(0,self.Run):
            path = 'Run_'+str(i+1)
            ar=os.path.join(self.fin_dir,path)
            os.chdir(ar)
            subprocess.call(r'{} i=run_main_{}.key NCPU={}'.format(self.ls_run_exe,(i+1),self.ncpu))


    def read_meta(self):
        """
        Reads .ses for meta postprocessing

        """
        meta_exec = self.meta_exe
        meta_session_file_path = self.ses_path
        meta_session_file_name = self.ses
        session = meta_session_file_path + meta_session_file_name
        meta_options = " -b -noses -fastses -s "
        metapost_command = meta_exec + meta_options + session
        simulation_path = self.sim_path
        os.chdir(simulation_path)
        process_command=shlex.split(metapost_command)
        command_process=subprocess.Popen(process_command, stdout=subprocess.PIPE)
        output, err = command_process.communicate()

    def get_results(self):
        """
        Running Meta post to get results

         Returns
        -------
         returns .yaml file with specified injury results

        """
        result=[]
        HIC = {}
        for runs in range(0,self.Run):
            os.chdir(self.fin_dir)
            self.sim_path = 'Run_'+str(runs+1)
            self.read_meta()
            df = pd.read_csv("{}/{}/HIC_15.csv".format(self.fin_dir.replace('\\','/'),self.sim_path),skiprows = 5,nrows=1)
            result = df.values.tolist()
            HIC['HIC_15'] = result[0][1]
            with open('HIC.yaml','w') as result_file:
                yaml.dump(HIC,result_file,default_flow_style = False)

    def get_dataset(self):
        """ read and joins the input and output yaml file from each simulation folder
        and saves it in a Inputs_outputs_dataset.csv file.

        Returns
        -------
         Inputs_outputs_dataset.csv

        """
        os.chdir(self.fin_dir)
        Result_set = pd.DataFrame(data=None,columns=None,dtype=None,copy=False)
        for j in range(0,self.Run):
            os.chdir('Run_{}'.format(j+1))
            with open('FE_Parameters.yaml','r') as file:
                inp = yaml.load(file, Loader=yaml.FullLoader)
            with open('HIC.yaml','r') as file:
                out = yaml.load(file, Loader=yaml.FullLoader)
            df_input_set = pd.DataFrame.from_dict(inp, orient='index').T
            df_output_set = pd.DataFrame.from_dict(out, orient='index').T
            df_input_set[df_output_set.columns]=df_output_set.values
            Result_set=Result_set.append(df_input_set,ignore_index=True)
            os.chdir(self.fin_dir)
        Result_set.to_csv("Inputs_outputs_dataset.csv", index=False)

    def Run_all(self):
        ''' Runs all the methods to get the final data set
            which contains input and output data based on config.yaml file
        '''
        self.get_simulation_files()
        self.Run_LS()
        self.get_results()
        self.get_dataset()