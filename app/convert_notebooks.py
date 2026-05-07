#!/usr/bin/env python
# coding: utf-8

# In[3]:


# convert_notebooks_structure.py
import os
import subprocess

NOTEBOOK_DIR = r"C:\Users\Jason.Ouyang\Downloads\OuYang\Python\20250204_PM21_GreenZone\app"

def convert_notebooks(base_dir):
    for root, dirs, files in os.walk(base_dir):
        # 忽略 .ipynb_checkpoints 資料夾
        dirs[:] = [d for d in dirs if d != ".ipynb_checkpoints"]

        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                print(f"正在轉換: {notebook_path}")
                
                subprocess.run([
                    "jupyter", "nbconvert",
                    "--to", "script",
                    notebook_path
                ])

    print("全部轉換完成！")

if __name__ == "__main__":
    convert_notebooks(NOTEBOOK_DIR)


# In[6]:


from nbconvert import PythonExporter
import nbformat
import os

import time

start_time = 

NOTEBOOK_DIR = r"C:\Users\Jason.Ouyang\Downloads\OuYang\Python\20250204_PM21_GreenZone\app"

def convert_notebooks_api(base_dir):
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d != ".ipynb_checkpoints"]
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                print(f"正在轉換: {notebook_path}")
                
                # 讀 notebook
                nb_node = nbformat.read(notebook_path, as_version=4)
                exporter = PythonExporter()
                source, _ = exporter.from_notebook_node(nb_node)
                
                # 寫入 .py
                py_path = notebook_path.replace(".ipynb", ".py")
                with open(py_path, "w", encoding="utf-8") as f:
                    f.write(source)
    print("全部轉換完成！")
    
if __name__ == "__main__":
    convert_notebooks(NOTEBOOK_DIR)    


# In[ ]:




