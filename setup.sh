# create the conda environment and install dependencies
conda create --name cuhvid --file requirements.txt
# add local modules to environment
conda develop .