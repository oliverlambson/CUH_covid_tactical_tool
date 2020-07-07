# Tactical tool for CUH Covid configuration planning

## Getting setup
This project uses an Anaconda environment that contains all the required Python package dependencies. 

### Install Anaconda
First, you'll need to install Anaconda. Follow [the instructions their website](https://docs.anaconda.com/anaconda/install/).

### Create a conda environment for the project
```bash
conda create --name cuhvid --file requirements.txt
conda develop .
```

Alternatively, just run:
```
bash setup.sh
```

This creates a conda environment called ```cuhvid``` and installs all the dependencies. It then adds the project folder to the conda environment to allow the local package (also called cuhvid) to be used.

## Serve the interactive dashboard
You can serve an interactive version of the notebook as a dashboard using:
```bash
bash serve.sh
```
