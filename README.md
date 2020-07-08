# Tactical tool for CUH Covid configuration planning

## 0. Getting setup
This project uses an Anaconda environment that contains all the required Python package dependencies. 

### 0.1. Install Anaconda
First, you'll need to install Anaconda. Follow [the instructions their website](https://docs.anaconda.com/anaconda/install/).

### 0.2. Create a conda environment for the project
To get started, just run the included `setup.sh` bash script:
```
bash setup.sh
```

This creates a conda environment called `cuhvid` and installs all the dependencies. It then adds the project folder to the conda environment to allow the local package (also called `cuhvid`) to be used.

## 1. Serve the interactive dashboard
You can serve an interactive version of the notebook as a dashboard by activating the `cuhvid` conda environment and serving the Jupyter notebook using Voila by running the included `conda_env.sh` and `serve.sh` bash scripts:
```bash
bash conda_env.sh
bash serve.sh
```
