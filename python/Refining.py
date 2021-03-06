import os
import pandas as pd
import numpy as np
import math
from tqdm import tqdm
from rdkit import Chem
from rdkit import DataStructs
from rdkit.Chem import AllChem
from rdkit.Chem import Draw, PandasTools, MolFromSmiles

class convert_format: # You can convert format from dataframe, txt, excel, sdf to dataframe, txt, excel, sdf, png files.
                      # And you can also refine the dataframe.
    # initiation: from your input file, automatically set path, name and dataframe.
    def __init__(self, inputfile, path='D:', name='new'):
        if type(inputfile) == type(pd.DataFrame()): # input path and data when input format is dataframe.
            self.fm = 'dataframe'
            self.path = path
            self.name = name
        else:
            lst = inputfile.split('/') # else list the path, name and format.
            path = '/'.join(lst[:-1])
            name = lst[-1].split('.')[0]
            fm = lst[-1].split('.')[1]
            self.path = path
            self.name = name
            self.fm = fm
        # Make your input to dataframe.
        if type(inputfile) == type(pd.DataFrame()):
            dataframe = inputfile
            dataframe = dataframe.loc[:, ~dataframe.columns.str.contains('^Unnamed')]
            self.dataframe = dataframe
        elif self.fm == 'txt':
            dataframe = pd.read_csv(inputfile, sep='\t')
            self.dataframe = dataframe
        elif self.fm == 'tsv':
            dataframe = pd.read_csv(inputfile, sep='\t')
            self.dataframe = dataframe
        elif self.fm == 'csv':
            dataframe = pd.read_csv(inputfile, sep=',')
            self.dataframe = dataframe
        elif self.fm == 'xlsx':
            dataframe = pd.read_excel(inputfile)
            dataframe = dataframe.loc[:, ~dataframe.columns.str.contains('^Unnamed')]
            self.dataframe = dataframe
        elif (self.fm == 'sdf') or (self.fm == 'sd'):
            dataframe = PandasTools.LoadSDF(inputfile)
            smi_list = []
            for idx, mol in enumerate(list(dataframe['ROMol'])):
                try:
                    smi = Chem.MolToSmiles(mol)
                    smi_list.append(smi)
                except:
                    print(f'Lost Smiles \n index: {idx}, ID: {dataframe["ID"][idx]}')
                    dataframe.drop([idx])
                    continue
            dataframe['Smiles'] = smi_list
            result = pd.DataFrame(dataframe, columns=['ID'] + ['Smiles'] + list(dataframe.columns[:-3]))
            self.dataframe = result
        else:
            print('This format is not available yet.')
            self.dataframe = pd.Dataframe()
        # unify smile codes
        if list(self.dataframe['Smiles']):
            self.dataframe['Smiles'] = self.dataframe['Smiles'].apply(lambda x: Chem.MolToSmiles(Chem.MolFromSmiles(x), isomericSmiles=True))

    # return you a dataframe if you import "convert_format('inputfile')()". Or you can list columns if you want.
    def __call__(self, *args, **kwargs):
        return self.dataframe

    def to_txt(self, sep='\t'):
        dataframe = self.dataframe
        dataframe.to_csv(f'{self.path}/{self.name}.txt', sep=sep, index=False)
        print(f'Your file "{self.name}" is successfully converted from {self.fm} to text file.')

    def to_xlsx(self):
        dataframe = self.dataframe
        dataframe.to_excel(f'{self.path}/{self.name}.xlsx', index=False)
        print(f'Your file "{self.name}" is successfully converted from {self.fm} to excel file.')

    def to_sdf(self):
        dataframe = self.dataframe
        ID = input(f'Your columns are {list(dataframe.columns)}. \n' # show your columns.
                   'Which column do you want to select to ID?:')     # select ID column.
        PandasTools.AddMoleculeColumnToFrame(dataframe, 'Smiles', 'Molecule')
        auto = input('Do you want to set properties Automatically? [Y/N]:')
        # if yes, input all of your propertiees except ID and Smiles.
        if auto.upper() == 'Y':
            columns = [x for x in dataframe.columns if not (x == ID or x == 'Smiles')]
        # Or you can choose your properties.
        else:
            columns = input('Which columns do you want to use as properties?:').split(', ')
        PandasTools.WriteSDF(dataframe, f'{self.path}/{self.name}.sdf', molColName='Molecule',idName=str(ID), properties=columns)
        print(f'Your file "{self.name}" is successfully converted from {self.fm} to sdf file.')

    def to_png(self):
        dataframe = self.dataframe
        ID = input(f'Your columns are {list(dataframe.columns)}. \n'
                   'Which column do you want to select as "ID"? [import column name]:\n'
                   'Or do you want to save only structure img? [import "only structure"]:')
        # make new folder for images.
        try:
            os.mkdir(f"{self.path}/{self.name}_draw")
        except:
            print('Already exist folder')
        # indicate structure name.
        if ID.upper() == 'ONLY STRUCTURE':
            structure_name = None
        else:
            structure_name = list(map(str, list(dataframe[ID])))
        # make splits if you want.
        if len(list(dataframe['Smiles'])) >= 5:
            split = input(f'The file have {len(dataframe)} structures.\n'
                          'How many structures do you want to include in one png file?:')
            lst = np.array_split(dataframe, math.ceil(len(dataframe) / int(split)))
            n=0
            for idx, i in enumerate(lst):
                mols = [MolFromSmiles(mol) for mol in list(i['Smiles'])]
                if structure_name:
                    img = Draw.MolsToGridImage(mols, molsPerRow=4,
                                               subImgSize=(250, 250), legends=structure_name[n:n+len(i)])
                    n+=len(i)
                else:
                    img = Draw.MolsToGridImage(mols, molsPerRow=4,
                                               subImgSize=(250, 250), legends=structure_name)
                img.save(f"{self.path}/{self.name}_draw/{self.name}_{idx}.png")
        else:
            mols = [MolFromSmiles(mol) for mol in list(dataframe['Smiles'])]
            img = Draw.MolsToGridImage(mols, molsPerRow=len(list(dataframe['Smiles'])),
                                       subImgSize=(250, 250), legends=structure_name)
            img.save(f"{self.path}/{self.name}_draw/{self.name}.png")
        print(f'Your file "{self.name}" is successfully converted from {self.fm} to png file.')

class dataframe_calculator:
    def __init__(self, df1):
        self.df1 = df1

    def intersection(self, df2):
        s1 = set(list(self.df1.columns))
        s2 = set(list(df2.columns))
        columns = list(s1 & s2)
        self.df1 = pd.merge(self.df1[columns], df2[columns], how='inner')
        return self.df1

    def sub(self, df2):
        s1 = set(list(self.df1.columns))
        s2 = set(list(df2.columns))
        columns = list(s1 & s2)
        self.df1 = pd.concat([self.df1[columns], df2[columns], df2[columns]]).drop_duplicates(keep=False)
        return self.df1

    def union(self, df2):
        self.df1 = pd.merge(self.df1, df2, how='outer')
        return self.df1

    def add(self, df2):
        s1 = set(list(self.df1.columns))
        s2 = set(list(df2.columns))
        columns = list(s1 & s2)
        self.df1 = pd.merge(self.df1[columns], df2[columns], how='outer')
        return self.df1

    def abstract_rows(self, column, relation, value):
        dataframe = self.df1
        lst = []
        values = []
        try:
            values = values + value
        except:
            values.append(value)
        for v in values:
            new = dataframe[eval('dataframe[column]' + " " + relation + " " + 'v')]
            lst.append(new)
        for df in lst:
            df.reset_index(drop=True, inplace=True)
        return lst

    def abstract_columns(self, columns):
        dataframe = self.df1
        if type(columns) == str:
            return list(dataframe[columns])
        else:
            lst = []
            for idx, column in enumerate(columns):
                lst.append(list(dataframe[column]))
            return lst

if __name__ == "__main__":
    # # Ex1) excel to sdf
    # convert_format('D:/New_Target/ULK1/ULK1_purecompounds.xlsx').to_sdf()
    #
    # # Ex2) sdf to excel
    # convert_format('D:/New_Target/ULK1/ULK1_purecompounds.sdf').to_xlsx()

    # Ex3) excel to png
    data = convert_format('D:/New_Target/ULK1/ULK1_Patent_data.xlsx')()
    print(data)

    # # Ex4) sdf to dataframe
    # dataframe = convert_format('D:/New_Target/ULK1/ULK1_purecompounds.sdf')()
    #
    # # Ex5) dataframe to png
    # convert_format(dataframe).to_png()
    #
    # # Ex6) Abstract columns from data
    # ID, Smiles, PIC50_Class = convert_format('D:/New_Target/ULK1/ULK1_purecompounds.xlsx')(['ID', 'Smiles', 'PIC50_Class'])
    #
    # # Ex7) Abstract rows satisfying the condition from data
    # active = dataframe_calculator(dataframe).abstract_rows('PIC50_Class', '==', ['Range_A', 'Range_B', 'Range_C', 'Range_D'])
    # print(f'active:\n{active}')
    # inactive = dataframe_calculator(dataframe).abstract_rows('PIC50_Class', '==', 'Range_F')
    # print(f'inactive:\n{inactive}')